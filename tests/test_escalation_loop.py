"""Focused integration test for the QA escalation loop-breaker.

The test uses the real LangGraph workflow, but monkeypatches node callables to
keep execution deterministic and fast:
- QA fails three times and triggers the human escalation pause.
- Human feedback is injected on resume.
- The next execution passes QA and completes.
"""

from __future__ import annotations

import importlib


def test_qa_escalation_pause_and_resume(monkeypatch, tmp_path):
    """Repeated QA failures should pause at escalation and resume with feedback."""
    checkpoint_path = tmp_path / "qa-escalation.db"
    monkeypatch.setenv("CHECKPOINT_DB_PATH", str(checkpoint_path))

    import config as cfg
    import nodes as nodes_pkg
    import graph as graph_module

    importlib.reload(cfg)

    def requirements_node(state):
        return {"requirements": "requirements ok", "prd": "prd ok"}

    def architect_node(state):
        return {"architect_plan": "plan ok"}

    def fe_executor_node(state):
        return {"fe_output": "fe ok"}

    def be_executor_node(state):
        feedback = (state.get("human_escalation") or "").strip()
        if feedback:
            return {"be_output": f"be fixed with feedback: {feedback}"}
        return {"be_output": "be attempt"}

    def test_executor_node(state):
        return {"test_output": "tests ok"}

    def qa_executor_node(state):
        feedback = (state.get("human_escalation") or "").strip()
        if feedback:
            return {"qa_report": "PASS after human escalation", "attempt_count": 0}

        attempts = int(state.get("attempt_count", 0)) + 1
        return {
            "qa_report": f"FAIL attempt {attempts}",
            "attempt_count": attempts,
        }

    def infra_executor_node(state):
        return {"infra_output": "infra ok"}

    monkeypatch.setattr(nodes_pkg, "requirements_node", requirements_node)
    monkeypatch.setattr(nodes_pkg, "architect_node", architect_node)
    monkeypatch.setattr(nodes_pkg, "fe_executor_node", fe_executor_node)
    monkeypatch.setattr(nodes_pkg, "be_executor_node", be_executor_node)
    monkeypatch.setattr(nodes_pkg, "test_executor_node", test_executor_node)
    monkeypatch.setattr(nodes_pkg, "qa_executor_node", qa_executor_node)
    monkeypatch.setattr(nodes_pkg, "infra_executor_node", infra_executor_node)

    # Reload the graph so it picks up the monkeypatched node bindings and temp DB.
    graph_module = importlib.reload(graph_module)
    app = graph_module.app

    thread_id = "qa-escalation-loop-test"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "user_request": "demo feature",
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

    # First run should stop at Gate 1, before any executor runs.
    list(app.stream(initial_state, config))

    gate1 = app.get_state(config)
    assert "fe_executor" in list(gate1.next or [])

    # Resume past Gate 1 and run until the workflow pauses at escalation.
    list(app.stream(None, config))

    paused = app.get_state(config)
    assert "human_escalation" in list(paused.next or [])
    assert paused.values["qa_report"] == "FAIL attempt 3"
    assert paused.values["attempt_count"] == 3

    # Resume with human guidance and verify the next pass completes.
    app.update_state(
        config,
        {"human_escalation": "Use simpler checks and fix the failing QA branch."},
    )
    list(app.stream(None, config))

    final_state = app.get_state(config)
    assert not list(final_state.next or [])
    assert final_state.values["qa_report"] == "PASS after human escalation"
    assert final_state.values["attempt_count"] == 0
    assert "Use simpler checks" in final_state.values["be_output"]
