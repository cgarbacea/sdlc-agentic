# Executor Prompt Review

**Date:** 11 May 2026  
**Reviewer:** AI Prompt Engineer  
**Scope:** `fe_executor.md`, `be_executor.md`, `be_module_executor.md`, `infra_executor.md`

---

## Executive Summary

The four executors form a solid, production-grade set of coding standards for an AI SDLC pipeline. They are grounded in real codebases, use consistent structure, and separate concerns cleanly. The main strengths are specificity (real code examples, not abstract advice), defensiveness (verified before writing), and principle-first design (cloud/framework-agnostic rules with illustrative examples).

There are no critical failures. The issues identified are refinements that would improve consistency, reduce LLM ambiguity, and close a few gaps in coverage.

---

## Scoring

| Executor                | Clarity | Completeness | Specificity | Consistency | Total     |
| ----------------------- | ------- | ------------ | ----------- | ----------- | --------- |
| `fe_executor.md`        | 4/5     | 4/5          | 4/5         | 4/5         | **16/20** |
| `be_executor.md`        | 5/5     | 4/5          | 5/5         | 4/5         | **18/20** |
| `be_module_executor.md` | 4/5     | 5/5          | 5/5         | 4/5         | **18/20** |
| `infra_executor.md`     | 4/5     | 4/5          | 4/5         | 4/5         | **16/20** |

---

## What Works Well (Strengths)

### 1. Explore-before-write discipline is consistent across all four

Every executor opens with the same three-step gate: knowledge base → directory structure → read existing files. This prevents the most common LLM failure mode — generating code without understanding the target context. This is the single most valuable pattern in the set.

### 2. Real code examples, not abstract advice

The executors are grounded in actual project code (`backend-modulith`, `platform-monorepo`, `rules-engine`, `health-coach-portal-cronus-infrastructure`). Every pattern has a real-world reference. This makes them far more reliable than generic style guides.

### 3. Principle-over-tool design

The `be_executor`, `infra_executor`, and `fe_executor` all correctly separate the principle (e.g. "secrets never in files") from the implementation (e.g. "use AWS Secrets Manager"), with explicit notes to verify the toolchain first. This means the executors transfer to new projects without rewriting.

### 4. Scope rules are explicit and specific

Each executor ends with a `STRICT SCOPE RULES` section that explicitly forbids common LLM over-generation patterns (README files, extra abstractions, undocumented dependencies). This is critical for keeping AI output within the architect's plan.

### 5. Known trade-offs are documented honestly

`be_executor.md` explicitly calls out the JPA-on-aggregate trade-off with its rationale. `infra_executor.md` notes `recovery_window_in_days = 0` as dev-only. This intellectual honesty prevents cargo-culting.

### 6. The clean code section in `be_executor.md` is the best section in the set

SOLID mapped to Spring code, the guard-clause example with before/after, CQS, Boy Scout Rule — all actionable, all concrete. This section should be considered as a template for adding equivalent sections to `fe_executor.md`.

---

## Issues and Recommendations

### Issue 1 — `fe_executor.md` lacks a clean code / principles section

**Severity: Medium**

`be_executor.md` opens with a comprehensive Clean Code section (naming, SOLID, error handling, Boy Scout Rule). `fe_executor.md` jumps straight to architecture patterns. TypeScript/React code quality principles are just as important as Java ones, but they're absent.

**Recommendation:** Add a "Clean Code Principles" section to `fe_executor.md` covering:

- Naming conventions for hooks (`useEntityName`), components (`EntityName`), and types
- Component responsibility: presentational vs container
- Avoid prop drilling: when to use context vs Zustand
- `useEffect` rules: stable dependencies, cleanup functions
- TypeScript discipline: no `any`, explicit return types on exported functions

---

### Issue 2 — The `be_executor.md` and `be_module_executor.md` relationship is implicit

**Severity: Medium**

`be_module_executor.md` mentions it "complements `be_executor.md`" but doesn't explain when to use which. An LLM receiving both in context may apply both simultaneously, or may be uncertain which takes precedence for a given task.

**Recommendation:** Add a clear decision table at the top of each:

```
# be_executor.md — use when:
# - Adding a new module to an existing Spring Modulith service
# - Implementing an endpoint, service, repository, or event in Spring
#
# be_module_executor.md — use when:
# - Creating a new multi-module Gradle project from scratch
# - Adding a new Gradle submodule to an existing project
# - Working on build configuration, quality gates, or CI pipelines
```

---

### Issue 3 — `infra_executor.md` has a stale ExternalSecret API reference

**Severity: Medium**

The "Secret Injection" section under "Container Orchestration Patterns" still uses the deprecated `kubernetes-client.io/v1` API:

```yaml
apiVersion: kubernetes-client.io/v1
kind: ExternalSecret
```

The Helm Chart section later correctly uses `external-secrets.io/v1beta1`. This contradiction will cause an LLM to generate deprecated manifests when following the "Container Orchestration Patterns" section.

**Recommendation:** Update the inline example in the "Container Orchestration Patterns" section to use `external-secrets.io/v1beta1`, consistent with the Helm section.

---

### Issue 4 — Missing error state handling in the `fe_executor.md` hook pattern

**Severity: Low-Medium**

