# SDLC Agentic Workflow

A LangGraph-powered multi-agent pipeline that automates the Software Development Life Cycle (SDLC) from plain-English request to generated code, QA output, and infrastructure artifacts.

---

## Runtime Status (As Implemented)

| Capability                                      | Status                                                                  |
| ----------------------------------------------- | ----------------------------------------------------------------------- |
| Natural language feature input                  | ✅ Implemented                                                          |
| Requirements and architecture split             | ✅ Implemented (`requirements` -> `architect`)                          |
| Gate 1 HITL plan approval                       | ✅ Implemented (`interrupt_before=["fe_executor"]`)                     |
| Persistent checkpoint state                     | ✅ Implemented (SQLite checkpointer)                                    |
| RAG knowledge base (ChromaDB)                   | ✅ Implemented                                                          |
| FE -> BE -> Test -> QA -> Infra execution chain | ✅ Implemented                                                          |
| Real git commit and branch creation             | ✅ Implemented                                                          |
| Real GitHub PR creation via API                 | ✅ Implemented when `GITHUB_ENABLED=true`; simulated fallback otherwise |
| PR review comment -> auto-fix loop              | 🔲 Not implemented                                                      |
| QA escalation loop breaker node                 | 🔲 Not implemented                                                      |
| Infra approval gate                             | 🔲 Not implemented                                                      |
| Visual preview approval gate                    | 🔲 Not implemented                                                      |

See `guideline/hitl_implementation_plan.md` for the roadmap of pending HITL gates.

---

## Current Runtime Graph

```text
requirements -> architect -> [Gate 1 pause before fe_executor] ->
fe_executor -> be_executor -> test_executor -> qa_executor -> infra_executor -> END
```

Notes:

- Entry point is `requirements`.
- `planner` is legacy/deprecated and is not wired into the runtime graph.
- Gate 1 pauses after architecture planning and before any code-writing executor runs.

---

## Nodes (Current Implementation)

### 1. Requirements (`requirements_node`)

- Role: Product analysis and requirement capture.
- Output: PRD + Jira ticket artifacts via tools, plus `state["requirements"]` summary.
- Rule: Defines what to build and why, not architecture internals.

### 2. Architect (`architect_node`)

- Role: Produce a no-code architectural plan.
- Output: `state["architect_plan"]` with interfaces, contracts, and implementation guidance in prose/tables.
- Rule: No code snippets by design.

### 3. FE Executor (`fe_executor_node`)

- Role: Frontend implementation from approved plan + RAG knowledge retrieval.

### 4. BE Executor (`be_executor_node`)

- Role: Backend implementation from approved plan + RAG knowledge retrieval.
- Extra behavior: ArchUnit validation retry loop (if enabled) before commit/PR.

### 5. Test Executor (`test_executor_node`)

- Role: Generates tests aligned to generated FE/BE changes.

### 6. QA Executor (`qa_executor_node`)

- Role: Produces QA report for generated work.
- Note: Escalation routing node is not implemented yet.

### 7. Infra Executor (`infra_executor_node`)

- Role: Generates infrastructure-related artifacts (for example Dockerfiles/compose files per plan).
- Note: Explicit human infra-approval gate is not implemented yet.

---

## State Schema

The active shared state is defined in `state.py`:

| Field                | Type   | Status     | Description                                 |
| -------------------- | ------ | ---------- | ------------------------------------------- |
| `user_request`       | `str`  | ✅         | Raw user request                            |
| `requirements`       | `str`  | ✅         | Requirements summary from Requirements node |
| `prd`                | `str`  | ✅         | PRD generation result                       |
| `architect_plan`     | `str`  | ✅         | Human-reviewable architecture plan          |
| `fe_output`          | `str`  | ✅         | FE executor summary                         |
| `be_output`          | `str`  | ✅         | BE executor summary                         |
| `test_output`        | `str`  | ✅         | Test executor summary                       |
| `qa_report`          | `str`  | ✅         | QA report content                           |
| `infra_output`       | `str`  | ✅         | Infra executor summary                      |
| `pr_urls`            | `list` | ✅         | PR links opened by executors                |
| `attempt_count`      | `int`  | 🔲 Planned | QA retry/escalation tracking                |
| `human_escalation`   | `str`  | 🔲 Planned | Human hint for stuck-loop recovery          |
| `visual_preview_url` | `str`  | 🔲 Planned | Preview URL for visual approval gate        |

---

## Integrations

### Implemented

| Integration         | Status      | Behavior                                                         |
| ------------------- | ----------- | ---------------------------------------------------------------- |
| Confluence tool     | ✅          | Local mock artifact write                                        |
| Jira tool           | ✅          | Local mock artifact write                                        |
| Git branch + commit | ✅          | Real git operations                                              |
| GitHub PR API       | ✅/fallback | Real PR when credentials configured; simulated message otherwise |
| SQLite checkpoints  | ✅          | Pause/resume by `thread_id`                                      |

### Planned

| Integration                     | Status | Purpose                                    |
| ------------------------------- | ------ | ------------------------------------------ |
| GitHub review webhook           | 🔲     | PR comment -> agent correction loop        |
| Preview deployment integration  | 🔲     | Human visual approval gate                 |
| Dedicated infra approval policy | 🔲     | Human confirmation for risky infra actions |

---

## Observability and Security Snapshot

| Area                               | Status | Notes                                                                      |
| ---------------------------------- | ------ | -------------------------------------------------------------------------- |
| Structured logging                 | ✅     | Configured via observability module (`json`/`console`)                     |
| LangSmith tracing config           | ✅     | Config flags/env present; enable per environment                           |
| Path traversal guard in file tools | ✅     | Writes constrained to allowed roots                                        |
| Provider guardrails                | ✅     | Multi-provider checks (`anthropic`, `openai_compatible`, `ollama`, `stub`) |
| Secrets manager integration        | 🔲     | Still env-based for local development                                      |

---

## Run Commands

```bash
source venv/bin/activate
python main.py
```

Provider preflight:

```bash
python main.py --provider-check-only
```

Non-interactive run:

```bash
python main.py --feature "Add dark mode toggle" --non-interactive
```

Resume paused run:

```bash
python main.py --thread-id <existing-thread-id>
```

Rebuild the knowledge base after `docs/` updates:

```bash
python build_knowledge_base.py
```
