# Executor Restructure Plan — Two-Tier Architecture

**Date:** 11 May 2026  
**Goal:** Reduce executor prompt size from ~2,356 lines to ~400 lines total, moving detailed patterns into the RAG knowledge base (`docs/`) while preserving all content quality.

---

## Why

The `docs/` folder feeds `build_knowledge_base.py` → ChromaDB → `search_company_knowledge_base` tool. The executor already calls this tool as step 1. Loading the full executor into every call wastes tokens and was a workaround for an underpopulated knowledge base.

**Target after restructure:**

| Executor                | Current         | Target         | Savings  |
| ----------------------- | --------------- | -------------- | -------- |
| `fe_executor.md`        | 454 lines       | ~100 lines     | ~78%     |
| `be_executor.md`        | 799 lines       | ~120 lines     | ~85%     |
| `be_module_executor.md` | 624 lines       | ~100 lines     | ~84%     |
| `infra_executor.md`     | 479 lines       | ~80 lines      | ~83%     |
| **Total**               | **2,356 lines** | **~400 lines** | **~83%** |

---

## What Stays in the Executor Prompt (always in context)

Every executor keeps only what must be present before any tool is called:

1. **Role identity + specialisation** (2 lines)
2. **When-to-use decision table** (already added — 10–15 lines)
3. **3-step exploration gate** (10 lines — non-negotiable, must run before KB)
4. **Clean code principles — bullet points only, no code examples** (25–35 lines)
5. **Strict scope rules** (8–10 lines)

Total per executor: ~60–80 lines.

---

## What Moves to `docs/` (retrieved on demand via RAG)

Each section with code examples becomes a separate `docs/` file with a descriptive name. The agent will retrieve these when it searches for the relevant pattern.

### `docs/be/` — Backend Spring patterns

| New `docs/` file                   | Content moved from executor                               | Search terms that retrieve it                           |
| ---------------------------------- | --------------------------------------------------------- | ------------------------------------------------------- |
| `be_spring_hexagonal_layout.md`    | Module layout diagram + layer rules                       | "module layout", "hexagonal", "package structure"       |
| `be_spring_aggregate_root.md`      | Aggregate root pattern with full Java code                | "aggregate", "domain entity", "registerEvent"           |
| `be_spring_domain_event.md`        | Domain event pattern + @NamedInterface                    | "domain event", "cross-module", "NamedInterface"        |
| `be_spring_repository_port.md`     | Repository port + JPA adapter pattern                     | "repository", "port", "JPA adapter"                     |
| `be_spring_application_service.md` | Application service pattern + @Transactional rules        | "service", "use case", "transactional"                  |
| `be_spring_event_listener.md`      | @ApplicationModuleListener + REQUIRES_NEW                 | "event listener", "ApplicationModuleListener", "outbox" |
| `be_spring_rest_controller.md`     | Controller pattern + ProblemDetail + exception handlers   | "controller", "endpoint", "REST", "ProblemDetail"       |
| `be_spring_response_dto.md`        | Response record pattern + from() factory                  | "response", "DTO", "record", "mapping"                  |
| `be_spring_liquibase.md`           | Liquibase changeset + master changelog wiring             | "migration", "Liquibase", "changeset"                   |
| `be_spring_jpa_n_plus_one.md`      | N+1 patterns: JOIN FETCH, @EntityGraph, FetchType         | "N+1", "lazy loading", "JOIN FETCH", "EntityGraph"      |
| `be_spring_pagination.md`          | Offset vs cursor pagination + @PageableDefault            | "pagination", "cursor", "offset", "Pageable"            |
| `be_spring_structured_logging.md`  | MDC, correlation IDs, JSON logging format                 | "logging", "MDC", "structured logs", "correlation"      |
| `be_spring_api_versioning.md`      | Versioning strategy, breaking changes, Deprecation header | "versioning", "API version", "deprecation", "Sunset"    |
| `be_spring_messaging.md`           | Kafka consumer + outbox pattern + idempotency             | "Kafka", "messaging", "consumer", "outbox", "broker"    |
| `be_spring_exception_handling.md`  | Global vs local @ExceptionHandler decision                | "exception", "error handling", "RestControllerAdvice"   |
| `be_spring_archunit_rules.md`      | ArchUnit 5 rules + self-check instruction                 | "ArchUnit", "architecture rules", "boundary"            |

### `docs/fe/` — Frontend React/TS patterns

