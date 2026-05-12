from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from state import SDLCState
from tools import list_directory, read_file, write_file, search_company_knowledge_base


def _load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_executor_node(state: SDLCState) -> SDLCState:
    print("\n🧪 [Test Executor] Writing automated tests...")

    if is_stub_mode():
        msg = (
            f"Skipped in stub mode (provider={get_provider_name()}). "
            "No test generation executed."
        )
        print(f"   ↳ [Test Executor] {msg}")
        return {"test_output": msg}

    prompt = f"""
    {_load_prompt("prompts/test_executor.md")}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    FE WORKSPACE: {FE_REPO_PATH}
    BE WORKSPACE: {BE_REPO_PATH}
    TODAY'S DATE: {CURRENT_DATE} — use this date in any generated file headers, comments, or metadata.

    The FE and BE code has already been written. Read the source files first, then write the tests.
    """

    try:
        llm = get_llm(temperature=0.1)
        agent = create_agent(
            llm, tools=[list_directory, read_file, write_file, search_company_knowledge_base])
        result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
        test_output = result["messages"][-1].content
    except Exception as e:
        test_output = f"Test agent failed: {str(e)}"
        print(f"   ❌ [Test Executor] Error: {e}")

    return {"test_output": test_output}
