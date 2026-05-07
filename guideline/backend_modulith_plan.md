# backend-modulith — Architecture & Build Plan

**Date:** 07 May 2026
**Repository:** https://github.com/cgarbacea/backend-modulith
**Local path:** /Users/cgarbacea/Projects/YOUPAGE/backend-modulith
**Source of truth for reused logic:** /Users/cgarbacea/Projects/insighthealth/health-coach-portal-backend/microservices/

---

## Context

The old system is a Gradle/Java microservices architecture (user-management-service,
tenant-configuration-service, patient-management-service, etc.) backed by AWS Cognito
for auth. We are consolidating the relevant domain logic into a single Spring Modulith
monolith with enforced module boundaries, replacing Cognito with Keycloak, and connecting
it to the existing platform-monorepo frontend.

We are **not** rebuilding all 20 microservices. We are extracting the core domains that
the admin-portal frontend actually needs and implementing them correctly.

---

## Technology Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Java 25 (Temurin) | Latest, installed, non-LTS but production-ready |
| Framework | Spring Boot 3.5.0 | Current GA, supports Java 25 |
| Module boundaries | Spring Modulith 1.4.11 | Enforced at test time, generates module graph |
| DDD vocabulary | jMolecules 2023.2.3 | Annotations: @AggregateRoot, @DomainEvent, @BoundedContext |
| Architecture rules | ArchUnit 1.3.0 | Breaks build on violations |
| Auth (local dev) | Keycloak 26 (Docker) | Replaces Cognito; OAuth2/OIDC |
| Auth (Spring) | spring-boot-starter-oauth2-resource-server | Validates Keycloak JWTs |
| Database | PostgreSQL 15 (local Homebrew, port 5432) | Already running, no Docker needed |
| Migrations | Liquibase | Reuse existing SQL from old microservices (Liquibase format) |
| Build | Maven (via mvnw wrapper) | Already scaffolded |
| Inter-module events | Spring ApplicationEventPublisher (sync) → Spring Modulith EventPublication (async) | Hexagonal: modules don't import each other |

---

## Hexagonal Architecture — The Rule

```
┌─────────────────────────────────────────────────────────────┐
│  Module: users                                              │
│                                                             │
│  domain/         ← pure Java, no Spring, no JPA            │
│    User.java     ← @AggregateRoot (jMolecule)              │
│    UserCreatedEvent.java ← @DomainEvent                    │
│    UserRepository.java   ← interface (port)                │
│                                                             │
│  application/    ← use cases, orchestrates domain          │
│    UserService.java  ← @ApplicationService                 │
│    CreateUserCommand.java                                   │
│                                                             │
│  infrastructure/ ← JPA adapters, Keycloak adapter          │
│    JpaUserRepository.java  ← implements UserRepository     │
│    KeycloakUserAdapter.java ← calls Keycloak Admin API     │
│                                                             │
│  api/            ← REST controllers, DTOs                  │
│    UserController.java  ← @RestController                  │
│    UserResponse.java    ← record (no domain leakage)       │
└─────────────────────────────────────────────────────────────┘
         │ publishes UserCreatedEvent
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Module: workspaces                                         │
│  @ApplicationModuleListener UserCreatedEvent → create       │
│  default workspace for new user                             │
│  NEVER imports users.domain.User directly                   │
└─────────────────────────────────────────────────────────────┘
```

**The rule enforced by ArchUnit + Spring Modulith:**
- `workspaces` may NOT import anything from `users.domain`, `users.application`, or `users.infrastructure`
- `workspaces` MAY import `users.api` package (public API surface only)
- All cross-module communication goes via domain events

---

## Modules to Build (Scope)

### Module 1: `users`
**Reuses from:** `user-management-service`

| What | Source |
|---|---|
| User entity + phone_numbers table | `migrations/release-1/schema/001–007_*.sql` |
| Privacy policy tables | `003_create_user_privacy_policy_tables_ddl.sql` |
| UserProfileDto shape | `dto/UserProfileDto.java`, `LightUserProfileDto.java` |
| Role/permission model | `dto/UserPermissionDto.java` |
| Theme preference | New — connects to dark mode toggle in FE |

**Keycloak integration:**
- On user creation: call Keycloak Admin REST API to create the user in the realm
- JWT validation: Spring resource server validates tokens issued by Keycloak
- Replace `CognitoIdentityAdaptorImpl` with `KeycloakIdentityAdapter`

**Events published:**
- `UserCreatedEvent` → consumed by `workspaces` (create default workspace)
- `UserDeactivatedEvent` → consumed by `notifications`
- `ThemePreferenceChangedEvent` → consumed by nobody (stored only)

**REST API (consumed by admin-portal):**
```
GET  /api/v1/users/me              → current user profile
PUT  /api/v1/users/me/profile      → update display name, avatar
PUT  /api/v1/users/me/preferences  → theme preference (dark/light/system)
GET  /api/v1/users/{id}            → admin: get any user
GET  /api/v1/users                 → admin: list users (paginated)
POST /api/v1/users/invite          → invite user by email via Keycloak
```

---

### Module 2: `workspaces`
**Reuses from:** `tenant-configuration-service` (partial)

Simplified scope — we don't rebuild full tenant config. Just:
- Workspace = a named container users belong to (maps to "tenant" concept)
- One user may belong to multiple workspaces
- Default workspace auto-created when a user is created (via UserCreatedEvent)

