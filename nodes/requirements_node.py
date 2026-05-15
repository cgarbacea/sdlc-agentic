from langchain_core.messages import HumanMessage

from config import CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from resilience import run_with_retry
from state import SDLCState
from tools import create_jira_ticket, create_confluence_page


def _build_stub_requirements(state: SDLCState) -> SDLCState:
    feature = state["user_request"].strip()
    title = f"PRD - {feature[:80]}"

    prd_content = (
        f"Feature request: {feature}\n\n"
        "This PRD was generated in stub mode because no external LLM provider is configured or available.\n"
        "It captures baseline scope for later refinement in Gate 1."
    )

    create_confluence_page.invoke(
        {
            "title": title,
            "content": prd_content,
            "space_key": "ENG",
        }
    )
    create_jira_ticket.invoke(
        {
            "title": f"[FE] {feature[:70]}",
            "description": f"Implement frontend scope for: {feature}",
            "project_key": "FE",
        }
    )
    create_jira_ticket.invoke(
        {
            "title": f"[BE] {feature[:70]}",
            "description": f"Implement backend scope for: {feature}",
            "project_key": "BE",
        }
    )

    requirements_summary = f"""Feature: {feature}

PRD: PRD generated and saved to Confluence.
Jira tickets created for FE and BE teams.
"""
    return {"requirements": requirements_summary, "prd": "PRD generated and saved to Confluence."}


def requirements_node(state: SDLCState) -> SDLCState:
    """
    Phase 1 — Requirements.

    Produces:
    - Confluence PRD page (via tool)
    - Jira tickets for FE and BE teams (via tool)
    - A plain-text requirements summary stored in state['requirements']

    This node does NOT write any architectural decisions or code.
    That is the architect_node's responsibility.
    """
    print("\n🧠 [Requirements] Analyzing request and creating Jira tickets...")

    if is_stub_mode():
        print(
            f"   ↳ [Requirements] Stub mode active (provider={get_provider_name()}).")
        return _build_stub_requirements(state)

    llm = get_llm(temperature=0.1)
    requirements_llm = llm.bind_tools(
        [create_jira_ticket, create_confluence_page])

    try:
        response = requirements_llm.invoke([HumanMessage(content=f"""
You are the Product Analyst.
User request:
\"\"\"
{state['user_request']}
\"\"\"

Today's date is {CURRENT_DATE}.

Your job is ONLY to:
1. Create a Confluence PRD Wiki page summarising the feature requirements.
2. Create 1 Jira ticket for the Frontend team and 1 for the Backend team.

The PRD and tickets should describe WHAT the feature does and WHY it is needed.
Do NOT include implementation details, code, or architectural decisions — those come later.
""")])
    except Exception as exc:
        print(
            f"   ⚠️ [Requirements] LLM call failed ({exc}). Falling back to stub mode.")
        return _build_stub_requirements(state)

    prd = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "create_jira_ticket":
                result = create_jira_ticket.invoke(tool_call["args"])
                print(f"   ↳ Jira result: {result}")
            elif tool_call["name"] == "create_confluence_page":
                result = create_confluence_page.invoke(tool_call["args"])
                prd = "PRD generated and saved to Confluence."
                print(f"   ↳ Confluence result: {result}")

    # Summarise what was created for downstream nodes
    requirements_summary = f"""Feature: {state['user_request']}

PRD: {prd}
Jira tickets created for FE and BE teams.
"""

    return {"requirements": requirements_summary, "prd": prd}
