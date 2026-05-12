# Cognito → Keycloak Migration

> Based on code analysis of this repo (April 2026).  
> "No code change needed" means the existing abstraction already handles it — only config/data changes.

---

## How auth currently works (what we're replacing)

1. **JWT validation (all services)** — `security-starter` → `TenantAuthenticationManagerResolver` calls `JwtDecoders.fromIssuerLocation(issuerUrl)` using the issuer URL stored per-tenant in the DB. Completely provider-agnostic.
2. **User management (user-management-service)** — `CognitoIdentityAdaptorImpl` calls the Cognito SDK directly to create users, set passwords, update attributes, initiate auth, etc.
3. **Machine-to-machine token fetching (rule-engine-service, patient-data-service)** — Spring OAuth2 client configured to hit Cognito's `token-uri` for client-credentials flows.
4. **Per-tenant identity config (tenant-configuration-service)** — `identity_provider_settings` table stores `domain`, `clientId`, `issuerUrl`, `patientIssuerUrl`, `redirectUrl`, `responseType` per tenant.

---

## Part 1 — Keycloak Setup (what DevOps/Keycloak admin must do)

### Realms

- Create one **realm per tenant** (or a shared realm with separate clients — decide on strategy).
  - Recommended: one realm per tenant to keep data isolated (matches current multi-tenant model).
- For each realm create **two clients** mirroring the two Cognito user pools:
  - `staff-client` — for coaches/admins (maps to current `issuerUrl`)
  - `patient-client` — for patients (maps to current `patientIssuerUrl`)

### Clients — Staff & Patient (Authorization Code + PKCE, for frontend)

| Setting               | Value                                                             |
| --------------------- | ----------------------------------------------------------------- |
| Client authentication | OFF (public client, PKCE)                                         |
| Valid redirect URIs   | Same values currently in `identity_provider_settings.redirectUrl` |
| Web origins           | Frontend origin (CORS)                                            |
| Standard flow         | Enabled                                                           |
| Direct access grants  | Disabled (unless internal tooling needs it)                       |

### Clients — Machine-to-Machine (Client Credentials)

Two additional confidential clients (or service accounts on existing clients):

| Service                | Purpose                      | Current Cognito config location                                  |
| ---------------------- | ---------------------------- | ---------------------------------------------------------------- |
| `rule-engine-service`  | calls dynamic-survey-service | `application.yml` → `cognito-external-credentials` block         |
| `patient-data-service` | calls HAPI FHIR server       | `application.yml` → `hapi-fhir-cognito-client-credentials` block |

- Enable **Service accounts** on each client.
- Create the equivalent **client scopes** to replace Cognito custom resource server scopes:
  - `default-m2m-resource-server-ua2gcq/read` → Keycloak client scope (e.g. `dynamic-survey:read`)
  - `dynamic-survey-resource-server/read` → same
  - `hapi_fhir_client/resource.read`, `hapi_fhir_client/resource.operation` → equivalent Keycloak scopes

### User schema / attributes

Cognito attributes used by the code (from `CognitoIdentityAdaptorImpl`):

- `email`
- `phone_number` + `phone_number_verified`
- `email_verified`
- Custom attribute currently mapped via `AdminCreateUser` invite flow

Keycloak equivalents:

- `email`, `email_verified` — built-in, no action needed.
- `phone_number`, `phone_number_verified` — add as **user attributes** in realm settings.
- Invite/welcome email — configure **email action: VERIFY_EMAIL** and use Keycloak's invitation / required-action flow instead of Cognito's `MessageActionType.SUPPRESS` + manual email.

### Password policy

`IdentityAdaptor.getPasswordPolicy()` fetches Cognito's `PasswordPolicyType`. In Keycloak, set the equivalent **Password Policy** on the realm and remove the runtime fetch (see BE changes below).

### Token claims (important)

The `jwtAuthenticationConverter` in `security-starter` uses `JwtGrantedAuthoritiesConverter` which by default reads the `scope` claim. Roles/groups are loaded from the DB via `PermissionProvider`, NOT from the JWT — so Keycloak role claims don't need to map 1:1 with Cognito groups. **No claim mapping is required** as long as the `sub` claim is populated (it is, by default in Keycloak).

Verify: Keycloak `sub` = user UUID. If Keycloak uses its own UUIDs (it does by default), user IDs will differ from Cognito UUIDs — **user data migration must map old Cognito `sub` → Keycloak user ID** so `PermissionProvider.loadAuthorities(userId, tenantId)` still resolves correctly.

---

## Part 2 — Backend Service Changes

### `user-management-service` — **HIGH EFFORT, most impactful**

This is the only service with deep Cognito SDK coupling. `CognitoIdentityAdaptorImpl` implements `IdentityAdaptor` — the interface is already abstracted, so the plan is:

