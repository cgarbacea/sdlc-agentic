from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from state import SDLCState
from tools import list_directory, read_file, write_file, search_company_knowledge_base

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.1)
_agent = create_agent(
    llm, tools=[list_directory, read_file, write_file, search_company_knowledge_base])


def _load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def infra_executor_node(state: SDLCState) -> SDLCState:
    print("\n🐳 [Infra Executor] Writing Dockerfiles and docker-compose...")

    prompt = f"""
    {_load_prompt("prompts/infra_executor.md")}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    FE WORKSPACE: {FE_REPO_PATH}
    BE WORKSPACE: {BE_REPO_PATH}
    TODAY'S DATE: {CURRENT_DATE} — use this date in any generated file headers, comments, or metadata.

    Write a Dockerfile to each repo and a docker-compose.yml to the BE repo root.
    """

    try:
        result = _agent.invoke({"messages": [HumanMessage(content=prompt)]})
        infra_output = result["messages"][-1].content
    except Exception as e:
        infra_output = f"Infra agent failed: {str(e)}"
        print(f"   ❌ [Infra Executor] Error: {e}")

    return {"infra_output": infra_output}
