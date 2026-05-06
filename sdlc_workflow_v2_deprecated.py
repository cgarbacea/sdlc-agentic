# ──────────────────────────────────────────────────────────────────────────────
# This file is kept for reference only.
# The project has been refactored into:
#
#   config.py          — env vars and path constants
#   state.py           — SDLCState TypedDict
#   tools/             — all @tool functions (jira, confluence, filesystem, git, rag)
#   nodes/             — one file per executor node
#   graph.py           — StateGraph assembly and compile
#   main.py            — interactive runner with HITL Gate 1
#
# Run the workflow with:  python main.py
# ──────────────────────────────────────────────────────────────────────────────
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import runpy
runpy.run_path("main.py", run_name="__main__")


load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set. Add it to your .env file.")

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.1)

FE_REPO_PATH = os.getenv(
    "FE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/fe-repo")
BE_REPO_PATH = os.getenv(
    "BE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/be-repo")
JIRA_PATH = os.getenv(
    "JIRA_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/jira")
CONFLUENCE_PATH = os.getenv(
    "CONFLUENCE_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/confluence")
ALLOWED_ROOTS = (
    os.path.realpath(FE_REPO_PATH),
    os.path.realpath(BE_REPO_PATH),
)

# Load the local RAG vector database (built by build_knowledge_base.py)
_rag_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./rag_db",
                   embedding_function=_rag_embeddings)

# ==========================================
# 1. DEFINE THE TOOLS (The Agents' "Hands")
# ==========================================


@tool
def create_confluence_page(title: str, content: str, space_key: str) -> str:
    """Use this tool to create or update a Wiki page in Confluence for the PRD."""
    # In reality: requests.post("https://domain.atlassian.net/wiki/rest/api/content", ...)
    print(
        f"📝[CONFLUENCE API CALLED] Published PRD Wiki Page: '{title}' in Space: {space_key}")

    os.makedirs(CONFLUENCE_PATH, exist_ok=True)
    filename = f"{title.replace(' ', '_')}_PRD.md"
    with open(os.path.join(CONFLUENCE_PATH, filename), "w") as f:
        f.write(f"# {title}\n\n**Space:** {space_key}\n\n{content}\n")
    print(
        f"📄 [CONFLUENCE FILE] Saved to {os.path.join(CONFLUENCE_PATH, filename)}")

    return f"Confluence page '{title}' created successfully."


@tool
def create_jira_ticket(title: str, description: str, project_key: str) -> str:
    """Use this tool to create a Jira ticket for the engineering team."""
    # In reality, you would use requests.post("https://your-domain.atlassian.net/rest/api/3/issue", auth=...)
    print(f"🎫 [JIRA API CALLED] Created ticket: [{project_key}] {title}")

    os.makedirs(JIRA_PATH, exist_ok=True)
    filename = f"{project_key}_{title.replace(' ', '_')}.md"
    with open(os.path.join(JIRA_PATH, filename), "w") as f:
        f.write(f"# [{project_key}] {title}\n\n{description}\n")
    print(f"📄 [JIRA FILE] Saved to {os.path.join(JIRA_PATH, filename)}")

    return f"Ticket '{title}' created successfully in project {project_key}."


@tool
def list_directory(directory_path: str) -> str:
    """Lists all files and folders in a given directory."""
    try:
        files = os.listdir(directory_path)
        return f"Contents of {directory_path}: {', '.join(files)}"
    except Exception as e:
        return f"Error reading directory: {str(e)}"


