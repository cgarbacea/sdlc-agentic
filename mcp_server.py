"""
SDLC Agentic — MCP Server
=========================
Exposes the LangGraph SDLC pipeline as an MCP server so any MCP-compatible
AI client (GitHub Copilot, Claude, Cursor) can trigger it as a native tool.

Transport: stdio (standard input/output JSON-RPC)
Protocol:  Model Context Protocol 1.x (Anthropic)

Register in VS Code ~/.config/Code/User/mcp.json (or global mcp.json):

    {
      "servers": {
        "sdlc-pipeline": {
          "type": "stdio",
          "command": "/absolute/path/to/venv/bin/python",
          "args": ["/absolute/path/to/sdlc-agentic/mcp_server.py"]
        }
      }
    }

Tools exposed:
    - health_check       Return service readiness and runtime metadata
  - start_pipeline     Start a new pipeline run (returns thread_id)
  - get_pipeline_state Read current state of a paused/running thread
  - approve_plan       Approve (or correct) the plan at Gate 1 and resume
    - resolve_escalation Provide human feedback when QA escalation is triggered
  - list_threads       List all known checkpoint threads
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP
from config import (
    LANGSMITH_TRACING_ENABLED,
    LOG_FORMAT,
    LOG_LEVEL,
)
from llm_factory import get_provider_name
from observability import configure_observability
from resilience import run_with_retry

# ── Logging ───────────────────────────────────────────────────────────────────
# MCP servers communicate over stdio; logging MUST go to stderr only.
configure_observability("sdlc.mcp")
log = logging.getLogger("sdlc.mcp")

# ── Lazy pipeline import ──────────────────────────────────────────────────────
# graph.py initialises the SQLite checkpointer and loads the embedding model
# on import — we defer this until the first tool call so the MCP client gets
# a fast response to the initial handshake.
_pipeline_ready = False
_app = None


def _ensure_pipeline() -> Any:
    """Import and return the compiled LangGraph app (idempotent)."""
    global _pipeline_ready, _app
    if not _pipeline_ready:
        log.info("Loading pipeline (first call — this may take a few seconds)...")
        from graph import app  # noqa: PLC0415
        _app = app
        _pipeline_ready = True
        log.info("Pipeline ready.")
    return _app


# ── MCP server ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="sdlc-pipeline",
    instructions=(
        "AI-native SDLC pipeline. Use start_pipeline to kick off a new feature, "
        "then get_pipeline_state to read the generated plan, and approve_plan to "
        "approve or correct it before the executors run."
    ),
)


@mcp.tool()
def health_check() -> dict:
    """Return a lightweight health snapshot for MCP operational checks."""
    return {
        "status": "ok",
        "service": "sdlc-pipeline",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_ready": _pipeline_ready,
        "provider": get_provider_name(),
        "log_level": LOG_LEVEL,
        "log_format": LOG_FORMAT,
        "langsmith_tracing_enabled": LANGSMITH_TRACING_ENABLED,
    }


# ── Tool: start_pipeline ──────────────────────────────────────────────────────
@mcp.tool()
def start_pipeline(feature_description: str) -> dict:
    """
    Start a new SDLC pipeline run for the given feature description.

    Runs the Planner node and pauses at Gate 1 (before any code is written).
    Returns the thread_id — use it with get_pipeline_state and approve_plan.

    Args:
        feature_description: Plain-English description of the feature to build.

    Returns:
        dict with keys: thread_id, status, summary (first 500 chars of plan).
    """
    if not feature_description or not feature_description.strip():
        return {"error": "feature_description must not be empty"}

    app = _ensure_pipeline()
    from state import SDLCState  # noqa: PLC0415

    thread_id = feature_description[:40].strip().replace(" ", "-").lower()
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: SDLCState = {
        "user_request": feature_description,
        "requirements": "",
        "prd": "",
        "architect_plan": "",
        "fe_output": "",
        "be_output": "",
        "test_output": "",
        "qa_report": "",
        "infra_output": "",
        "pr_urls": [],
        "attempt_count": 0,
        "human_escalation": "",
    }

    log.info("Starting pipeline for thread: %s", thread_id)
    nodes_run = []
    for output in app.stream(initial_state, config):
        for node_name in output:
            nodes_run.append(node_name)
            log.info("Node completed: %s", node_name)

    state = app.get_state(config).values
    plan = state.get("architect_plan", "")
    next_nodes = list(app.get_state(config).next or [])

    return {
        "thread_id": thread_id,
        "status": "paused_at_gate1" if "fe_executor" in next_nodes else "running",
        "nodes_completed": nodes_run,
        "plan_preview": plan[:500] + ("..." if len(plan) > 500 else ""),
        "full_plan": plan,
        "message": (
            "Plan generated. Review it and call approve_plan(thread_id, corrections='') "
            "to proceed, or approve_plan(thread_id, corrections='your changes') to revise."
        ),
    }


# ── Tool: get_pipeline_state ──────────────────────────────────────────────────
@mcp.tool()
def get_pipeline_state(thread_id: str) -> dict:
    """
    Get the current state of a pipeline run.

    Use this to read the generated plan while paused at Gate 1, or to check
    outputs after executors have run.

    Args:
        thread_id: The thread ID returned by start_pipeline.

    Returns:
        dict with all state fields: prd, architect_plan, fe_output, qa_report, etc.
    """
    app = _ensure_pipeline()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = app.get_state(config)
    except Exception as exc:
        return {"error": f"Thread not found or state unavailable: {exc}"}

    if snapshot is None or not snapshot.values:
        return {"error": f"No state found for thread_id='{thread_id}'"}

    state = snapshot.values
    next_nodes = list(snapshot.next or [])

    return {
        "thread_id": thread_id,
        "next_nodes": next_nodes,
        "status": (
            "paused_at_gate1"
            if "fe_executor" in next_nodes
            else (
                "paused_at_escalation"
                if "human_escalation" in next_nodes
                else ("complete" if not next_nodes else "running")
            )
        ),
        "prd": state.get("prd", ""),
        "architect_plan": state.get("architect_plan", ""),
        "fe_output": state.get("fe_output", ""),
        "be_output": state.get("be_output", ""),
        "test_output": state.get("test_output", ""),
        "qa_report": state.get("qa_report", ""),
        "infra_output": state.get("infra_output", ""),
        "pr_urls": state.get("pr_urls", []),
    }


# ── Tool: approve_plan ────────────────────────────────────────────────────────
@mcp.tool()
def approve_plan(thread_id: str, corrections: str = "") -> dict:
    """
    Approve the plan at Gate 1 and resume the pipeline.

    If corrections are provided, the plan is rewritten by the LLM to
    incorporate them before the executors run. Pass an empty string to
    approve as-is.

    Args:
        thread_id:   The thread ID returned by start_pipeline.
        corrections: Optional plain-English corrections to apply to the plan.
                     Leave empty to approve the current plan unchanged.

    Returns:
        dict with status and nodes completed after resuming.
    """
    app = _ensure_pipeline()
    config = {"configurable": {"thread_id": thread_id}}

    # Optionally rewrite the plan with corrections
    if corrections and corrections.strip():
        from langchain_anthropic import ChatAnthropic  # noqa: PLC0415
        from langchain_core.messages import HumanMessage  # noqa: PLC0415

        state = app.get_state(config).values
        current_plan = state.get("architect_plan", "")
        if not current_plan:
            return {"error": "No plan found for this thread. Run start_pipeline first."}

        log.info("Rewriting plan with corrections for thread: %s", thread_id)
        llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.1)
        response = run_with_retry(
            "mcp_approve_plan_rewrite",
            lambda: llm.invoke([HumanMessage(content=f"""