The hook pattern shows:

```typescript
return useQuery({ queryKey, queryFn, enabled, staleTime });
```

But says "hooks return the raw React Query result — they do not catch errors or show toasts". This is correct but incomplete — it doesn't show _how_ the consuming component should handle the `isError` / `error` state. An LLM following this pattern will write hooks correctly but may generate components that silently ignore errors.

**Recommendation:** Add a brief component example showing the error state:

```tsx
const { data, isLoading, isError, error } = useMyEntity(id);
if (isLoading) return <Skeleton />;
if (isError) return <ErrorBoundary message={error.message} />;
```

---

### Issue 5 — `be_executor.md` Liquibase section lacks the master changelog structure

**Severity: Low**

The Liquibase pattern shows a changeset SQL file but not the `db.changelog-master.xml` that includes it. A new module contributor will write a migration file but won't know how to wire it into the master changelog.

**Recommendation:** Add the include pattern:

```xml
<!-- db/changelog/db.changelog-master.xml -->
<include file="migrations/001_create_users_table.sql" relativeToChangelogFile="true"/>
```

---

### Issue 6 — No explicit instruction about LLM self-correction on `be_executor.md` ArchUnit failures

**Severity: Low**

Phase 5 of the career plan explicitly calls for "ArchUnit feedback loop" — if generated code violates rules, the executor should retry. The `be_executor.md` documents the rules but doesn't instruct the executor what to do when it _detects_ a violation in its own output.

**Recommendation:** Add to the ArchUnit section:

> "Before writing any file, mentally validate it against all five rules above. If your code would violate one, restructure the code — do not write the violation and expect a later fix."

This is already partially present ("If your code would break any of these rules, restructure it before writing the file") but should be more explicit about the self-check step.

---

### Issue 7 — `infra_executor.md` missing the Naming Convention section generalisation

**Severity: Low**

The naming convention section still shows:

```hcl
# Every resource name follows: <workspace>-<name>-<resource-type>
# e.g. dev-my-service-vpc, prod-my-service-eks
```

The `eks` example leaks the AWS-specific original. A minor cleanup.

---

## Structural Observations

### Token budget considerations

**Updated after two-tier restructure (11 May 2026):** All code examples and architecture patterns have been extracted to `docs/` (49 files, 219 RAG chunks). Executors now contain only role identity, when-to-use table, KB search gate, clean code bullet points, and scope rules.

| File                    | Before          | After         | Reduction |
| ----------------------- | --------------- | ------------- | --------- |
| `fe_executor.md`        | 454 lines       | 99 lines      | −78%      |
| `be_executor.md`        | 799 lines       | 94 lines      | −88%      |
| `be_module_executor.md` | 624 lines       | 70 lines      | −89%      |
| `infra_executor.md`     | 479 lines       | 57 lines      | −88%      |
| **Total**               | **2,356 lines** | **320 lines** | **−86%**  |

Code patterns are retrieved on demand via `search_company_knowledge_base` — confirmed working in integration test (RAG SEARCH calls observed in `agent.log.txt`). The splitting recommendation above is now obsolete — the two-tier architecture solves the token budget problem.

### Coverage gaps

| Gap                                                                       | Home             | Status                                   |
| ------------------------------------------------------------------------- | ---------------- | ---------------------------------------- |
| N+1 / JPA query patterns (JOIN FETCH, @EntityGraph, FetchType.EAGER)      | `be_executor.md` | ✅ Added                                 |
| Pagination patterns (offset vs cursor, @PageableDefault, unbounded lists) | `be_executor.md` | ✅ Added                                 |
| Accessibility (semantic HTML, aria-label, keyboard navigation)            | `fe_executor.md` | ✅ Added                                 |
| Structured logging / MDC correlation IDs / JSON format                    | `be_executor.md` | ✅ Added                                 |
| API versioning / deprecation strategy                                     | `be_executor.md` | ✅ Added                                 |
| React performance (`useMemo`, `useCallback`)                              | `fe_executor.md` | ✅ Already covered in clean code section |

---

## Priority Order for Improvements

| #   | Issue                                                                           | Status   |
| --- | ------------------------------------------------------------------------------- | -------- |
| 1   | Fix stale ExternalSecret API in `infra_executor.md`                             | ✅ Fixed |
| 2   | Make be_executor / be_module_executor fully independent with when-to-use tables | ✅ Fixed |
| 3   | Add clean code principles to `fe_executor.md`                                   | ✅ Fixed |
| 4   | Add error state example in component pattern                                    | ✅ Fixed |
| 5   | Add Liquibase master changelog pattern                                          | ✅ Fixed |
| 6   | Strengthen ArchUnit self-check language                                         | ✅ Fixed |
| 7   | Remove AWS-specific naming example (`eks`)                                      | ✅ Fixed |

---

## Final Verdict

These executors are production-ready for the AI SDLC pipeline. They encode real architectural knowledge extracted from real codebases, maintain principle-over-tool design, and consistently enforce the explore-before-write discipline. The six issues identified are refinements, not regressions. The set will produce consistent, well-structured code across FE, BE, and infra deliverables.

The `be_executor.md` is the strongest of the four — the clean code section in particular should be used as the template for expanding the other executors.