@tool
def read_file(file_path: str) -> str:
    """Reads the contents of a specific file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Writes new code or updates to a specific file."""
    resolved = os.path.realpath(file_path)
    if not any(resolved.startswith(root) for root in ALLOWED_ROOTS):
        return f"Error: path '{file_path}' is outside the allowed workspace. Write only to FE or BE repo folders."
    try:
        dir_name = os.path.dirname(resolved)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(resolved, 'w') as f:
            f.write(content)
        print(f"💾 [FILE SYSTEM] Wrote to {resolved}")
        return f"Successfully wrote to {resolved}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def git_commit_to_branch(repo_path: str, branch_name: str, commit_message: str) -> str:
    """
    Creates a new branch, stages all changed files, and commits them.
    Use this AFTER writing your code to save your work.
    """
    if not any(os.path.realpath(repo_path).startswith(root) for root in ALLOWED_ROOTS):
        return f"Git error: repo_path '{repo_path}' is outside the allowed workspace."

    print(f"\n🌱 [GIT] Creating branch '{branch_name}' in {repo_path}...")
    try:
        # 1. Create and checkout branch (-B resets it if it already exists)
        subprocess.run(
            ["git", "checkout", "-B", branch_name],
            cwd=repo_path, check=True, capture_output=True, text=True
        )
        # 2. Stage all changes
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path, check=True, capture_output=True, text=True
        )
        # 3. Commit the changes
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_path, check=True, capture_output=True, text=True
        )
        return f"Success: Committed to branch '{branch_name}' with message: '{commit_message}'"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout
        return f"Git error: {error_msg}"


@tool
def create_github_pr(repo_name: str, branch_name: str, title: str, pr_body: str) -> str:
    """
    Creates a Pull Request on GitHub. Use this AFTER committing your code.
    """
    # In a real app, you would use the PyGithub library here:
    # from github import Github
    # g = Github(os.getenv("GITHUB_TOKEN"))
    # repo = g.get_repo(repo_name)
    # repo.create_pull(title=title, body=pr_body, head=branch_name, base="main")

    print(f"\n🚀 [GITHUB API] Pull Request Created!")
    print(f"   Repo: {repo_name} | Branch: {branch_name}")
    print(f"   Title: {title}")
    return f"GitHub Pull Request '{title}' created successfully. Waiting for human review."


# ==========================================
# 2. STATE AND NODES
# ==========================================

class SDLCState(TypedDict):
    user_request: str
    prd: str
    architect_plan: str
    fe_output: str
    be_output: str
    test_output: str
    qa_report: str
    infra_output: str


