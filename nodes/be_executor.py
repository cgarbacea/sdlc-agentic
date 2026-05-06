from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import BE_REPO_PATH, CURRENT_DATE
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


# Keywords that indicate a task has no backend work
_FE_ONLY_SIGNALS = (
    "no backend",
    "no backend changes",
    "backend changes required\n**none",
    "backend changes required\nnone",
    "pure frontend",
    "frontend-only",
    "frontend only",
    "no be changes",
    "backend: none",
)


def be_executor_node(state: SDLCState) -> SDLCState:
    plan_lower = state["architect_plan"].lower()
    if any(signal in plan_lower for signal in _FE_ONLY_SIGNALS):
        print(
            "\n⏭️  [BE Executor] Skipping — plan indicates no backend work required.")
        return {"be_output": "Skipped — frontend-only task."}

    print("\n⚙️ [BE Executor] Navigating to Backend Monorepo...")

    prompt = f"""
    {_load_prompt("prompts/be_executor.md")}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    WORKSPACE PATH: {BE_REPO_PATH}
    TODAY'S DATE: {CURRENT_DATE} — use this date in any generated file headers, comments, or metadata.

    Read the ARCHITECT PLAN carefully. Create exactly the files and folder structure it describes.
    Do not create any files not mentioned in the plan.

    After writing all files, use git_commit_to_branch to commit your work to a branch named
    after the feature (e.g. feat/be-<short-slug>). Then use create_github_pr to open a PR
    from that branch to main. The repo_name should be the folder name of your workspace.
    """

    try:
        result = _agent.invoke({"messages": [HumanMessage(content=prompt)]})
        be_output = result["messages"][-1].content
    except Exception as e:
        be_output = f"BE agent failed: {str(e)}"
        print(f"   ❌ [BE Executor] Error: {e}")

    return {"be_output": be_output}
