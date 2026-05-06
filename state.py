from typing import TypedDict


class SDLCState(TypedDict):
    user_request: str
    prd: str
    architect_plan: str
    fe_output: str
    be_output: str
    test_output: str
    qa_report: str
    infra_output: str
    pr_urls: list          # Phase 2 — PR URLs opened by executors
    # Phase 5 (HITL loop breaker) — not yet active
    # attempt_count: int
    # human_escalation: str
    # Phase 7 (visual preview) — not yet active
    # visual_preview_url: str