**Events published:**
- `UserAddedToWorkspaceEvent`
- `WorkspaceCreatedEvent`

**REST API:**
```
GET  /api/v1/workspaces            → list workspaces for current user
POST /api/v1/workspaces            → create workspace
GET  /api/v1/workspaces/{id}/members
POST /api/v1/workspaces/{id}/members → add member
```

---

### Module 3: `notifications`
**Reuses from:** `user-notification-service` (patterns only, no code copy)

Lightweight — just persists notifications triggered by domain events.
No email sending in scope for local dev.

**Listens to:**
- `UserCreatedEvent` → persist welcome notification
- `UserDeactivatedEvent` → persist deactivation notification
- `UserAddedToWorkspaceEvent` → persist workspace invitation notification

**REST API:**
```
GET  /api/v1/notifications         → list notifications for current user
PUT  /api/v1/notifications/{id}/read
```

---

## Keycloak — Local Docker Setup

Single Docker container, **not Docker Compose** (keeps it simple for solo dev).

```bash
# Start Keycloak (run once, persists data in named volume)
docker run -d \
  --name keycloak-local \
  -p 8180:8080 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  -e KC_DB=dev-file \
  quay.io/keycloak/keycloak:26.2 \
  start-dev
```

Admin console: http://localhost:8180  
Admin credentials: admin / admin

**Realm setup (one-time, manual via admin console):**
1. Create realm: `youpage-dev`
2. Create client: `admin-portal` (public, Authorization Code + PKCE)
   - Valid redirect URIs: `http://localhost:3000/*`
   - Web origins: `http://localhost:3000`
3. Create test user: `dev@youpage.com` / `password`

**Spring resource server config (application-local.yml):**
```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: http://localhost:8180/realms/youpage-dev
```

---

## Database — Local PostgreSQL (no Docker)

PostgreSQL 15 is already running on localhost:5432 (Homebrew).

```sql
-- Run once in psql
CREATE DATABASE youpage_dev;
CREATE USER youpage_app WITH PASSWORD 'youpage_dev';
GRANT ALL PRIVILEGES ON DATABASE youpage_dev TO youpage_app;
```

**application-local.yml:**
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/youpage_dev
    username: youpage_app
    password: youpage_dev
  liquibase:
    change-log: classpath:db/changelog/db.changelog-master.xml
```

**Migration strategy:**
- Copy relevant SQL from old microservices into Liquibase changeset format
- Start with `user-management-service` migrations (007 SQL files from release-1/schema)
- Adapt: remove Cognito-specific columns, add `keycloak_id` column instead

---

## ArchUnit Rules (enforced in tests)

```java
// src/test/java/com/youpage/backend/ArchitectureTest.java

@AnalyzeClasses(packages = "com.youpage.backend")
class ArchitectureTest {

    // 1. No cross-module domain imports
    @ArchTest
    static final ArchRule noDirectModuleImports = noClasses()
        .that().resideInAPackage("..workspaces..")
        .should().accessClassesThat()
        .resideInAPackage("..users.domain..")
        .orShould().resideInAPackage("..users.application..");

    // 2. Controllers must not call repositories directly
    @ArchTest
    static final ArchRule controllersUseServices = noClasses()
        .that().areAnnotatedWith(RestController.class)
        .should().accessClassesThat()
        .resideInAPackage("..infrastructure..");

    // 3. Domain layer has no Spring dependencies
    @ArchTest
    static final ArchRule pureDomaín = noClasses()
        .that().resideInAPackage("..domain..")
        .should().dependOnClassesThat()
        .resideInAPackage("org.springframework..");
}
```

---

## Frontend (platform-monorepo) Changes for Keycloak

See `/guideline/keycloak/keycloak_FE_migration.md` for full detail.

**Summary of changes to admin-portal:**
- Replace current auth provider with `@keycloak/keycloak-js` + React adapter
- `KeycloakProvider` wraps the app — handles token refresh automatically
- All API calls include `Authorization: Bearer <access_token>` from Keycloak
- Login redirects to Keycloak login page instead of custom login form

---

## Build Order

| Step | Task | Dependency |
|---|---|---|
| 1 | Start Keycloak Docker + create realm/client | None |
| 2 | Create local PostgreSQL DB | None |
| 3 | `users` module — domain model + Liquibase migrations | Steps 1, 2 |
| 4 | `users` module — Keycloak adapter + JWT resource server | Step 1 |
| 5 | `users` module — REST API + ArchUnit tests | Step 3, 4 |
| 6 | `workspaces` module — domain + event listener | Step 5 |
| 7 | `notifications` module | Step 5, 6 |
| 8 | Spring Modulith integration test (module graph verification) | Step 7 |
| 9 | FE admin-portal — swap auth to Keycloak | Step 1, 5 |
| 10 | Wire SDLC pipeline BE executor to know these rules | All |

---

## What We Are NOT Building

- Email sending (notifications module persists only)
- Patient management (separate domain, not needed for admin-portal)
- Care plans, care teams, video calling
- Multi-tenancy (single realm for now, can add later)
- Full permission/RBAC system (basic roles only: ADMIN, MEMBER)

This keeps the scope honest and the service deliverable in Phase 4 of the career plan.