| New `docs/` file                 | Content moved from executor                              | Search terms that retrieve it                        |
| -------------------------------- | -------------------------------------------------------- | ---------------------------------------------------- |
| `fe_feature_module_structure.md` | Feature folder layout + barrel export pattern            | "feature", "module structure", "folder", "barrel"    |
| `fe_service_class.md`            | Service class pattern + KyHttpClient                     | "service", "HTTP", "API client", "KyHttpClient"      |
| `fe_query_key_factory.md`        | Query key factory pattern                                | "query key", "React Query", "TanStack"               |
| `fe_hook_pattern.md`             | useQuery/useMutation hook pattern + error state          | "hook", "useQuery", "useMutation", "error state"     |
| `fe_component_pattern.md`        | Component pattern + error/loading states + styling rules | "component", "isLoading", "isError", "design system" |
| `fe_zod_schema.md`               | Zod schema patterns (factory for i18n, plain for API)    | "Zod", "schema", "validation", "form"                |
| `fe_i18n_rules.md`               | Lingui macro usage + supported locales                   | "i18n", "Lingui", "Trans", "translation"             |
| `fe_state_management.md`         | Server vs client state + stable Zustand selectors        | "state", "Zustand", "React Query", "store"           |
| `fe_page_route_pattern.md`       | Page shell + i18n route segment pattern                  | "page", "route", "Next.js", "App Router"             |
| `fe_accessibility.md`            | Semantic HTML, ARIA, keyboard nav, colour contrast       | "accessibility", "ARIA", "a11y", "keyboard"          |

### `docs/be_module/` — Java module design patterns

| New `docs/` file                   | Content moved from executor                            | Search terms that retrieve it                             |
| ---------------------------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| `be_module_project_layout.md`      | Multi-module layout + core/impl/pipeline separation    | "multi-module", "Gradle", "project structure"             |
| `be_module_version_catalog.md`     | Version catalog .toml + bundles pattern                | "version catalog", "libs.versions.toml", "bundles"        |
| `be_module_interface_first.md`     | Interface-first design + Try<T> + AutoCloseable        | "interface", "core module", "Try", "Vavr"                 |
| `be_module_domain_types.md`        | @Builder record patterns + Instant timestamps          | "record", "Builder", "toBuilder", "domain type"           |
| `be_module_implementation.md`      | Implementation class + ConcurrentHashMap + Try.flatMap | "implementation", "executor", "ConcurrentHashMap"         |
| `be_module_checkstyle.md`          | Checkstyle XML rules + what they enforce               | "Checkstyle", "style", "EmptyCatchBlock"                  |
| `be_module_jacoco.md`              | JaCoCo 80% coverage gate + exclusions                  | "JaCoCo", "coverage", "test coverage"                     |
| `be_module_testing.md`             | Unit (H2/in-memory) vs integration (TestContainers)    | "test", "unit test", "integration test", "TestContainers" |
| `be_module_helm_externalsecret.md` | ExternalSecret v1beta1 + deployment template           | "Helm", "ExternalSecret", "K8s", "secrets"                |
| `be_module_github_actions.md`      | Path-based triggers + composite actions + skip CI      | "GitHub Actions", "CI", "pipeline", "workflow"            |
| `be_module_sonarqube.md`           | SonarQube integration + quality gates                  | "SonarQube", "quality", "sonar"                           |

### `docs/infra/` — Infrastructure patterns

| New `docs/` file               | Content moved from executor                                  | Search terms that retrieve it                       |
| ------------------------------ | ------------------------------------------------------------ | --------------------------------------------------- |
| `infra_terraform_providers.md` | Provider pinning + S3 remote backend                         | "Terraform", "provider", "backend", "state"         |
| `infra_terraform_naming.md`    | Naming convention + tags/labels pattern                      | "naming", "tags", "resource names"                  |
| `infra_terraform_variables.md` | Variables vs locals vs tfvars decision                       | "variables", "locals", "tfvars", "secrets"          |
| `infra_network_vpc.md`         | VPC pattern: private subnets, NAT, AZs                       | "VPC", "network", "subnet", "NAT"                   |
| `infra_firewall_sg.md`         | Security group pattern + separate rules                      | "security group", "firewall", "ingress", "egress"   |
| `infra_secrets_management.md`  | Secrets Manager pattern + recovery_window                    | "secrets", "Secrets Manager", "Key Vault"           |
| `infra_k8s_externalsecret.md`  | ExternalSecret v1beta1 + secret injection                    | "ExternalSecret", "K8s secrets", "secret injection" |
| `infra_k8s_deployment.md`      | Deployment manifest + probes + resources + workload identity | "Deployment", "K8s", "liveness", "readiness"        |
| `infra_dockerfile.md`          | Multi-stage Dockerfile patterns (Java + Next.js)             | "Dockerfile", "multi-stage", "container", "image"   |
| `infra_cicd_pipeline.md`       | Plan/apply separation + pinned tool versions                 | "CI/CD", "pipeline", "plan", "apply", "Terraform"   |
| `infra_security_checklist.md`  | Full security checklist (all categories)                     | "security", "checklist", "compliance"               |

