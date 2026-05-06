# HITL Implementation Plan

**Goal:** Evolve `sdlc_workflow.py` from a fully autonomous POC into an enterprise-grade system where humans review and approve agent output at every critical gate.

**Reference concepts:** See `guideline/how_i_did_it.md` → _Human-in-the-Loop (HITL) Concepts_

---

## The Two Human Gates

```
[Planner] ──► GATE 1: Human reviews PRD + Architecture Plan
                │
                ▼ (approved / corrected)
[FE Executor] → [BE Executor] → [Test Executor] → [QA Executor] → [Infra Executor]
                                                                        │
                                                              GATE 2: Human reviews PRs on GitHub
                                                                        │
                                                                        ▼ (approved)
                                                                    Auto-merge → Deploy to Staging
```

---

## Phase 1 — Checkpoint 1: Planner Approval (Pre-Development)

**What:** Pause the workflow after the Planner produces the PRD, Jira tickets, and architectural plan — before any executor writes a single line of code.

**Why:** The most expensive mistakes happen downstream. If the architecture plan is wrong, all 5 executors will build the wrong thing. A 2-minute human review here saves hours of re-work.

### Tasks

- [x] Add `MemorySaver` checkpointer to the workflow compilation.
- [x] Add `interrupt_before=["fe_executor"]` to `workflow.compile()`.
- [x] Add a `thread_id` config based on the user's feature description (e.g., slugified input + timestamp).
- [x] After the Planner run completes, display the `architect_plan` and Jira ticket summaries clearly in the terminal.
- [x] Prompt the human: **"Approve this plan? (yes / type corrections)"**
  - If `yes` → resume with `app.stream(None, config)`.
  - If corrections → call `app.update_state(config, {"architect_plan": amended_plan})` then resume.
- [x] Update `initial_state` and the runner loop to support this two-phase execution.

### Acceptance Criteria

- [x] The workflow stops after the Planner and prints the plan to the terminal.
- [x] The human can type corrections and the FE Executor receives the amended plan.
- [x] The human can type `yes` and the workflow continues unmodified.

---

## Phase 2 — Checkpoint 2: PR Approval (Post-Development)

**What:** After the Infra Executor completes, the workflow opens real GitHub Pull Requests. The human reviews them on GitHub. The workflow terminates — no Python process sits waiting.

**Why:** Code reviews take hours or days. Keeping a terminal process paused is brittle and impractical. GitHub is already the natural home for code review.

### Tasks

- [x] Enable real git operations: `git_commit_to_branch` auto-inits the repo if no `.git` folder exists.
- [x] Wire `git_tools` into FE and BE executor agents — both now commit and open PRs after writing code.
- [ ] Replace the mocked `create_github_pr` with a real PyGithub API call using `GITHUB_TOKEN` — production step, pending real repo connection.
- [x] Branch name is derived from the feature slug (e.g. `feat/fe-<slug>`). Jira ticket ID linkage is a Phase 3 refinement.
- [x] The workflow prints PR URLs at the end. Currently simulated with realistic fake URLs until real repos are connected.

### Acceptance Criteria

- After the workflow completes, real branches exist in the FE and BE GitHub repos.
- Real PRs are open and visible on GitHub with a description referencing the Jira ticket.
- The Python process exits cleanly — no hanging state.

---

## Phase 3 — Feedback Loop: PR Comments → Agent Fix

**What:** When the human leaves a review comment on the GitHub PR requesting changes, a webhook automatically starts a new LangGraph thread that reads the comment, fixes the code, and pushes a new commit to the same PR.

**Why:** This closes the full SDLC loop. The human is the Lead Engineer who guides the agent, not a rubber-stamper.

### Tasks

- [ ] Set up a webhook receiver (FastAPI endpoint or serverless function) that listens for GitHub `pull_request_review` events.
- [ ] When a "changes requested" review is received, extract the PR body and comments.
- [ ] Start a new LangGraph thread with the review comments injected into the executor prompt as `HUMAN_FEEDBACK`.
- [ ] The executor pulls the existing branch, reads the PR diff, applies the fix, and pushes a new commit.
- [ ] The webhook receiver posts a GitHub comment on the PR confirming the agent has acted.

### Acceptance Criteria

- Leaving a review comment on a PR triggers a new agent run within 60 seconds.
- The agent pushes a new commit addressing the feedback.
- The PR is updated and the human receives a GitHub notification.

