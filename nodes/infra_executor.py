from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from state import SDLCState
from tools import list_directory, read_file, write_file, search_company_knowledge_base


def _load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def infra_executor_node(state: SDLCState) -> SDLCState:
    print("\n🐳 [Infra Executor] Writing Dockerfiles and docker-compose...")

    if is_stub_mode():
        msg = (
            f"Skipped in stub mode (provider={get_provider_name()}). "
            "No infra file generation executed."
        )
        print(f"   ↳ [Infra Executor] {msg}")
        return {"infra_output": msg}

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
        llm = get_llm(temperature=0.1)
        agent = create_agent(
            llm, tools=[list_directory, read_file, write_file, search_company_knowledge_base])
        result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
        infra_output = result["messages"][-1].content
    except Exception as e:
        infra_output = f"Infra agent failed: {str(e)}"
        print(f"   ❌ [Infra Executor] Error: {e}")

    return {"infra_output": infra_output}
