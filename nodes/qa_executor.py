import re

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from resilience import run_with_retry
from state import SDLCState
from tools import list_directory, read_file, write_file, search_company_knowledge_base


def _qa_failed(report: str) -> bool:
    text = (report or "").upper()
    if re.search(r"\bFAIL(?:ED|URE)?\b", text):
        return True
    if re.search(r"\bPASS(?:ED)?\b", text):
        return False
    # Fail-safe default: uncertain verdicts are treated as failures.
    return True


def _load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def qa_executor_node(state: SDLCState) -> SDLCState:
    print("\n🔍 [QA Executor] Reviewing code against company standards...")

    if is_stub_mode():
        msg = (
            f"Skipped in stub mode (provider={get_provider_name()}). "
            "No QA review generation executed."
        )
        print(f"   ↳ [QA Executor] {msg}")
        return {"qa_report": msg, "attempt_count": 0}

    prompt = f"""
    {_load_prompt("prompts/qa_executor.md")}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    FE WORKSPACE: {FE_REPO_PATH}
    BE WORKSPACE: {BE_REPO_PATH}
    TODAY'S DATE: {CURRENT_DATE} — use this date in any generated file headers, comments, or metadata.

    Review all generated source and test files. Write the QA report to '{FE_REPO_PATH}/qa_report.md'.
    """

    try:
        llm = get_llm(temperature=0.1)
        agent = create_agent(
            llm, tools=[list_directory, read_file, write_file, search_company_knowledge_base])
        result = run_with_retry(
            "qa_agent_invoke",
            lambda: agent.invoke({"messages": [HumanMessage(content=prompt)]}),
        )
        qa_report = result["messages"][-1].content
    except Exception as e:
        qa_report = f"QA agent failed: {str(e)}"
        print(f"   ❌ [QA Executor] Error: {e}")

    failed = _qa_failed(qa_report)
    current_attempts = int(state.get("attempt_count", 0))
    next_attempts = current_attempts + 1 if failed else 0

    if failed:
        print(f"   ⚠️ [QA Executor] Verdict=FAIL (attempt {next_attempts})")
    else:
        print("   ✅ [QA Executor] Verdict=PASS")

    return {"qa_report": qa_report, "attempt_count": next_attempts}