---

## Phase 4 — Production Hardening

**What:** Replace development shortcuts with production-grade infrastructure.

### Tasks

- [ ] **Persistent checkpointer:** Replace `MemorySaver` with `AsyncPostgresSaver` or `AsyncSqliteSaver` so state survives process restarts.
- [ ] **Secrets management:** Move `ANTHROPIC_API_KEY` and `GITHUB_TOKEN` from `.env` to a secrets manager (AWS Secrets Manager or HashiCorp Vault).
- [ ] **Retry policies:** Wrap LLM calls with exponential backoff for transient API errors.
- [ ] **Observability:** Add LangSmith tracing or equivalent so every agent run is logged and inspectable.
- [ ] **Async execution:** Migrate the graph to async mode so FE and BE executors can run concurrently (using LangGraph's `Send()` API).
- [ ] **Audit log:** Write a structured JSON log of every tool call (file written, Jira ticket created, PR opened) to a persistent store for compliance.
- [ ] **Rate limiting:** Add a queue in front of the workflow so concurrent feature requests don't exceed API rate limits.

### Acceptance Criteria

- A process restart does not lose an in-progress workflow run.
- No secrets are stored on disk.
- FE and BE executors run in parallel, reducing total wall-clock time by ~40%.
- Every run produces a traceable, queryable audit trail.

---

## Phase 5 — The "Help, I'm Stuck!" Escalation (Loop Breaker)

**What:** If an executor agent fails to satisfy the QA check after a set number of attempts, route to a human escalation node instead of looping forever.

**Why:** An agent stuck in a loop burns API tokens, wastes time, and never self-resolves. After N attempts, a human hint is always cheaper than N more LLM calls.

**Where in the graph:** Between `qa_executor_node` and the executor nodes, via a routing function.

### Tasks

- [ ] Add an `attempt_count: int` field to `SDLCState` (default `0`).
- [ ] Add a `human_escalation: str` field to `SDLCState` for the human's hint.
- [ ] Add a `human_escalation_node` that pauses the graph and prompts the terminal: _"🚨 Agent is stuck after N attempts. Here is the QA report. What should I do?"_
- [ ] Update the QA routing function: if `attempt_count >= 5`, route to `human_escalation_node` instead of back to the executor.
- [ ] After the human types a hint, `update_state` with the hint injected into the relevant executor's next prompt, then resume.
- [ ] Reset `attempt_count` to `0` after a successful QA pass.

### Acceptance Criteria

- After 5 failed QA attempts, the workflow pauses and asks the human for help.
- The human's hint is injected into the executor's next prompt.
- Successful runs never hit the escalation node.

---

## Phase 6 — The DevOps / Infrastructure Gate ("Money & Keys" Check)

**What:** Any tool call that modifies cloud infrastructure or IAM configuration requires an explicit human confirmation before execution.

**Why:** Writing frontend code is sandboxed in a PR. A Terraform script that drops a production database, opens port 22 to the public, or provisions $10k of GPU servers is irreversible. This gate is non-negotiable for enterprise deployment.

**Where in the graph:** As a pre-execution guard inside `infra_executor_node`, before any cloud API tool call.

### Tasks

- [ ] Define a list of **high-risk tool patterns** (e.g., any `write_file` to an `infrastructure/` or `terraform/` path, any future `run_terraform`, `aws_iam_update` tools).
- [ ] Add an `infra_approval_node` that presents the proposed infra changes and asks: _"⚠️ Agent wants to apply these infrastructure changes. Approve? (yes / no)"_
- [ ] Wire `infra_executor_node → infra_approval_node → (approved) → continue | (rejected) → END`.
- [ ] The approval gate also applies to `create_github_pr` when targeting infrastructure repos.
- [ ] Log every approved/rejected infra action to the audit log from Phase 4.

### Acceptance Criteria

- No infrastructure file is written and no cloud API is called without an explicit `yes` from the human.
- A `no` answer stops the infra phase cleanly without crashing the workflow.
- All approvals are recorded in the audit log with a timestamp.

---

## Phase 7 — The Visual UI/UX Check ("Does It Look Ugly?" Gate)

**What:** After the FE executor opens a PR, a CI/CD pipeline automatically deploys a preview environment from the feature branch. The LangGraph workflow polls for the preview URL, presents it to the human, and waits for visual approval before the run completes.

**Why:** Automated tests can verify that a button exists and is clickable. They cannot tell you it is neon green, overlapping the logo, or broken on mobile. Human eyes are the only reliable UI check. Using the CI/CD pipeline (rather than triggering deployments from Python) means the same pipeline that deploys to staging and production also handles previews — no new tooling, no new permissions.

**Architecture:** Pipeline-based (preferred over Vercel CLI triggered from Python)

```
FE Executor writes code
    → git_commit_to_branch (Phase 2)
    → create_github_pr opens PR
    → CI/CD pipeline triggers automatically on feat/* branch push
    → Vercel / Netlify / custom pipeline deploys preview
    → Posts preview URL as GitHub PR comment
    → visual_review_node polls PR comments for the URL
    → Presents URL to human in terminal
    → Human approves or describes visual changes
    → If changes → back to FE executor with HUMAN_VISUAL_FEEDBACK
    → If approved → END
```

**Where in the graph:** New `visual_review_node` after `infra_executor_node`, before `END`.

**Prerequisites:** Phase 2 (real GitHub PRs) must be complete. The FE repo must have a CI/CD pipeline configured that deploys previews on PR creation.

### Tasks

#### CI/CD Pipeline (FE repo — one-time setup)

- [ ] Add a GitHub Actions workflow to the FE repo: triggers on `pull_request` targeting `main`.
- [ ] Workflow runs `npm install && npm run build`, deploys to preview host (Vercel, Netlify, or self-hosted), and posts the preview URL as a PR comment using `github-actions/deploy-pages` or equivalent.
- [ ] Confirm the preview URL appears in PR comments before wiring the LangGraph side.

#### LangGraph side (this project)

- [ ] Add `visual_preview_url: str` to `SDLCState`.
- [ ] Add `visual_review_node` that:
  - Polls the GitHub PR comments (via PyGithub) for a URL matching the preview host domain
  - Times out after 5 minutes with a clear message if no preview URL is found
  - Prints: _"🎨 Preview ready: [URL] — open it and approve the layout, or describe what to change"_
- [ ] Wire routing: if human describes changes → update state with `HUMAN_VISUAL_FEEDBACK` → re-run `fe_executor_node` → re-open PR from same branch → re-check preview
- [ ] If approved → proceed to `END`.
- [ ] Add `visual_preview_url` to the end-of-run summary printed in `main.py`.

### Acceptance Criteria

- After the FE PR is opened, the workflow waits for the CI/CD pipeline to post a preview URL.
- The human receives the URL in the terminal and can approve or request visual changes.
- Visual change requests loop back through the FE executor and trigger a new preview deployment automatically.
- The run does not complete until the human gives visual approval.
- No Vercel/Netlify CLI is run from Python — the pipeline handles all deployments.

---

## Summary Roadmap

| Phase | Focus                     | Effort                       | Unlocks                                  |
| ----- | ------------------------- | ---------------------------- | ---------------------------------------- |
| **1** | Planner approval gate     | Low — ~50 lines              | Human control before any code is written |
| **2** | Real Git + GitHub PRs     | Medium — git + PyGithub      | Real code review workflow                |
| **3** | PR comment feedback loop  | High — webhook + serverless  | Fully closed SDLC loop                   |
| **4** | Production hardening      | High — infra + observability | Enterprise-ready deployment              |
| **5** | Loop breaker / escalation | Low — routing + counter      | No more runaway token burn               |
| **6** | DevOps / infra gate       | Medium — approval node       | Zero unreviewed cloud changes            |
| **7** | Visual UI/UX check        | Medium — preview deployment  | Human eyes on every UI change            |

### Implementation Order (recommended)

**Day 1 (this week):** Phase 1 — highest safety value, lowest cost.
**Day 2:** Phase 5 — pair with Phase 1, protects against QA loops from the start.
**Week 2:** Phase 2 + 3 — real git workflow.
**Week 3:** Phase 6 — required before any cloud infrastructure is touched.
**Week 4:** Phase 7 — required before any real users see the UI.
**Ongoing:** Phase 4 — production hardening is continuous, not a single milestone.

When all 7 phases are complete, the two foundational gates (Strategy + Quality) are reinforced by five safety valves, covering 100% of the risk vectors in an autonomous SDLC.
