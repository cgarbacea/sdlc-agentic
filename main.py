import argparse
import logging
import sys

from langchain_core.messages import HumanMessage

from config import FE_REPO_PATH, BE_REPO_PATH
from graph import app
from observability import configure_observability
from llm_factory import (
    get_llm,
    is_stub_mode,
    get_provider_name,
    get_provider_report,
)
from state import SDLCState
from tools.rag import index_plan

configure_observability("sdlc.cli")
log = logging.getLogger(__name__)


def _rewrite_plan_with_corrections(original_plan: str, corrections: str) -> str:
    """
    Ask the LLM to produce a single, clean, rewritten plan that fully
    incorporates the human's corrections. The executor receives this
    unified plan with no contradictions.
    """
    if is_stub_mode():
        print(
            f"\n🔄 [Gate 1] Stub mode rewrite (provider={get_provider_name()}) — appending corrections."
        )
        return (
            f"{original_plan}\n\n"
            "--- Human Corrections ---\n"
            f"{corrections}\n"
        )

    print("\n🔄 [Gate 1] Rewriting plan with your corrections...")
    llm = get_llm(temperature=0.1)
    response = llm.invoke([HumanMessage(content=f"""
You are a Lead Architect. A human reviewer has provided corrections to an architectural plan.
Rewrite the plan as a single, clean document that fully incorporates the corrections.
Do not include any commentary about what changed — just produce the updated plan.

ORIGINAL PLAN:
\"\"\"
{original_plan}
\"\"\"

HUMAN CORRECTIONS:
\"\"\"
{corrections}
\"\"\"

Produce the rewritten plan now:
""")])
    return response.content if isinstance(response.content, str) else original_plan

# ==========================================
# INTERACTIVE RUNNER WITH HITL GATE 1
# ==========================================


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sdlc-agent",
        description="AI-native SDLC pipeline: feature request → PR via LangGraph + Claude.",
    )
    parser.add_argument(
        "--feature",
        type=str,
        default=None,
        help="Feature description (omit for interactive prompt).",
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        default=None,
        help="Resume an existing paused pipeline run by its thread ID.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Auto-approve Gate 1 without prompting (for CI use).",
    )
    parser.add_argument(
        "--provider-check",
        action="store_true",
        help="Print effective LLM provider and required env checks before running.",
    )
    parser.add_argument(
        "--provider-check-only",
        action="store_true",
        help="Print provider/env checks and exit without running the pipeline.",
    )
    return parser.parse_args()


def _print_provider_check() -> None:
    report = get_provider_report()
    print("\n🔎 LLM Provider Check")
    print(f"- Configured provider: {report['configured_provider']}")
    print(f"- Effective provider: {report['effective_provider']}")

    missing_env_vars = report["missing_env_vars"]
    if missing_env_vars:
        print(f"- Missing required env vars: {', '.join(missing_env_vars)}")
    else:
        print("- Missing required env vars: none")

    notes = report["notes"]
    if notes:
        for note in notes:
            print(f"- Note: {note}")


