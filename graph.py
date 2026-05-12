import logging

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from config import CHECKPOINT_DB_PATH
from state import SDLCState
from nodes import (
    requirements_node,
    architect_node,
    fe_executor_node,
    be_executor_node,
    test_executor_node,
    qa_executor_node,
    infra_executor_node,
)

log = logging.getLogger(__name__)

# ── Build the directed graph ──────────────────────────────────────────────────
#
# Phase 1 — Requirements:  requirements → architect
#   requirements_node: PRD + Jira tickets (WHAT to build, WHY)
#   architect_node:    API contracts, component names, data models (NO code)
#
# Gate 1 — Human review of the architectural plan before any code is written
#
# Phase 2 — Execution:  fe_executor → be_executor → test_executor → qa_executor → infra_executor
#   Executors use the architect_plan from state + KB retrieval for implementation patterns
#
# Future: FE and BE can run in parallel using LangGraph's Send() API

workflow = StateGraph(SDLCState)

workflow.add_node("requirements", requirements_node)
workflow.add_node("architect", architect_node)
workflow.add_node("fe_executor", fe_executor_node)
workflow.add_node("be_executor", be_executor_node)
workflow.add_node("test_executor", test_executor_node)
workflow.add_node("qa_executor", qa_executor_node)
workflow.add_node("infra_executor", infra_executor_node)

workflow.add_edge("requirements", "architect")
workflow.add_edge("architect", "fe_executor")
workflow.add_edge("fe_executor", "be_executor")
workflow.add_edge("be_executor", "test_executor")
workflow.add_edge("test_executor", "qa_executor")
workflow.add_edge("qa_executor", "infra_executor")
workflow.add_edge("infra_executor", END)

workflow.set_entry_point("requirements")

# ── Compile with SQLite checkpointer + Gate 1 breakpoint ─────────────────────
# SqliteSaver persists state to disk so paused runs survive process restarts.
# The DB file lives at CHECKPOINT_DB_PATH (default: .checkpoints/sdlc.db).
# To resume a paused run: python main.py --thread-id <thread-id>
#
# Gate 1 is placed after architect (plan review) and before fe_executor (first executor).
# The human sees only the architectural plan — no code — and approves or corrects it.
log.info("Initialising SQLite checkpointer at %s", CHECKPOINT_DB_PATH)
_sqlite_ctx = SqliteSaver.from_conn_string(CHECKPOINT_DB_PATH)
_checkpointer = _sqlite_ctx.__enter__()

app = workflow.compile(
    checkpointer=_checkpointer,
    # Gate 1: pause after architect, before any executor
    interrupt_before=["fe_executor"],
)