def load_prompt(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


@tool
def search_company_knowledge_base(query: str) -> str:
    """
    Search the company Knowledge Base, Wiki, and Architecture guidelines.
    Use this tool whenever you need to know how the company implements specific features,
    coding patterns, or UI/UX rules.
    """
    print(f"\n🔍 [RAG SEARCH] Agent is looking up: '{query}'")
    results = vector_db.similarity_search(query, k=3)
    if not results:
        return "No relevant guidelines found."
    compiled_knowledge = "Found the following company guidelines:\n\n"
    for doc in results:
        source = doc.metadata.get("source", "Unknown")
        compiled_knowledge += f"--- Source: {source} ---\n{doc.page_content}\n\n"
    return compiled_knowledge


fs_tools = [list_directory, read_file,
            write_file, search_company_knowledge_base]
# git_tools = [git_commit_to_branch, create_github_pr]  # TODO: enable once git repos are initialised

fe_agent = create_agent(llm, tools=fs_tools)      # + git_tools when ready
be_agent = create_agent(llm, tools=fs_tools)      # + git_tools when ready
test_agent = create_agent(llm, tools=fs_tools)
qa_agent = create_agent(llm, tools=fs_tools)
infra_agent = create_agent(llm, tools=fs_tools)


def planner_node(state: SDLCState) -> SDLCState:
    print("\n🧠 [Planner] Analyzing request and creating Jira tickets...")

    planner_llm = llm.bind_tools([create_jira_ticket, create_confluence_page])

    prompt = f"""
    You are the Lead Architect.
    User request:
    \"\"\"
    {state['user_request']}
    \"\"\"

    1. Create a Confluence PRD Wiki page summarising the feature using your tools.
    2. Create 1 Jira ticket for the Frontend team and 1 for the Backend team using your tools.
    3. Write a brief architectural plan explaining how the FE (path: {FE_REPO_PATH}) and BE (path: {BE_REPO_PATH}) should communicate.
    """

    response = planner_llm.invoke([HumanMessage(content=prompt)])

    prd = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call['name'] == 'create_jira_ticket':
                result = create_jira_ticket.invoke(tool_call['args'])
                print(f"   ↳ Jira result: {result}")
            elif tool_call['name'] == 'create_confluence_page':
                result = create_confluence_page.invoke(tool_call['args'])
                prd = "PRD generated and saved to Confluence."
                print(f"   ↳ Confluence result: {result}")

    # Dedicated second call to generate the architectural plan as plain text.
    # The first call is consumed by tool calls; this guarantees a full, readable plan.
    print("\n🧠 [Planner] Writing architectural plan...")
    plan_response = llm.invoke([HumanMessage(content=f"""
    You are the Lead Architect.
    User request:
    \"\"\"
    {state['user_request']}
    \"\"\"

    Write a detailed architectural plan explaining:
    - What the Frontend needs to build (component names, form fields, validation, API call)
    - What the Backend needs to build (endpoint path, request/response models, auth logic)
    - How FE (path: {FE_REPO_PATH}) and BE (path: {BE_REPO_PATH}) communicate (request format, response format, token handling)

    Write in clear sections with headings. Be specific and actionable.
    """)])

    architect_plan = plan_response.content if isinstance(
        plan_response.content, str) else ""

    return {"architect_plan": architect_plan, "prd": prd}


def fe_executor_node(state: SDLCState) -> SDLCState:
    print("\n⚙️ [FE Executor] Navigating to Frontend Monorepo...")

    base_prompt = load_prompt("prompts/fe_executor.md")

    prompt = f"""
    {base_prompt}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    WORKSPACE PATH: {FE_REPO_PATH}

    Use your tools to write a new file called 'App.tsx' with the required UI.
    """

    try:
        result = fe_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        fe_output = result["messages"][-1].content
    except Exception as e:
        fe_output = f"FE agent failed: {str(e)}"
        print(f"   ❌ [FE Executor] Error: {e}")

    return {"fe_output": fe_output}


def be_executor_node(state: SDLCState) -> SDLCState:
    print("\n⚙️ [BE Executor] Navigating to Backend Monorepo...")

    base_prompt = load_prompt("prompts/be_executor.md")

    prompt = f"""
    {base_prompt}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    WORKSPACE PATH: {BE_REPO_PATH}

    Use your tools to write a new file called 'main.py' with the required API endpoints.
    """

    try:
        result = be_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        be_output = result["messages"][-1].content
    except Exception as e:
        be_output = f"BE agent failed: {str(e)}"
        print(f"   ❌ [BE Executor] Error: {e}")

    return {"be_output": be_output}


def test_executor_node(state: SDLCState) -> SDLCState:
    print("\n🧪 [Test Executor] Writing automated tests...")

    base_prompt = load_prompt("prompts/test_executor.md")

    prompt = f"""
    {base_prompt}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    FE WORKSPACE: {FE_REPO_PATH}
    BE WORKSPACE: {BE_REPO_PATH}

    The FE and BE code has already been written. Read the source files first, then write the tests.
    """

    try:
        result = test_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]})
        test_output = result["messages"][-1].content
    except Exception as e:
        test_output = f"Test agent failed: {str(e)}"
        print(f"   ❌ [Test Executor] Error: {e}")

    return {"test_output": test_output}


def qa_executor_node(state: SDLCState) -> SDLCState:
    print("\n🔍 [QA Executor] Reviewing code against company standards...")

    base_prompt = load_prompt("prompts/qa_executor.md")

    prompt = f"""
    {base_prompt}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    FE WORKSPACE: {FE_REPO_PATH}
    BE WORKSPACE: {BE_REPO_PATH}

    Review all generated source and test files. Write the QA report to '{FE_REPO_PATH}/qa_report.md'.
    """

    try:
        result = qa_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        qa_report = result["messages"][-1].content
    except Exception as e:
        qa_report = f"QA agent failed: {str(e)}"
        print(f"   ❌ [QA Executor] Error: {e}")

    return {"qa_report": qa_report}


