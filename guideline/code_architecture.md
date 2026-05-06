# Code Architecture Overview

This document describes the module structure of `sdlc-agentic` after the refactor from a single-file POC into a maintainable, modular codebase.

---

## File Structure

```
sdlc-agentic/
│
├── main.py                     # Entry point — interactive runner + HITL Gate 1 loop
├── graph.py                    # LangGraph StateGraph assembly and compile
├── state.py                    # SDLCState TypedDict (shared memory)
├── config.py                   # Environment variables and path constants
│
├── tools/
│   ├── __init__.py             # Re-exports all tools for clean imports
│   ├── confluence.py           # create_confluence_page
│   ├── jira.py                 # create_jira_ticket
│   ├── filesystem.py           # list_directory, read_file, write_file
│   ├── git.py                  # git_commit_to_branch, create_github_pr
│   └── rag.py                  # search_company_knowledge_base + ChromaDB init
│
├── nodes/
│   ├── __init__.py             # Re-exports all node functions
│   ├── planner.py              # planner_node
│   ├── fe_executor.py          # fe_executor_node
│   ├── be_executor.py          # be_executor_node
│   ├── test_executor.py        # test_executor_node
│   ├── qa_executor.py          # qa_executor_node
│   └── infra_executor.py       # infra_executor_node
│
├── prompts/
│   ├── fe_executor.md          # System prompt for FE agent
│   ├── be_executor.md          # System prompt for BE agent
│   ├── test_executor.md        # System prompt for Test agent
│   ├── qa_executor.md          # System prompt for QA agent
│   └── infra_executor.md       # System prompt for Infra agent
│
├── docs/
│   └── clean_code_guidelines.md    # Company coding standards (indexed into RAG)
│
├── rag_db/                     # ChromaDB vector database (built by build_knowledge_base.py)
│   └── chroma.sqlite3
│
├── build_knowledge_base.py     # One-time RAG ingestion script
├── sdlc_workflow.py            # Legacy shim — delegates to main.py
│
└── guideline/
    ├── code_architecture.md    # This file
    ├── sdlc_workflow.md        # Workflow spec (current + target state)
    ├── hitl_implementation_plan.md   # HITL phases roadmap
    ├── how_i_did_it.md         # Concepts and definitions glossary
    └── stakeholder_pitch.md    # Non-technical stakeholder briefing
```

---

## Module Responsibilities

### `main.py`

The only entry point. Contains the interactive prompt loop and the two-phase HITL Gate 1 logic:

1. Streams the Planner phase
2. Pauses, displays the plan, accepts human approval or corrections
3. Resumes all executor nodes

**To run:** `python main.py`

---

### `graph.py`

Assembles the LangGraph `StateGraph`, adds all nodes and edges, and compiles the app with the `MemorySaver` checkpointer and `interrupt_before=["fe_executor"]` breakpoint.

This is the only file that needs to change when:

- Adding a new node to the pipeline
- Changing the execution order
- Enabling parallel execution (FE + BE via `Send()` API)
- Adding new HITL breakpoints (Phase 5, 6, 7)

---

### `state.py`

Defines `SDLCState` — the shared TypedDict passed between every node. Each node reads from state and writes its output field back.

Add new state fields here when implementing future HITL phases (e.g., `attempt_count`, `visual_preview_url`).

---

### `config.py`

Loads `.env` and exports all path constants (`FE_REPO_PATH`, `BE_REPO_PATH`, `JIRA_PATH`, `CONFLUENCE_PATH`, `ALLOWED_ROOTS`). Also performs the startup API key guard.

Every module imports from here — never read `os.getenv()` directly in node or tool files.

---

### `tools/`

Each file defines one or more `@tool`-decorated functions. Tools are how agents interact with the real world (filesystem, APIs, git, RAG).

| File            | Tools                                       | Notes                               |
| --------------- | ------------------------------------------- | ----------------------------------- |
| `confluence.py` | `create_confluence_page`                    | Mocked — writes local `.md`         |
| `jira.py`       | `create_jira_ticket`                        | Mocked — writes local `.md`         |
| `filesystem.py` | `list_directory`, `read_file`, `write_file` | Real — path traversal guarded       |
| `git.py`        | `git_commit_to_branch`, `create_github_pr`  | Defined but not yet wired to agents |
| `rag.py`        | `search_company_knowledge_base`             | Real — queries ChromaDB             |

To add a new tool: create a file in `tools/`, add the `@tool` decorator, export from `tools/__init__.py`.

---

### `nodes/`

Each file defines one node function. A node receives `SDLCState`, runs an agent with a specific prompt and tool set, and returns a partial state update.

**Pattern every node follows:**

1. Load prompt from `prompts/<name>.md`
2. Build the full prompt with dynamic state values injected
3. Call `_agent.invoke()`
4. Return the output field update

To add a new executor: create `nodes/<name>.py`, add it to `nodes/__init__.py`, add the node and edge to `graph.py`.

---

### `prompts/`

Plain Markdown files loaded at runtime by each node. Changing an agent's behaviour — its persona, what tools to call first, what rules to follow — requires only editing the `.md` file. No Python change needed.

---

### `rag_db/`

The ChromaDB vector database built from `docs/*.md`. Rebuilt by running `python build_knowledge_base.py`. Not committed to git (add to `.gitignore`).

---

## Import Dependency Graph

```
main.py
  ├── config.py
  ├── state.py
  └── graph.py
        ├── state.py
        └── nodes/
              ├── planner.py
              │     ├── config.py
              │     ├── state.py
              │     └── tools/ (confluence, jira)
              ├── fe_executor.py
              │     ├── config.py
              │     ├── state.py
              │     └── tools/ (filesystem, rag)
              └── ... (same pattern for be, test, qa, infra)
```

No circular imports. `config.py` and `state.py` are pure leaves — they import nothing from this project.

---

## How to Add a New Executor (e.g., `docs_executor`)

1. Create `prompts/docs_executor.md` with the agent's persona and instructions
2. Create `nodes/docs_executor.py` — copy the pattern from any existing executor node
3. Add `from .docs_executor import docs_executor_node` to `nodes/__init__.py`
4. In `graph.py`:
   - `workflow.add_node("docs_executor", docs_executor_node)`
   - Add the edge connecting it into the pipeline
5. Add `docs_output: str` to `SDLCState` in `state.py`
6. Add `"docs_output": ""` to `initial_state` in `main.py`

That's it — no other files need to change.
