from langchain_core.messages import HumanMessage

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from state import SDLCState
from tools import create_jira_ticket, create_confluence_page


def planner_node(state: SDLCState) -> SDLCState:
    if is_stub_mode():
        feature = state["user_request"].strip()
        print(
            f"\n🧠 [Planner] Stub mode active (provider={get_provider_name()}).")
        create_confluence_page.invoke(
            {
                "title": f"PRD - {feature[:80]}",
                "content": f"Feature request: {feature}",
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
        return {
            "architect_plan": (
                "Stub planner output. Replace with requirements_node + architect_node flow.\n\n"
                f"Feature: {feature}"
            ),
            "prd": "PRD generated and saved to Confluence.",
        }

    llm = get_llm(temperature=0.1)
    print("\n🧠 [Planner] Analyzing request and creating Jira tickets...")

    planner_llm = llm.bind_tools([create_jira_ticket, create_confluence_page])

    response = planner_llm.invoke([HumanMessage(content=f"""
    You are the Lead Architect.
    User request:
    \"\"\"
    {state['user_request']}
    \"\"\"

    Today's date is {CURRENT_DATE}.

    1. Create a Confluence PRD Wiki page summarising the feature using your tools.
    2. Create 1 Jira ticket for the Frontend team and 1 for the Backend team using your tools.
    3. Write a brief architectural plan explaining how the FE (path: {FE_REPO_PATH}) and BE (path: {BE_REPO_PATH}) should communicate.
    """)])

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

    # Dedicated second call — the first is consumed by tool calls and may return
    # no text. This guarantees a full, readable architectural plan for Gate 1 review.
    print("\n🧠 [Planner] Writing architectural plan...")
    plan_response = llm.invoke([HumanMessage(content=f"""
    You are the Lead Architect.
    User request:
    \"\"\"
    {state['user_request']}
    \"\"\"

    Today's date is {CURRENT_DATE}. Use this in any document headers or metadata you generate.

    Write a detailed architectural plan explaining:
    - What the Frontend needs to build (component names, form fields, validation, API call)
    - What the Backend needs to build (endpoint path, request/response models, auth logic)
    - How FE (path: {FE_REPO_PATH}) and BE (path: {BE_REPO_PATH}) communicate (request format, response format, token handling)

    Write in clear sections with headings. Be specific and actionable.
    """)])

    architect_plan = plan_response.content if isinstance(
        plan_response.content, str) else ""

    return {"architect_plan": architect_plan, "prd": prd}
