# SDLC Agentic Workflow

A LangGraph-powered multi-agent pipeline that automates the full Software Development Life Cycle (SDLC) using **Claude Sonnet 4.5** as the underlying LLM — from plain-English feature request to deployed, reviewed code.

---

## Current Status

| Capability                             | Status                            |
| -------------------------------------- | --------------------------------- |
| Natural language prompt input          | ✅ POC — working                  |
| Mocked Jira + Confluence tools         | ✅ POC — writes local `.md` files |
| Real filesystem read/write to monorepo | ✅ POC — working                  |
| RAG knowledge base (ChromaDB)          | ✅ POC — working                  |
| 6-node sequential executor pipeline    | ✅ POC — working                  |
| HITL Gate 1 — Planner approval         | 🔲 Phase 1 — not yet implemented  |
| Real Git branches + GitHub PRs         | 🔲 Phase 2 — not yet implemented  |
| PR comment → agent feedback loop       | 🔲 Phase 3 — not yet implemented  |
| Production hardening                   | 🔲 Phase 4 — not yet implemented  |
| Loop breaker / escalation node         | 🔲 Phase 5 — not yet implemented  |
| DevOps / infra approval gate           | 🔲 Phase 6 — not yet implemented  |
| Visual UI/UX preview check             | 🔲 Phase 7 — not yet implemented  |

See `guideline/hitl_implementation_plan.md` for the full roadmap.

---

## Enterprise Architecture (Target State)

```
                         ┌─────────────────────────────────┐
                         │  USER: plain-English feature     │
                         └────────────────┬────────────────┘
                                          │
                                    [Planner Node]
                                 Confluence PRD + Jira tickets
                                          │
                              ◄─── GATE 1: Human reviews ───►
                               Approve or correct the plan
                                          │ (approved)
                         ┌────────────────┼────────────────┐
                         │                │                │
                  [FE Executor]    [BE Executor]   (future: parallel)
                         │                │
                         └────────────────┘
                                  │
                          [Test Executor]
                       pytest + vitest tests
                                  │
                          [QA Executor] ◄──── if attempt > 5:
                        PASS / FAIL report     GATE 5: Human escalation
                                  │ (PASS)
                          [Infra Executor]
                       Dockerfiles + compose
                                  │
                         ◄─ GATE 6: Infra approval ──►
                          (cloud/IAM changes only)
                                  │ (approved)
                       [Visual Preview Node] (Phase 7)
                     Vercel/ephemeral deployment URL
                                  │
                         ◄─ GATE 7: Human eyes on UI ──►
                                  │ (approved)
                       Git commit → GitHub PR opened
                                  │
                  ◄─── GATE 2: Human reviews PR on GitHub ───►
                   Approve  ──────────────────  Request changes
                      │                               │
                 Auto-merge                    Webhook triggers
               → Deploy staging              new LangGraph thread
                                             with review comments
                                                      │
                                             Agent fixes + pushes
                                             new commit to same PR
```

---

## Nodes (Current Implementation)

### 1. Planner (`planner_node`)

Acts as the Lead Architect.

- **Input:** Raw user request
- **Output:** Confluence PRD page, 2 Jira tickets (FE + BE), architectural plan in state
- **Tools:** `create_confluence_page`, `create_jira_ticket`
- **Prompt:** Hardcoded
- **HITL Gate:** Gate 1 (Phase 1) — pauses here before any executor runs

### 2. FE Executor (`fe_executor_node`)

Acts as the Senior Frontend Developer.

- **Input:** Architect plan (human-approved)
- **Output:** React/TypeScript source files written to `FE_REPO_PATH`
- **Tools:** `list_directory`, `read_file`, `write_file`, `search_company_knowledge_base`
- **Prompt:** `prompts/fe_executor.md`

### 3. BE Executor (`be_executor_node`)

Acts as the Senior Backend Developer.

- **Input:** Architect plan (human-approved)
- **Output:** FastAPI Python source files written to `BE_REPO_PATH`
- **Tools:** `list_directory`, `read_file`, `write_file`, `search_company_knowledge_base`
- **Prompt:** `prompts/be_executor.md`

### 4. Test Executor (`test_executor_node`)

Acts as the QA Engineer.

- **Input:** Architect plan, FE and BE workspaces
- **Output:** pytest (BE) and vitest (FE) test files written to both repos
- **Tools:** `list_directory`, `read_file`, `write_file`, `search_company_knowledge_base`
- **Prompt:** `prompts/test_executor.md`

### 5. QA Executor (`qa_executor_node`)

Acts as the QA Architect — the Orchestrator layer.

- **Input:** All generated source and test files
- **Output:** `qa_report.md` with PASS/FAIL verdict
- **Tools:** `list_directory`, `read_file`, `write_file`, `search_company_knowledge_base`
- **Prompt:** `prompts/qa_executor.md`
- **HITL Gate:** Gate 5 (Phase 5) — if `attempt_count >= 5`, escalates to human instead of looping

### 6. Infra Executor (`infra_executor_node`)

Acts as the Senior DevOps Engineer.

- **Input:** Architect plan, FE and BE workspaces
- **Output:** `Dockerfile` in each repo, `docker-compose.yml` in BE repo
- **Tools:** `list_directory`, `read_file`, `write_file`, `search_company_knowledge_base`
- **Prompt:** `prompts/infra_executor.md`
- **HITL Gate:** Gate 6 (Phase 6) — any cloud/IAM change requires explicit human `yes`