You are a Lead Architect. A human reviewer has provided corrections to an architectural plan.
Rewrite the plan as a single, clean document that fully incorporates the corrections.
Do not include any commentary about what changed — just produce the updated plan.

ORIGINAL PLAN:
\"\"\"
{current_plan}
\"\"\"

HUMAN CORRECTIONS:
\"\"\"
{corrections}
\"\"\"

Produce the rewritten plan now:
        """)]),
        )
        revised_plan = response.content if isinstance(
            response.content, str) else current_plan
        app.update_state(config, {"architect_plan": revised_plan})
        log.info("Plan rewritten and state updated.")

    # Resume the graph from Gate 1
    log.info("Resuming pipeline for thread: %s", thread_id)
    nodes_run = []
    for output in app.stream(None, config):
        for node_name in output:
            nodes_run.append(node_name)
            log.info("Node completed: %s", node_name)

    final_state = app.get_state(config).values
    pr_urls = final_state.get("pr_urls", [])
    qa_report = final_state.get("qa_report", "")

    snapshot = app.get_state(config)
    next_nodes = list(snapshot.next or [])
    status = "complete"
    if "human_escalation" in next_nodes:
        status = "paused_at_escalation"

    return {
        "thread_id": thread_id,
        "status": status,
        "nodes_completed": nodes_run,
        "next_nodes": next_nodes,
        "qa_report": qa_report,
        "pr_urls": pr_urls,
        "message": (
            "Pipeline complete. Check configured output paths for generated code."
            if status == "complete"
            else "Pipeline paused at QA escalation. Call resolve_escalation(thread_id, feedback) to continue."
        ),
    }


@mcp.tool()
def resolve_escalation(thread_id: str, feedback: str) -> dict:
    """
    Resume pipeline execution after a QA escalation pause.
    """
    app = _ensure_pipeline()
    config = {"configurable": {"thread_id": thread_id}}

    snapshot = app.get_state(config)
    next_nodes = list(snapshot.next or [])
    if "human_escalation" not in next_nodes:
        return {
            "thread_id": thread_id,
            "status": "not_paused_at_escalation",
            "next_nodes": next_nodes,
            "message": "Thread is not waiting at human escalation.",
        }

    app.update_state(
        config,
        {
            "human_escalation": feedback.strip() or "Fix all failing QA checks from the latest report.",
        },
    )

    nodes_run = []
    for output in app.stream(None, config):
        for node_name in output:
            nodes_run.append(node_name)
            log.info("Node completed: %s", node_name)

    final_snapshot = app.get_state(config)
    final_next_nodes = list(final_snapshot.next or [])
    final_state = final_snapshot.values

    status = "complete" if not final_next_nodes else "running"
    if "human_escalation" in final_next_nodes:
        status = "paused_at_escalation"

    return {
        "thread_id": thread_id,
        "status": status,
        "nodes_completed": nodes_run,
        "next_nodes": final_next_nodes,
        "qa_report": final_state.get("qa_report", ""),
        "pr_urls": final_state.get("pr_urls", []),
    }


# ── Tool: list_threads ────────────────────────────────────────────────────────
@mcp.tool()
def list_threads() -> dict:
    """
    List all pipeline threads stored in the SQLite checkpoint database.

    Useful for resuming a previous run or auditing what has been run.

    Returns:
        dict with a list of thread metadata entries.
    """
    try:
        from config import CHECKPOINT_DB_PATH  # noqa: PLC0415
        import sqlite3

        conn = sqlite3.connect(CHECKPOINT_DB_PATH)
        cursor = conn.execute(
            "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id"
        )
        threads = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"threads": threads, "count": len(threads)}
    except Exception as exc:
        return {"error": f"Could not read checkpoint database: {exc}"}


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting SDLC MCP server (stdio transport)...")
    mcp.run(transport="stdio")
