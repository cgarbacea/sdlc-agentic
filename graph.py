import logging

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from config import CHECKPOINT_DB_PATH
from state import SDLCState
from nodes import (
    planner_node,
    fe_executor_node,
    be_executor_node,
    test_executor_node,
    qa_executor_node,
    infra_executor_node,
)

log = logging.getLogger(__name__)

# ── Build the directed graph ──────────────────────────────────────────────────
workflow = StateGraph(SDLCState)

workflow.add_node("planner", planner_node)
workflow.add_node("fe_executor", fe_executor_node)
workflow.add_node("be_executor", be_executor_node)
workflow.add_node("test_executor", test_executor_node)
workflow.add_node("qa_executor", qa_executor_node)
workflow.add_node("infra_executor", infra_executor_node)

# Sequential edges: Planner → FE → BE → Tests → QA → Infra → END
# Future: FE and BE can run in parallel using LangGraph's Send() API
workflow.add_edge("planner", "fe_executor")
workflow.add_edge("fe_executor", "be_executor")
workflow.add_edge("be_executor", "test_executor")
workflow.add_edge("test_executor", "qa_executor")
workflow.add_edge("qa_executor", "infra_executor")
workflow.add_edge("infra_executor", END)

workflow.set_entry_point("planner")

# ── Compile with SQLite checkpointer + Gate 1 breakpoint ─────────────────────
# SqliteSaver persists state to disk so paused runs survive process restarts.
# The DB file lives at CHECKPOINT_DB_PATH (default: .checkpoints/sdlc.db).
# To resume a paused run: python main.py --thread-id <thread-id>
#
# SqliteSaver.from_conn_string() is a context manager — we enter it once at
# module load and keep the connection open for the lifetime of the process.
# This is the correct pattern for a long-running server or CLI session.
log.info("Initialising SQLite checkpointer at %s", CHECKPOINT_DB_PATH)
_sqlite_ctx = SqliteSaver.from_conn_string(CHECKPOINT_DB_PATH)
_checkpointer = _sqlite_ctx.__enter__()

app = workflow.compile(
    checkpointer=_checkpointer,
    interrupt_before=["fe_executor"],  # Gate 1: pause for human plan review
)
