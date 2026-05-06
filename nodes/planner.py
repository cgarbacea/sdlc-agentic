from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from state import SDLCState
from tools import create_jira_ticket, create_confluence_page

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.1)


def planner_node(state: SDLCState) -> SDLCState:
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