def infra_executor_node(state: SDLCState) -> SDLCState:
    print("\n🐳 [Infra Executor] Writing Dockerfiles and docker-compose...")

    base_prompt = load_prompt("prompts/infra_executor.md")

    prompt = f"""
    {base_prompt}

    ARCHITECT PLAN:
    \"\"\"
    {state['architect_plan']}
    \"\"\"
    FE WORKSPACE: {FE_REPO_PATH}
    BE WORKSPACE: {BE_REPO_PATH}

    Write a Dockerfile to each repo and a docker-compose.yml to the BE repo root.
    """

    try:
        result = infra_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]})
        infra_output = result["messages"][-1].content
    except Exception as e:
        infra_output = f"Infra agent failed: {str(e)}"
        print(f"   ❌ [Infra Executor] Error: {e}")

    return {"infra_output": infra_output}


# ==========================================
# 3. BUILD THE GRAPH
# ==========================================
workflow = StateGraph(SDLCState)

workflow.add_node("planner", planner_node)
workflow.add_node("fe_executor", fe_executor_node)
workflow.add_node("be_executor", be_executor_node)
workflow.add_node("test_executor", test_executor_node)
workflow.add_node("qa_executor", qa_executor_node)
workflow.add_node("infra_executor", infra_executor_node)

# Sequential: Planner → FE → BE → Tests → QA → Infra
workflow.add_edge("planner", "fe_executor")
workflow.add_edge("fe_executor", "be_executor")
workflow.add_edge("be_executor", "test_executor")
workflow.add_edge("test_executor", "qa_executor")
workflow.add_edge("qa_executor", "infra_executor")
workflow.add_edge("infra_executor", END)

workflow.set_entry_point("planner")

# HITL Phase 1: MemorySaver checkpointer + breakpoint before executors start
memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["fe_executor"],
)

# ==========================================
# 4. THE INTERACTIVE RUNNER
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 Welcome to the Agentic SDLC Workspace")
    print("="*50)

    user_input = input(
        "\n👨‍💻 Product Analyst, what feature are we building today?\n> ")

    # Thread ID ties this run's state to the checkpointer so it can be paused/resumed
    thread_id = user_input[:40].strip().replace(" ", "-").lower()
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: SDLCState = {
        "user_request": user_input,
        "prd": "",
        "architect_plan": "",
        "fe_output": "",
        "be_output": "",
        "test_output": "",
        "qa_report": "",
        "infra_output": "",
    }

    # ── PHASE 1: Run Planner only (graph pauses at interrupt_before=["fe_executor"]) ──
    print("\n🚀 Starting Planner phase...")
    for output in app.stream(initial_state, config):
        for node_name, _ in output.items():
            print(f"\n✅ [{node_name}] completed.")

    # ── GATE 1: Human reviews the plan ──
    current_state = app.get_state(config).values
    architect_plan = current_state.get("architect_plan", "")

    print("\n" + "="*50)
    print("⏸️  GATE 1 — PLAN REVIEW")
    print("="*50)
    print("\n📋 Architect Plan:\n")
    print(architect_plan)
    print("\n" + "="*50)

    human_feedback = input(
        "\nApprove this plan? Type 'yes' to proceed, or type your corrections:\n> "
    ).strip()

    if human_feedback.lower() != "yes":
        print("\n✍️  Updating plan with your corrections...")
        amended_plan = (
            architect_plan
            + "\n\n--- Human Corrections ---\n"
            + human_feedback
        )
        app.update_state(config, {"architect_plan": amended_plan})
        print("✅ Plan updated.")
    else:
        print("\n✅ Plan approved.")

    # ── PHASE 2: Resume — run all remaining executor nodes ──
    print("\n🚀 Resuming — handing off to executors...")
    for output in app.stream(None, config):
        for node_name, _ in output.items():
            print(f"\n✅ [{node_name}] completed.")

    print(
        f"\n🎉 Run Complete! Check your {FE_REPO_PATH} and {BE_REPO_PATH} folders!")
