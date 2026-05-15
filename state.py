from typing import TypedDict


class SDLCState(TypedDict):
    user_request: str
    requirements: str   # Phase 1: PRD + Jira ticket summaries (what to build)
    prd: str
    architect_plan: str  # Phase 2: interfaces, API contracts, data models — NO code
    fe_output: str
    be_output: str
    test_output: str
    qa_report: str
    infra_output: str
    pr_urls: list          # Phase 2 — PR URLs opened by executors
    # Phase 6 (HITL loop breaker)
    attempt_count: int
    human_escalation: str
    # Phase 7 (visual preview) — not yet active
    # visual_preview_url: str
