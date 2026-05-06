from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import FE_REPO_PATH, CURRENT_DATE
from state import SDLCState
from tools import list_directory, read_file, write_file, search_company_knowledge_base
from tools import git_commit_to_branch, create_github_pr

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.1)
_agent = create_agent(
    llm, tools=[
        list_directory, read_file, write_file, search_company_knowledge_base,
        git_commit_to_branch, create_github_pr,
    ])


def _load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fe_executor_node(state: SDLCState) -> SDLCState:
    print("\n⚙️ [FE Executor] Navigating to Frontend Monorepo...")

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
        result = _agent.invoke({"messages": [HumanMessage(content=prompt)]})
        fe_output = result["messages"][-1].content
    except Exception as e:
        fe_output = f"FE agent failed: {str(e)}"
        print(f"   ❌ [FE Executor] Error: {e}")

    return {"fe_output": fe_output}