---

## Nodes (Planned — Not Yet Implemented)

| Node                    | Phase | Role                                                      |
| ----------------------- | ----- | --------------------------------------------------------- |
| `human_escalation_node` | 5     | Terminal prompt when QA loop exceeds attempt limit        |
| `infra_approval_node`   | 6     | Explicit confirmation before any cloud API call           |
| `visual_preview_node`   | 7     | Triggers ephemeral deployment, prompts human to review UI |

---

## State

The shared state (`SDLCState`) passed between all nodes — current fields plus planned additions:

| Field                | Type  | Status     | Description                                                  |
| -------------------- | ----- | ---------- | ------------------------------------------------------------ |
| `user_request`       | `str` | ✅         | Raw input from the user                                      |
| `prd`                | `str` | ✅         | Confirmation that the PRD was saved to Confluence            |
| `architect_plan`     | `str` | ✅         | Architectural plan (may be human-amended via `update_state`) |
| `fe_output`          | `str` | ✅         | Summary of what the FE Executor wrote                        |
| `be_output`          | `str` | ✅         | Summary of what the BE Executor wrote                        |
| `test_output`        | `str` | ✅         | Summary of what the Test Executor wrote                      |
| `qa_report`          | `str` | ✅         | Full QA report content                                       |
| `infra_output`       | `str` | ✅         | Summary of what the Infra Executor wrote                     |
| `attempt_count`      | `int` | 🔲 Phase 5 | Number of QA→Executor iterations (escalate at ≥5)            |
| `human_escalation`   | `str` | 🔲 Phase 5 | Human hint injected when loop breaker fires                  |
| `visual_preview_url` | `str` | 🔲 Phase 7 | URL of the ephemeral UI preview deployment                   |

---

## Knowledge Base (RAG)

Each executor has access to `search_company_knowledge_base`, which queries a local ChromaDB vector database built from `docs/*.md`. Agents are instructed via their prompt files to search the knowledge base before writing any code.

- **Build:** `python build_knowledge_base.py` (run once; re-run when `docs/` changes)
- **Storage:** `rag_db/chroma.sqlite3`
- **Model:** `all-MiniLM-L6-v2` (HuggingFace, runs locally, no API cost)

See `guideline/how_i_did_it.md` for full RAG concepts.

---

## Integrations

### Currently Mocked (POC)

| Tool                     | Simulates           | Local side-effect                |
| ------------------------ | ------------------- | -------------------------------- |
| `create_confluence_page` | Confluence REST API | Writes `CONFLUENCE_PATH/*.md`    |
| `create_jira_ticket`     | Jira REST API       | Writes `JIRA_PATH/*.md`          |
| `create_github_pr`       | GitHub REST API     | Console log only                 |
| `git_commit_to_branch`   | Git CLI             | Defined + validated but disabled |

### Planned (Phase 2+)

| Integration                  | Phase | What it enables                       |
| ---------------------------- | ----- | ------------------------------------- |
| Real GitHub PRs via PyGithub | 2     | Actual code review on GitHub          |
| Git branch per Jira ticket   | 2     | Traceable `feat/FE-123-...` branches  |
| GitHub Webhook receiver      | 3     | PR comments trigger new agent thread  |
| Vercel / preview deployment  | 7     | Ephemeral UI for visual review        |
| LangSmith tracing            | 4     | Full observability of every agent run |
| PostgreSQL checkpointer      | 4     | State survives process restarts       |

---

## Security

| Control                     | Status     | Detail                                                                    |
| --------------------------- | ---------- | ------------------------------------------------------------------------- |
| Path traversal guard        | ✅         | `write_file` rejects paths outside `FE_REPO_PATH` / `BE_REPO_PATH`        |
| Prompt injection delimiters | ✅         | `user_request` and `architect_plan` wrapped in `"""` in all prompts       |
| API key guard               | ✅         | Raises `EnvironmentError` at startup if `ANTHROPIC_API_KEY` missing       |
| Secrets on disk             | ⚠️         | `.env` file — acceptable for POC, must move to secrets manager in Phase 4 |
| Cloud API guard             | 🔲 Phase 6 | Infra approval gate before any cloud/IAM call                             |

---

## Dependencies

| Package                    | Purpose                                            |
| -------------------------- | -------------------------------------------------- |
| `langchain-anthropic`      | LLM interface for Claude                           |
| `langgraph`                | Graph-based agent orchestration                    |
| `langchain-chroma`         | ChromaDB vector store integration                  |
| `langchain-huggingface`    | Local embedding model for RAG                      |
| `langchain-community`      | Document loaders (`DirectoryLoader`, `TextLoader`) |
| `langchain-text-splitters` | Chunking documents for RAG ingestion               |
| `python-dotenv`            | Loads `.env` at startup                            |

---

## Running

```bash
source venv/bin/activate
python sdlc_workflow.py
```

Rebuild knowledge base after updating `docs/`:

```bash
python build_knowledge_base.py
```

Set `ANTHROPIC_API_KEY` in `.env` before running.

## Running

```bash
source venv/bin/activate
python sdlc_workflow.py
```

To rebuild the knowledge base after updating `docs/`:

```bash
python build_knowledge_base.py
```

Set `ANTHROPIC_API_KEY` in your `.env` file before running.
