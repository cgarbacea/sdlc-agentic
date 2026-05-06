import os
from typing import TypedDict, List, Dict
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Validate API key at startup
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set. Add it to your .env file.")

# Initialize our LLM (Claude 3.5 Sonnet)
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.2)

# 1. DEFINE THE STATE (The Shared Memory)


class SDLCState(TypedDict):
    user_request: str        # The raw input from the Product Analyst
    prd: str                 # Product Requirements Document
    tasks: List[str]         # Breakdown of tasks (FE, BE, DevOps)
    code_files: Dict[str, str]  # Dictionary of filename -> code content
    qa_status: str           # "pending", "passed", or "failed"
    qa_feedback: str         # Error logs or feedback if QA fails

# --- LAYER 1: PLANNER ---


def product_manager_node(state: SDLCState) -> SDLCState:
    print("🧠 [Planner] Drafting PRD and identifying tasks...")
    prompt = f"""
    You are a Product Manager and Architect.
    User request: \"\"\"
    {state['user_request']}
    \"\"\"
    Output a brief PRD and a list of exactly 3 specific engineering tasks (BE, FE, DevOps).
    Format your response as plain text with two clearly labelled sections:
    PRD: <prd text>
    TASKS:
    1. <task 1>
    2. <task 2>
    3. <task 3>
    """
    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse tasks from the LLM response
    lines = response.content.splitlines()
    tasks = [
        line.lstrip("0123456789. ").strip()
        for line in lines
        if line.strip() and line.strip()[0].isdigit()
    ]
    if not tasks:
        tasks = ["Backend Auth API", "Frontend Login UI", "DevOps Secrets"]

    return {
        "prd": response.content,
        "tasks": tasks,
        "code_files": {}
    }

# --- LAYER 3: EXECUTORS ---


def executor_node(state: SDLCState) -> SDLCState:
    print("⚙️ [Executor] Writing code for tasks based on QA feedback (if any)...")

    feedback_context = f"Previous QA Feedback: {state.get('qa_feedback', 'None')}"
    prompt = f"""
    You are a Full-Stack Engineering Agent.
    PRD: {state['prd']}
    Tasks: {state['tasks']}
    {feedback_context}

    Write the code to solve this. Return ONLY a series of file blocks in this exact format:
    ===filename.py===
    <code here>
    ===end===
    """
    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse code blocks from LLM response
    new_code: Dict[str, str] = {}
    current_file = None
    current_lines: List[str] = []
    for line in response.content.splitlines():
        if line.startswith("===") and line.endswith("===") and not line == "===end===":
            if current_file:
                new_code[current_file] = "\n".join(current_lines).strip()
            current_file = line.strip("=").strip()
            current_lines = []
        elif line == "===end===" and current_file:
            new_code[current_file] = "\n".join(current_lines).strip()
            current_file = None
            current_lines = []
        elif current_file:
            current_lines.append(line)

    if not new_code:
        # Fallback if LLM didn't follow the format
        new_code = {"main.py": response.content}

    return {"code_files": new_code, "qa_status": "pending"}

# --- LAYER 2: ORCHESTRATOR / QA ---


def qa_orchestrator_node(state: SDLCState) -> SDLCState:
    print("🧐 [Orchestrator QA] Reviewing code...")

    code_str = str(state['code_files'])
    prompt = f"""
    You are the QA Orchestrator. Review this code: {code_str}.
    Does it satisfy the PRD? Reply ONLY with "PASSED" or "FAILED: [reason]".
    """
    response = llm.invoke([HumanMessage(content=prompt)])

    if "PASSED" in response.content.upper():
        print("✅ QA Passed!")
        return {"qa_status": "passed", "qa_feedback": ""}
    else:
        print("❌ QA Failed, sending back to Executor.")
        return {"qa_status": "failed", "qa_feedback": response.content}


def qa_router(state: SDLCState) -> str:
    """Routes the graph based on the QA status."""
    if state["qa_status"] == "passed":
        return "end"
    return "execute"


# Initialize the Graph with our State definition
workflow = StateGraph(SDLCState)

# Add our Nodes (Agents)
workflow.add_node("planner", product_manager_node)
workflow.add_node("executor", executor_node)
workflow.add_node("qa_orchestrator", qa_orchestrator_node)

# Define the standard Flow (Edges)
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "qa_orchestrator")

# Define the Conditional Flow (The loop)
workflow.add_conditional_edges(
    "qa_orchestrator",  # The node making the decision
    qa_router,         # The routing function
    {
        "execute": "executor",  # If router says 'execute', go back to executor
        "end": END             # If router says 'end', finish the graph
    }
)

# Set the entry point
workflow.set_entry_point("planner")

# Compile the graph
app = workflow.compile()

# --- RUNNING THE WORKFLOW ---
if __name__ == "__main__":
    print("🚀 Starting Agentic SDLC Workflow...\n")

    initial_state = {
        "user_request": "Users need to be able to log in with Apple ID, not just Google.",
    }

    # thread_id is required to retrieve state after streaming
    config = {"configurable": {"thread_id": "1"}, "recursion_limit": 10}

    iteration = 0
    for output in app.stream(initial_state, config):
        for node_name, state_update in output.items():
            iteration += 1
            print(f"--- Finished: {node_name} (iteration {iteration}) ---")

    print("\n🎉 Workflow Complete! Final State:")
    final_state = app.get_state(config).values
    print(final_state)