1. **Add a `KeycloakIdentityAdaptorImpl`** that implements `IdentityAdaptor` using the [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/) (via `keycloak-admin-client` library or plain REST calls).
2. **Wire conditionally** — keep `CognitoIdentityAdaptorImpl` behind a feature flag / Spring profile so you can run both during transition.
3. **Remove `AwsConfig.java`** (`CognitoIdentityProviderClient` bean) once migration is complete.

Method mapping:

| `IdentityAdaptor` method                      | Keycloak Admin API equivalent                                                                                          |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `createUser(Invitation)`                      | `POST /admin/realms/{realm}/users`                                                                                     |
| `getPasswordPolicy()`                         | `GET /admin/realms/{realm}` → `passwordPolicy` field                                                                   |
| `saveUserPhoneNumber(email, phone, verified)` | `PUT /admin/realms/{realm}/users/{id}` with `attributes`                                                               |
| `updateUserEmail(old, new)`                   | `PUT /admin/realms/{realm}/users/{id}`                                                                                 |
| `verifyUserEmailAndPhoneNumber(...)`          | `PUT /admin/realms/{realm}/users/{id}` + set `emailVerified`                                                           |
| `setUserPassword(email, password)`            | `PUT /admin/realms/{realm}/users/{id}/reset-password`                                                                  |
| `getAccessToken(email, password)`             | `POST /realms/{realm}/protocol/openid-connect/token` (Resource Owner Password — or eliminate this, it's a legacy flow) |
| `existByPhoneNumber(phone, email)`            | `GET /admin/realms/{realm}/users?q=phone_number:{phone}`                                                               |
| `changePassword(accessToken, current, new)`   | Keycloak Account REST API or Admin API `reset-password`                                                                |

Dependencies to add to `user-management-service/build.gradle`:

```groovy
implementation 'org.keycloak:keycloak-admin-client:24.x.x'
```

### `rule-engine-service` — **LOW EFFORT**

Replace the `cognito-external-credentials` OAuth2 client config in `application.yml`:

```yaml
# BEFORE
cognito-external-credentials:
  client-id: '...'
  client-secret: '...'
  scope: 'default-m2m-resource-server-ua2gcq/read, dynamic-survey-resource-server/read'
  token-uri: 'https://us-east-1o7fq6yyu0.auth.us-east-1.amazoncognito.com/oauth2/token'

spring.security.oauth2.client:
  registration.cognito-external-credentials:
    client-id: '${cognito-external-credentials.client-id}'
    client-secret: '${cognito-external-credentials.client-secret}'
    authorization-grant-type: client_credentials
    scope: '${cognito-external-credentials.scope}'
  provider.cognito-external-credentials:
    token-uri: '${cognito-external-credentials.token-uri}'

spring.cloud.openfeign.oauth2:
  externalAppRegistrationId: 'cognito-external-credentials'

# AFTER
keycloak-m2m:
  client-id: '${KEYCLOAK_M2M_CLIENT_ID}'
  client-secret: '${KEYCLOAK_M2M_CLIENT_SECRET}'
  scope: 'dynamic-survey:read'
  token-uri: 'https://{keycloak-host}/realms/{realm}/protocol/openid-connect/token'

spring.security.oauth2.client:
  registration.keycloak-m2m:
    client-id: '${keycloak-m2m.client-id}'
    client-secret: '${keycloak-m2m.client-secret}'
    authorization-grant-type: client_credentials
    scope: '${keycloak-m2m.scope}'
  provider.keycloak-m2m:
    token-uri: '${keycloak-m2m.token-uri}'

spring.cloud.openfeign.oauth2:
  externalAppRegistrationId: 'keycloak-m2m'
```

No Java code changes needed — only `application.yml` + env vars.

### `patient-data-service` — **LOW EFFORT**

Same pattern as `rule-engine-service`. Replace `hapi-fhir-cognito-client-credentials` registration:

```yaml
# BEFORE
aws:
  hapi-fhir-cognito:
    domain: "https://dev-dhc-sap-hapi-fhir.auth.us-east-1.amazoncognito.com"
    user-pool.client:
      id: "..."
      secret: "..."
      scope: "hapi_fhir_client/resource.read, hapi_fhir_client/resource.operation"

spring.security.oauth2.client:
  registration.hapi-fhir-cognito-client-credentials:
    ...
    token-uri: '${aws.hapi-fhir-cognito.domain}/oauth2/token'

hapi.fhir:
  client-registration-id: 'hapi-fhir-cognito-client-credentials'

# AFTER
keycloak-hapi-fhir:
  token-uri: 'https://{keycloak-host}/realms/{realm}/protocol/openid-connect/token'
  client-id: '${KEYCLOAK_HAPI_FHIR_CLIENT_ID}'
  client-secret: '${KEYCLOAK_HAPI_FHIR_CLIENT_SECRET}'
  scope: 'hapi-fhir:read hapi-fhir:operation'

spring.security.oauth2.client:
  registration.keycloak-hapi-fhir:
    client-id: '${keycloak-hapi-fhir.client-id}'
    client-secret: '${keycloak-hapi-fhir.client-secret}'
    authorization-grant-type: client_credentials
    scope: '${keycloak-hapi-fhir.scope}'
  provider.keycloak-hapi-fhir:
    token-uri: '${keycloak-hapi-fhir.token-uri}'

hapi.fhir:
  client-registration-id: 'keycloak-hapi-fhir'
```

> Note: HAPI FHIR server also needs to accept Keycloak tokens — its own Cognito user pool and resource server must be migrated or a Keycloak → HAPI bridge configured.

### `tenant-configuration-service` — **LOW EFFORT (data migration)**

No code changes. Update the `identity_provider_settings` table rows per tenant:

| Column               | Cognito value                                                 | Keycloak value                                                                |
| -------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `domain`             | `https://{pool}.auth.us-east-1.amazoncognito.com`             | `https://{keycloak-host}/realms/{realm}`                                      |
| `issuer_url`         | `https://cognito-idp.us-east-1.amazonaws.com/{userPoolId}`    | `https://{keycloak-host}/realms/{realm}`                                      |
| `patient_issuer_url` | `https://cognito-idp.us-east-1.amazonaws.com/{patientPoolId}` | `https://{keycloak-host}/realms/{patient-realm}`                              |
| `client_id`          | Cognito app client ID                                         | Keycloak public client ID                                                     |
| `redirect_url`       | existing value                                                | same value (frontend callback URL — unchanged if frontend URL doesn't change) |
| `response_type`      | `code`                                                        | `code` (unchanged)                                                            |

SQL migration script needed (one row per tenant per environment).

### `security-starter` — **NO CODE CHANGES NEEDED**

`TenantAuthenticationManagerResolver` calls `JwtDecoders.fromIssuerLocation(issuerUrl)` — this is pure OIDC discovery, works with any compliant provider including Keycloak. No changes.

---

## Part 3 — User Data Migration

| Item                       | Action                                                                                                                                                                                                   |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Export users from Cognito  | `aws cognito-idp list-users` per user pool                                                                                                                                                               |
| Import users into Keycloak | Keycloak Admin API bulk import or `keycloak-import` JSON format                                                                                                                                          |
| Map `sub` (user IDs)       | Cognito `sub` (UUID) ≠ Keycloak user ID. Must update the `user_id` / foreign keys in the application DBs that reference Cognito `sub`, OR configure Keycloak to use the same UUIDs (possible via import) |
| Passwords                  | Cannot be migrated (Cognito doesn't expose hashed passwords). Options: (a) force-reset on first login, (b) use Keycloak's User Storage SPI to authenticate against Cognito during transition period      |
| MFA                        | Reconfigure per-user MFA in Keycloak (TOTP or SMS via custom SPI)                                                                                                                                        |

---

## Migration Order

```
1. Keycloak realm + client setup
2. user-management-service: KeycloakIdentityAdaptorImpl (behind feature flag)
3. Data migration: export Cognito users → import to Keycloak (preserve UUIDs)
4. DB migration: update identity_provider_settings per tenant
5. rule-engine-service + patient-data-service: swap token-uri configs (env var change + redeploy)
6. Smoke test JWT validation end-to-end
7. Remove CognitoIdentityAdaptorImpl + AwsConfig + AWS Cognito SDK dependency
8. Remove aws.cognito / cognito-external-credentials config keys
```

**On OAuth2 vs OIDC:**

You are using both, in different places — it's not one or the other:

- **OAuth2 Authorization Code flow** — the frontend login redirect. Configured via `domain`, `clientId`, `redirectUrl` in `identity_provider_settings`. This is what your frontend/mobile app uses to get tokens from Cognito.
- **OAuth2 Client Credentials** — `rule-engine-service` and `patient-data-service` fetching M2M tokens via `token-uri`. Pure OAuth2, no user involved.
- **OIDC (whether you knew it or not)** — `JwtDecoders.fromIssuerLocation(issuer)` in `security-starter` **hits the OIDC discovery endpoint** (`/.well-known/openid-configuration`) to auto-discover the JWKS URI and validate JWT signatures. Spring calls this under the hood. Cognito supports OIDC discovery, and so does Keycloak — so this still works fine.

So the doc is correct as-is. The "OIDC" mention in the doc refers specifically to that discovery mechanism, not to an authentication flow you consciously chose.

---

**On who does what:**

It genuinely needs **both roles** — there's a hard split:

| Work                                                                   | Role                                                                                                                                                    |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Keycloak realm/client setup, user import, password policy, MFA, scopes | **DevOps / Keycloak admin**                                                                                                                             |
| `user-management-service`: write `KeycloakIdentityAdaptorImpl`         | **Java dev** (biggest chunk)                                                                                                                            |
| `rule-engine-service` + `patient-data-service`: swap YAML configs      | Either — it's just config, but needs coordination with DevOps who creates the Keycloak clients and provides the `client-id`/`client-secret`/`token-uri` |
| DB migration (`identity_provider_settings`)                            | Either, but needs the Keycloak realm URLs from DevOps first                                                                                             |
