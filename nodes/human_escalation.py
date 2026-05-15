from state import SDLCState


def human_escalation_node(state: SDLCState) -> SDLCState:
    """
    Phase 6 loop-breaker gate.

    This node runs after the graph is resumed from an interrupt_before pause at
    `human_escalation`. It consumes human feedback from state and resets the
    QA attempt counter before retrying execution.
    """
    feedback = (state.get("human_escalation") or "").strip()
    if not feedback:
        feedback = "Focus on the QA failure details and fix root causes."

    print(
        "\n🆘 [HITL Escalation] Feedback captured. Retrying execution with human guidance...")
    return {
        "human_escalation": feedback,
        # Reset attempts so the next QA retry cycle has room to run.
        "attempt_count": 0,
    }