if __name__ == "__main__":
    args = _parse_args()

    if args.provider_check or args.provider_check_only:
        _print_provider_check()
        if args.provider_check_only:
            sys.exit(0)

    print("\n" + "=" * 50)
    print("🤖 Welcome to the Agentic SDLC Workspace")
    print("=" * 50)

    if args.feature:
        user_input = args.feature
        log.info("Feature provided via CLI: %s", user_input)
    else:
        user_input = input(
            "\n👨‍💻 Product Analyst, what feature are we building today?\n> "
        )

    if not user_input.strip():
        log.error("No feature description provided. Exiting.")
        sys.exit(1)

    # Thread ID ties this run to the checkpointer so it can be paused and resumed
    thread_id = args.thread_id or user_input[:40].strip().replace(
        " ", "-").lower()
    config = {"configurable": {"thread_id": thread_id}}
    log.info("Thread ID: %s", thread_id)

    initial_state: SDLCState = {
        "user_request": user_input,
        "requirements": "",
        "prd": "",
        "architect_plan": "",
        "fe_output": "",
        "be_output": "",
        "test_output": "",
        "qa_report": "",
        "infra_output": "",
        "pr_urls": [],
    }

    # ── PHASE 1: Requirements + Architecture (no code) ──────────────────────────
    # requirements_node: PRD + Jira tickets
    # architect_node: API contracts, component names, data models (NO code)
    # Graph pauses automatically at interrupt_before=["fe_executor"] (defined in graph.py)
    log.info("Starting Requirements + Architecture phase")
    print("\n🚀 Starting Requirements + Architecture phase...")
    for output in app.stream(initial_state, config):
        for node_name, _ in output.items():
            log.info("Node completed: %s", node_name)
            print(f"\n✅ [{node_name}] completed.")

    # ── GATE 1: Human reviews the architectural plan ───────────────────────────
    current_state = app.get_state(config).values
    architect_plan = current_state.get("architect_plan", "")

    # ── Iterative review loop — repeat until human types 'yes' ─────────────────
    current_plan = architect_plan
    round_num = 1
    while True:
        print("\n" + "=" * 50)
        print(f"⏸️  GATE 1 — PLAN REVIEW  (round {round_num})")
        print("=" * 50)
        print("\n📋 Architect Plan:\n")
        print(current_plan)
        print("\n" + "=" * 50)

        human_feedback = input(
            "\nApprove this plan? Type 'yes' to proceed, or type your corrections:\n> "
        ).strip()

        if args.non_interactive or human_feedback.lower() == "yes":
            if args.non_interactive:
                log.info("Non-interactive mode — auto-approving plan")
                print("\n✅ [CI] Plan auto-approved (--non-interactive).")
            else:
                print("\n✅ Plan approved.")
            break

        current_plan = _rewrite_plan_with_corrections(
            current_plan, human_feedback)
        app.update_state(config, {"architect_plan": current_plan})
        log.info("Plan rewritten — round %d", round_num)
        print("\n✅ Plan rewritten — review it above before approving.")
        round_num += 1

    # Index the approved plan into the RAG knowledge base so executors
    # (and future runs) can query it like any other company guideline.
    approved_state = app.get_state(config).values
    approved_plan = approved_state.get("architect_plan", "")
    plan_file = index_plan(approved_plan, thread_id)
    print(f"\n📚 [RAG] Approved plan indexed → {plan_file}")

    # Truncate the plan body before handing to executors to avoid memory pressure
    # in the RAG embedding model (segfault risk on very large plans).
    # IMPORTANT: always preserve the human corrections — they are appended after
    # the '--- Human Corrections ---' marker and must reach the executors intact.
    EXECUTOR_PLAN_LIMIT = 2000
    final_state = app.get_state(config).values
    final_plan = final_state.get("architect_plan", "")
    if len(final_plan) > EXECUTOR_PLAN_LIMIT:
        executor_plan = final_plan[:EXECUTOR_PLAN_LIMIT] + \
            "\n...[plan truncated]"
        app.update_state(config, {"architect_plan": executor_plan})
        print(
            f"\n✂️  Plan truncated to {EXECUTOR_PLAN_LIMIT} chars for executor context.")

    # ── PHASE 2: Resume — run all executor nodes ───────────────────────────────
    log.info("Resuming pipeline — handing off to executors")
    print("\n🚀 Resuming — handing off to executors...")
    for output in app.stream(None, config):
        for node_name, _ in output.items():
            log.info("Node completed: %s", node_name)
            print(f"\n✅ [{node_name}] completed.")

    final = app.get_state(config).values
    pr_urls = final.get("pr_urls", [])
    log.info("Pipeline complete. Thread: %s", thread_id)
    print(
        f"\n🎉 Run Complete! Check your {FE_REPO_PATH} and {BE_REPO_PATH} folders!")
    if pr_urls:
        print("\n📎 Pull Requests opened:")
        for url in pr_urls:
            print(f"   {url}")
