from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import SDLCState
from nodes import (
    planner_node,
    fe_executor_node,
    be_executor_node,
    test_executor_node,
    qa_executor_node,
    infra_executor_node,
)

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

# ── Compile with HITL Phase 1: checkpointer + Gate 1 breakpoint ──────────────
memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["fe_executor"],  # Gate 1: pause for human plan review
)
