from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import FE_REPO_PATH, CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from state import SDLCState
from tools import list_directory, read_file, write_file, search_company_knowledge_base
from tools import git_commit_to_branch, create_github_pr


def _load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fe_executor_node(state: SDLCState) -> SDLCState:
    print("\n⚙️ [FE Executor] Navigating to Frontend Monorepo...")

    if is_stub_mode():
        msg = (
            f"Skipped in stub mode (provider={get_provider_name()}). "
            "No code generation executed."
        )
        print(f"   ↳ [FE Executor] {msg}")
        return {"fe_output": msg}

    prompt = f"""
    {_load_prompt("prompts/fe_executor.md")}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    WORKSPACE PATH: {FE_REPO_PATH}
    TODAY'S DATE: {CURRENT_DATE} — use this date in any generated file headers, comments, or metadata.

    Read the ARCHITECT PLAN carefully. Create exactly the files and folder structure it describes.
    Do not create any files not mentioned in the plan.

    After writing all files, use git_commit_to_branch to commit your work to a branch named
    after the feature (e.g. feat/fe-<short-slug>). Then use create_github_pr to open a PR
    from that branch to main. The repo_name should be the folder name of your workspace.
    """

    try:
        llm = get_llm(temperature=0.1)
        agent = create_agent(
            llm, tools=[
                list_directory, read_file, write_file, search_company_knowledge_base,
                git_commit_to_branch, create_github_pr,
            ])
        result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
        fe_output = result["messages"][-1].content
    except Exception as e:
        fe_output = f"FE agent failed: {str(e)}"
        print(f"   ❌ [FE Executor] Error: {e}")

    return {"fe_output": fe_output}
