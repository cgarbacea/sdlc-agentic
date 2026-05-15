# HITL Implementation Plan

Goal: Track Human-in-the-Loop (HITL) gates against the current runtime implementation and remaining roadmap.

Reference concepts: `guideline/how_i_did_it.md`

---

## Current Human Gates Overview

```text
requirements -> architect -> GATE 1 (human plan review) ->
fe_executor -> be_executor -> test_executor -> qa_executor -> infra_executor
                                                     |
                                                     +-> GATE 2 (GitHub PR review, outside runtime)
```

- Gate 1 is implemented inside the LangGraph runtime (pause/resume with checkpoint).
- Gate 2 is implemented operationally through GitHub PR workflow after agent commits/PRs.

---

## Phase 1 - Gate 1 Plan Approval (Pre-Development)

Status: ✅ Completed

What: Pause after architecture planning and require human approval/corrections before executors run.

### Completed work

- [x] Use persistent SQLite checkpointer (`SqliteSaver`) in graph compilation.
- [x] Configure `interrupt_before=["fe_executor"]`.
- [x] Use `thread_id`-based resume flow in CLI and MCP usage.
- [x] Display architecture plan for human review before resume.
- [x] Support iterative correction loop via `app.update_state()` and resume via `app.stream(None, config)`.

### Acceptance status

- [x] Runtime pauses before first executor.
- [x] Human corrections rewrite the plan and propagate to execution.
- [x] Explicit approval resumes without rewriting.

---

## Phase 2 - Gate 2 PR Approval (Post-Development)

Status: ✅ Completed (with credential-aware fallback)

What: Executors commit to branches and open PRs; human review happens in GitHub.

### Completed work

- [x] Real git branch/commit operations enabled via `gitpython`.
- [x] FE/BE executors invoke git + PR tooling.
- [x] `create_github_pr` opens real PRs via PyGithub when `GITHUB_ENABLED=true`.
- [x] Safe fallback when credentials are missing: simulated PR message instead of runtime failure.
- [x] CLI prints PR URLs when available in final state.

### Acceptance status

- [x] Workflow exits cleanly after execution.
- [x] Branches and commits are created by agent tools.
- [x] PR creation is real when credentials are configured; otherwise explicitly simulated.

---

## Phase 3 - PR Feedback Loop (Review Comment -> Agent Fix)

Status: 🔲 Not implemented

### Planned tasks

- [ ] Add webhook receiver for GitHub review events.
- [ ] Parse review comments and PR context.
- [ ] Trigger targeted correction run with injected human feedback.
- [ ] Push follow-up commits to the same PR branch.
- [ ] Post acknowledgment/comment back to PR.

---

## Phase 4 - Production Hardening

Status: 🟨 In progress (partial)

### Completed

- [x] Persistent checkpointer in runtime (SQLite).
- [x] Structured logging scaffolding present.
- [x] LangSmith configuration flags and environment wiring present.

### Remaining

- [ ] Secrets manager integration (move off local `.env` for production).
- [ ] Retry/backoff policy around fragile external/tool calls.
- [ ] Async parallel FE/BE orchestration (if desired).
- [ ] Durable audit log of tool actions.
- [ ] Queue/rate-limiting for concurrent feature runs.

---

## Phase 5 - Loop Breaker Escalation Gate

Status: 🔲 Not implemented

What: Prevent infinite retry loops by escalating to human input after repeated QA failures.

### Planned tasks

- [ ] Add `attempt_count` and `human_escalation` fields to `SDLCState`.
- [ ] Implement `human_escalation_node` with pause + prompt.
- [ ] Add routing logic from QA to escalation when threshold exceeded.
- [ ] Inject human hint into next executor retry.

---

## Phase 6 - Infra Approval Gate (Money and Keys)

Status: 🔲 Not implemented

What: Require explicit human approval for high-risk infrastructure actions.

### Planned tasks

- [ ] Define high-risk infra/tool action patterns.
- [ ] Add `infra_approval_node` and rejection-safe exit path.
- [ ] Record approvals/rejections in audit log.

---

## Phase 7 - Visual Preview Gate

Status: 🔲 Not implemented

What: Human visual approval of preview deployment before final completion for UI-impacting features.

### Planned tasks

- [ ] Integrate FE preview deployment pipeline that posts preview URL to PR.
- [ ] Add runtime node to retrieve and present preview URL.
- [ ] Route visual feedback back to FE executor loop when needed.

---

## Priority Order (Updated)

1. [ ] Deliver demo evidence pack for ArchUnit fail -> retry -> pass loop (portfolio-ready proof).
2. [ ] Add MCP health endpoint for operational monitoring.
3. [ ] Implement QA escalation loop breaker (Phase 5).
4. [ ] Implement retry/backoff wrappers (Phase 4 remaining).
5. [ ] Implement PR feedback webhook loop (Phase 3).
6. [ ] Implement infra and visual approval gates (Phases 6 and 7).

This order reflects current runtime maturity: core Gate 1 and PR workflow are in place, while operational safety and feedback automation are the next highest-value gaps.