---

## Checkpoints

### Checkpoint 1 — Create `docs/` structure and populate files ✅ COMPLETE

- [x] Created `docs/be/`, `docs/fe/`, `docs/be_module/`, `docs/infra/` directories
- [x] Created 48 pattern files with YAML frontmatter (`tags:` + `executor:`) for RAG tuning
- [x] **Verified:** 49 total files in `docs/` (48 new + pre-existing `clean_code_guidelines.md`)
- **Result:** 219 chunks indexed in ChromaDB

### Checkpoint 2 — Rebuild knowledge base ✅ COMPLETE

- [x] Ran `python build_knowledge_base.py` — 219 chunks indexed
- [x] Tested 5 representative queries — all 5 returned correct source files:
  - `"aggregate root pattern registerEvent"` → `docs/be/be_spring_aggregate_root.md` ✅
  - `"useQuery isError error state component"` → `docs/fe/fe_hook_pattern.md` ✅
  - `"libs.versions.toml bundles Gradle"` → `docs/be_module/be_module_version_catalog.md` ✅
  - `"ExternalSecret v1beta1 refreshInterval"` → `docs/infra/infra_k8s_externalsecret.md` ✅
  - `"JOIN FETCH EntityGraph N+1"` → `docs/be/be_spring_jpa_n_plus_one.md` ✅
- **Retrieval quality: 5/5 — gate passed, proceed to Checkpoint 3**

### Checkpoint 3 — Slim the executor prompts ✅ COMPLETE

- [x] Rewrote `fe_executor.md` — 99 lines (target ~100)
- [x] Rewrote `be_executor.md` — 94 lines (target ~120)
- [x] Rewrote `be_module_executor.md` — 70 lines (target ~100)
- [x] Rewrote `infra_executor.md` — 57 lines (target ~80)
- **Total: 320 lines** (down from ~2,356 — 86% reduction)
- Every prompt: role + when-to-use table + KB search gate with named patterns + clean code bullets + strict scope rules
- Every code example removed from prompts — exclusively in `docs/` + RAG

### Checkpoint 4 — Integration test ✅ COMPLETE

- [x] Pipeline ran end-to-end (feature: "Testing the SDLC platform")
- [x] `agent.log.txt` confirms `[RAG SEARCH]` calls fired from Infra executor:
  - `'Docker Dockerfile standards best practices'` ✅
  - `'environment variables configuration'` ✅
  - `'CORS configuration frontend backend'` ✅
  - `'CI/CD deployment docker-compose'` ✅
- [x] All executors completed: planner → be_executor → fe_executor → qa_executor → infra_executor ✅
- [x] Files written to `tmp/be-repo/` and `tmp/fe-repo/` ✅
- **Note:** Planner generates verbose inline code in its architectural plan — separate issue, tracked below

### Checkpoint 5 — Cleanup ✅ COMPLETE

- [x] Fat executor backups already in `guideline/prompts/` ✅
- [x] Updated `executor_prompt_review.md` token budget section with before/after table and two-tier architecture note
- [x] Updated `career_plan.md` Phase 5 — added "Two-Tier Executor Restructure" completed section with what was built, metrics (320 lines, 86% reduction, 219 chunks), integration evidence, and remaining tasks

---

## Follow-up: SDLC Workflow Restructure (next phase)

Observed during Checkpoint 4: the **Planner generates verbose inline code** (TypeScript interfaces, Java classes, HTTP clients, etc.) in the architectural plan. This violates separation of concerns — the plan should describe _what_ to build, not _how_. The _how_ belongs in the executor output, retrieved from the KB.

**Decision:** Separate requirements/planning from execution into distinct pipeline phases:

- Phase 1 — Requirements: PRD, Jira tickets, stakeholder alignment
- Phase 2 — Architecture plan: _what_ to build, interfaces, data models, API contracts — NO code
- Phase 3 — Execution: executors write code, using KB for _how_

This is tracked as a separate workflow restructure task.

---

## Rollback

If retrieval quality is poor after Checkpoint 2, stop before Checkpoint 3. The fat executors in `guideline/prompts/` remain intact — copy them back to `prompts/` and the system is fully restored.

---

## File Naming Convention for `docs/`

All knowledge base files follow: `{executor_prefix}_{pattern_name}.md`

- `be_` — Spring Boot BE patterns
- `fe_` — Frontend patterns
- `be_module_` — Java module/build patterns
- `infra_` — Infrastructure patterns

Each file starts with:

```markdown
---
tags: [comma, separated, search, terms]
executor: be|fe|be_module|infra
---

# Pattern Name

...content...
```

This metadata improves ChromaDB retrieval precision.
