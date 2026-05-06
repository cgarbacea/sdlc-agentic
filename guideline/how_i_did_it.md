# SDLC Agentic — Concepts & Definitions

This document explains the key concepts and terminology used in this project. No prior AI experience assumed.

---

## The Three Layers of Defense in Depth

In enterprise-grade AI systems, agents are controlled using three complementary methods. Using all three together is called **Defense in Depth** — each layer catches what the previous one misses.

| Layer               | What it does                                                                    | Where it lives in this project |
| ------------------- | ------------------------------------------------------------------------------- | ------------------------------ |
| **1. Prompts**      | Tells the agent who it is and how to behave                                     | `prompts/*.md`                 |
| **2. RAG**          | Gives the agent access to company knowledge without blowing up costs            | `rag_db/`, `docs/*.md`         |
| **3. Orchestrator** | A hard mathematical/structural check that the agent actually did what was asked | `qa_executor_node`             |

---

## Core Concepts

### LLM (Large Language Model)

The brain. In this project we use **Claude Sonnet** (by Anthropic). It receives text as input, reasons about it, and produces text as output. It can also decide to call **Tools** (see below).

---

### Agent

An LLM that has been given **Tools** and is allowed to decide, in a loop, which tool to call next until it considers its task complete. An agent is not just a one-shot question-and-answer — it reasons, acts, observes the result, and reasons again.

In this project, each Executor node runs an agent (powered by LangGraph's ReAct pattern).

---

### Tool

A Python function that an Agent can call during its reasoning loop. The LLM does not run code itself — it requests a tool call, and the framework executes it and returns the result. Tools are how agents interact with the real world.

Tools in this project include: `write_file`, `read_file`, `list_directory`, `create_jira_ticket`, `create_confluence_page`, `search_company_knowledge_base`, `git_commit_to_branch`, `create_github_pr`.

---

### Executor

A specialised agent node in the LangGraph workflow that is responsible for a single domain. It receives context from the shared state, uses its tools, and writes its output back to state.

Executors in this project:

| Executor              | Role                                                                        |
| --------------------- | --------------------------------------------------------------------------- |
| `planner_node`        | Lead Architect — creates Confluence PRD + Jira tickets + architectural plan |
| `fe_executor_node`    | Frontend Developer — writes React/TypeScript code to the FE repo            |
| `be_executor_node`    | Backend Developer — writes FastAPI Python code to the BE repo               |
| `test_executor_node`  | QA Engineer — writes pytest + vitest tests for generated code               |
| `qa_executor_node`    | QA Architect — reviews all code against guidelines, produces a QA report    |
| `infra_executor_node` | DevOps Engineer — writes Dockerfiles and docker-compose                     |

---

### Prompt (loaded from `.md`)

The system instruction for a specific executor. Instead of hardcoding instructions inside Python strings (which gets messy), each executor loads its persona and rules from a Markdown file at runtime. This means you can update an agent's behaviour by editing a `.md` file — no code change needed.

Prompt files in this project live in `prompts/`.

---

### RAG (Retrieval-Augmented Generation)

RAG is the pattern of giving an LLM access to a searchable knowledge base at query time, instead of loading all documents into the prompt upfront.

**The problem it solves:** If your company has 500 Confluence pages, you cannot paste all of them into every prompt — it would be too expensive and exceed the context window. RAG lets the agent search for only the 2-3 most relevant paragraphs at the moment it needs them.

**How it works conceptually:**

1. During an **ingestion phase** (run once), all your `.md` documentation is split into small chunks (~500 characters each) and converted into **Embedding Vectors** — arrays of numbers that represent the semantic meaning of the text.
2. Those vectors are stored in a **Vector Database** (ChromaDB in this project) alongside the original text and metadata.
3. At runtime, when an agent needs to know something, it sends a natural-language query. That query is also converted to a vector, and the database finds the stored chunks whose vectors are mathematically closest — meaning most semantically similar.
4. The matching chunks are returned as plain text and injected into the agent's prompt.

**The ingestion script** is `build_knowledge_base.py`. Run it once whenever `docs/` is updated.

---

### Embedding Vector

A list of numbers (e.g., 384 numbers for the `all-MiniLM-L6-v2` model) that encodes the _meaning_ of a piece of text. Two pieces of text with similar meaning will have vectors that are close together in mathematical space. This is what enables semantic search — searching by meaning rather than exact keyword.

---

### Vector Database (ChromaDB)

A database optimised for storing and searching Embedding Vectors. Unlike a SQL database that matches rows by value, a vector database matches rows by _distance_ — how similar the meaning of the query is to the stored documents.

In this project, ChromaDB stores its data in `rag_db/chroma.sqlite3`, which you can open with DBeaver or any SQLite viewer. The key tables are:

- `embedding_metadata` — the actual text chunks and their source file
- `embeddings` — the raw numeric vectors (not human-readable)

---

### SQLite

A lightweight, file-based database engine. There is no server to run — the entire database is a single `.sqlite3` file on disk. ChromaDB uses SQLite as its storage backend, which is why the knowledge base is just a folder you can copy, move, or open with DBeaver.

---

### LangGraph (Graph / State Machine)

The framework that connects all the executor nodes into a **directed graph** — a flowchart where each node is an agent and each edge defines what runs next. The graph also manages a shared **State** object that is passed from node to node, allowing each executor to read what previous executors produced and write its own outputs.

---

### State

The shared memory of the workflow. It is a typed Python dictionary (`SDLCState`) that is passed through every node. Each node can read any field and write to its own output fields. This is how the QA Executor can read what the FE and BE executors wrote, without those nodes needing to talk to each other directly.

---

### Orchestrator

In the context of this guide's "Defense in Depth" model, the Orchestrator is a node that acts as a hard, rule-based checker rather than a creative generator. It reads the outputs of other agents and verifies them against a known standard. The `qa_executor_node` plays this role — it reads generated code, queries the knowledge base for the relevant rules, and produces a structured PASS/FAIL report.

---

## How It All Comes Together

1. You describe a feature in plain English.
2. The **Planner** turns it into a Confluence PRD and Jira tickets.
3. The **FE and BE Executors** query the **RAG** knowledge base for coding standards, then write code to the real filesystem.
4. The **Test Executor** reads that code and writes automated tests.
5. The **QA Executor** (the Orchestrator layer) reads everything and checks it against the guidelines, producing a structured report.
6. The **Infra Executor** writes Dockerfiles and docker-compose so the whole thing can be deployed.

All of this happens by editing a feature description — no manual coding, no copy-pasting. The agents do the work; the guidelines, prompts, and RAG keep them aligned with your team's standards.

---

## Human-in-the-Loop (HITL) Concepts

Moving from POC to production means agents must not run fully unchecked. HITL is the pattern where a human is given the opportunity to review, approve, or correct agent output at defined points in the workflow before execution continues.

---

### HITL (Human-in-the-Loop)

The architectural pattern of inserting mandatory human review points into an otherwise autonomous agent workflow. The agent does the heavy lifting; the human acts as the Lead Engineer or Product Owner who signs off at critical gates. Without HITL, agents can silently make wrong decisions and propagate mistakes through every subsequent node.

In this project there are two natural HITL gates:

1. **Pre-development** — after the Planner produces the PRD and architecture plan, before any code is written.
2. **Post-development** — after code is written and pull requests are opened, before anything merges to main.

---

### Checkpointer

A LangGraph component that saves the entire graph state to persistent storage (memory, SQLite, or a database) at every step. This is what makes HITL possible — the graph can be paused, its state stored, and resumed later (even days later, or by a different process). Without a checkpointer, pausing the graph would lose all state.

In this project the `MemorySaver` checkpointer (in-memory) is used for local development. A production system would use a database-backed checkpointer (e.g., PostgreSQL via `AsyncPostgresSaver`).

---

### Breakpoint (`interrupt_before` / `interrupt_after`)

A LangGraph instruction that tells the graph to pause execution immediately before or after a specific named node. The graph enters a suspended state and waits for the human to either resume it (`app.stream(None, config)`) or update its state before resuming.

Example: `interrupt_before=["fe_executor"]` means the graph pauses after the Planner finishes and before any code is written — the perfect moment for human review of the plan.

---

### Thread ID

A unique identifier for a single run of the graph. The Checkpointer uses the thread ID to store and retrieve the correct state when the graph is paused and resumed. Think of it like a conversation ID — it allows multiple independent runs of the same workflow to coexist without interfering with each other.

Example: `thread_id: "feature-dark-mode-123"`.

---

### `app.get_state(config)`

A LangGraph API call that retrieves the current saved state of a paused graph for a given thread. Used by the human-review step to read what the Planner produced (the PRD, architect plan, Jira ticket summaries) before deciding to approve or correct.

---

### `app.update_state(config, values)`

A LangGraph API call that allows a human (or another process) to directly overwrite specific fields in the graph's state while it is paused. This is how human corrections are injected — for example, overwriting `architect_plan` with an amended version before resuming execution. When the next node wakes up, it reads the corrected state as if the agent had produced it.

---

### Resume (`app.stream(None, config)`)

Passing `None` as the input to `app.stream()` tells LangGraph to resume a paused graph from exactly where it stopped, using the state that is currently saved under the given thread ID. If `update_state` was called before resuming, the next node will see the updated values.

---

### Webhook

An HTTP callback that a system (e.g., GitHub) sends to your server when a specific event occurs, such as a PR comment being posted or a review being submitted. In the HITL architecture for post-development review, a webhook replaces the need for a paused Python process — the human reviews asynchronously on GitHub, and the webhook triggers a new agent run when feedback is ready.

---

### GitHub Actions / CI-CD

Automated pipelines that run in response to events in a GitHub repository. In the HITL pattern: if the human approves a PR, GitHub Actions triggers the merge and deploys to staging. If the human requests changes, a webhook triggers a new LangGraph thread that reads the review comments, fixes the code, and pushes a new commit to the same PR.

---

### POC vs. Enterprise Production Architecture

|                       | POC (Proof of Concept)           | Enterprise Production                           |
| --------------------- | -------------------------------- | ----------------------------------------------- |
| **Agent oversight**   | Fully autonomous, no human gates | HITL checkpoints at every critical transition   |
| **State persistence** | In-memory only, lost on restart  | Database-backed checkpointer (e.g., PostgreSQL) |
| **PR review**         | Mocked / skipped                 | Real GitHub PRs with human approval required    |
| **Error handling**    | Basic try/except                 | Retry policies, dead-letter queues, alerting    |
| **Concurrency**       | Single thread                    | Multiple threads, async execution               |
| **Secrets**           | `.env` file                      | Secrets manager (AWS Secrets Manager, Vault)    |

This project is currently at **POC stage** — the HITL implementation plan in `guideline/hitl_implementation_plan.md` defines the path to production.

---

## Iterative Plan Correction — How It Works

One of the subtler but most important design decisions in this system is _how_ human corrections at Gate 1 are applied to the architectural plan before executors run.

### The Naive Approach (What We Don't Do)

A simple implementation would append the human's correction text to the end of the plan:

```
[original 300-line plan]

--- Human Corrections ---
only 2 folders in src/: /components and /styles...
```

This fails because the executor LLM now sees **two conflicting documents**. The original plan has `atoms/`, `molecules/`, `organisms/` with detailed structure. The correction says "only 2 folders". The LLM pattern-matches to the larger, more authoritative-looking original and silently ignores the correction.

### The Right Approach (What We Do)

After the human types corrections, a **dedicated LLM call rewrites the plan** as one clean, unified document:

```
ORIGINAL PLAN:   [current version of the plan]
HUMAN CORRECTIONS: [what you just typed]
→ LLM produces:  [single clean rewritten plan with corrections incorporated]
```

The executor only ever sees the rewritten plan — no contradictions, no competing sections.

### Why Iterative Rounds Work

The loop repeats until the human types `yes`:

- **Round 1:** Human corrects the folder structure → LLM rewrites → shows Revised Plan v1
- **Round 2:** Human adds another constraint → LLM rewrites from v1 → shows Revised Plan v2
- **Round N:** Human approves → plan is indexed to RAG → executors run

Each round the LLM rewrites from the **current version**, not the original. This means corrections accumulate cleanly — round 2's rewrite already includes round 1's changes. The LLM always has:

1. **What was already decided** — the current plan (includes all previous rounds)
2. **What you want changed now** — your input this round

This mirrors how a human Lead Engineer would work with a junior: "here's the current draft — make this change" repeated until both parties are satisfied.

### Why the Approved Plan Goes into the RAG

Once approved, the plan is indexed into ChromaDB (`docs/plans/<feature>.md`). This has three benefits:

1. **Executors query it** — the FE executor can search `"libs/ui folder structure"` and retrieve the exact structure that was approved, not guess from a truncated prompt
2. **QA Executor can verify** — the QA agent can check generated code against the approved decisions rather than just coding guidelines
3. **Future runs benefit** — the next time a similar feature is built, the agent finds a real precedent from your own project, not just generic training data

This is the RAG's highest-value use case: not just company guidelines, but **the living memory of every architectural decision your team has approved**.

### Metis

https://github.com/metisos/metisos_agentV1/blob/master/README.md

|                  | **LangGraph** (what we use)                                           | **Metis**                                                             |
| ---------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Core concept** | Multi-agent **directed graph** — you define the flow                  | Single-agent **tool orchestration** — one smart agent picks tools     |
| **Architecture** | `Planner → FE → BE → Test → QA → Infra` pipeline                      | `SingleAgent.process_query()` — one agent routes internally           |
| **State**        | Typed shared state passed between specialised nodes                   | Session memory within one agent                                       |
| **HITL**         | Native `interrupt_before`, `checkpointer`, `update_state`             | Not in this framework                                                 |
| **Strengths**    | Complex multi-step workflows, human review gates, conditional routing | 36+ built-in tools, fast setup, memory management, security hardening |
| **Best for**     | Orchestrating multiple specialised agents with defined handoffs       | Building a single capable assistant quickly                           |

**For our SDLC use case, LangGraph is the right choice** — we specifically need the multi-agent pipeline (Planner → FE → BE → QA → Infra), the HITL breakpoints, and state passing between nodes. Metis doesn't expose those primitives.

**Where Metis could genuinely help us:**

- Its `SecurePathValidator` and input validation framework are production-grade — could replace our hand-rolled path traversal guard in `write_file`
- Its `Titans memory` system is more sophisticated than our `MemorySaver` for session persistence
- Its built-in Git integration tools are already hardened — could augment or replace our git.py

## **The practical answer:** Keep LangGraph as the orchestration engine. Metis could be used to enhance individual executor agents with its memory and security utilities, or its tools could be wrapped and exposed as LangGraph tools. They're complementary, not competing.

## MCP — Model Context Protocol

### What It Is

MCP (Model Context Protocol) is a standard developed by Anthropic that defines how AI tools (Claude, Copilot, Cursor, etc.) can call external services during their reasoning loop. Think of it as a USB port for AI — instead of each AI tool having a proprietary plugin system, MCP provides one standard interface. A service that speaks MCP can be used by any MCP-compatible AI client without extra integration work.

An **MCP Server** exposes a set of **tools** (functions) over a protocol (stdio or HTTP). The AI client discovers the available tools, then decides which ones to call based on the user's query — exactly like the LangGraph tool-calling pattern, but standardised and decoupled from any specific framework.

---

### Why It Matters for This Project

Our SDLC pipeline currently runs as a Python script you invoke manually. It is not accessible to AI development tools like GitHub Copilot, Claude Code, or Cursor. An MCP server would change that: a developer could ask Copilot "generate a dark mode feature" and Copilot would call our pipeline as a tool — without leaving their editor.

This is what the requirements document means by:

> _"MCP-compatible server modules to integrate runtime environments with AI development tools"_
> _"MCP integrations to orchestrate AI-based tooling in CI/CD"_

---

### The CopilotMod Error — What It Is and Why It Fails

When VS Code shows:

```
The MCP server CopilotMod may have new tools and requires interaction to start. Starting CopilotMod...
```

This is coming from the **`ms-dotnettools.vscode-dotnet-modernize`** extension (installed at `~/.vscode/extensions/ms-dotnettools.vscode-dotnet-modernize-1.0.1063`). Inside that extension's bundle, `CopilotMod` is the registered name of an MCP server:

```js
// from the extension bundle
n.CopilotMod = "CopilotMod";
n.McpNuGetPackageId = "Microsoft.GitHubCopilot.Modernization.Mcp";
```

The extension tries to launch this MCP server with the command:

```
dnx Microsoft.GitHubCopilot.Modernization.Mcp --yes --prerelease
```

`dnx` is a .NET tool runner (similar to `npx` for Node). The server itself is a NuGet package — a .NET executable that Microsoft ships as their copilot-for-.NET migration tool.

**Why it fails on this machine:**

```
dnx not found
dotnet not found
```

Neither `dnx` nor .NET SDK is installed. The extension registers its MCP server definition, VS Code attempts to start it, the process fails silently because the runtime doesn't exist. The "requires interaction to start" message is VS Code asking you to confirm starting a newly registered MCP server — it is not an error you caused.

**How to fix it (if you want .NET Copilot features):**

1. Install .NET SDK 10: `brew install --cask dotnet`
2. Install `dnx` (once dotnet is present): `dotnet tool install -g dnx`
3. Restart VS Code — the extension will then successfully start the CopilotMod server

**If you don't need .NET Copilot modernization**, you can suppress the prompt by disabling the extension: `ms-dotnettools.vscode-dotnet-modernize`.

---

### How an MCP Server for Our SDLC Pipeline Would Work

An MCP server is just a process (Python, Node, .NET — doesn't matter) that reads JSON-RPC messages from stdin and writes responses to stdout. Here is what a minimal Python MCP server exposing our pipeline would look like conceptually:

```python
# mcp_server.py — expose the SDLC pipeline as an MCP tool
@tool(name="run_sdlc_pipeline", description="Run the full SDLC workflow for a feature")
def run_sdlc_pipeline(feature_description: str, thread_id: str) -> dict:
    result = app.invoke(
        {"feature_description": feature_description},
        config={"configurable": {"thread_id": thread_id}},
    )
    return {"status": "complete", "plan": result["architect_plan"]}
```

Once this server is registered in VS Code's `mcp.json`:

```json
{
  "servers": {
    "sdlc-pipeline": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

GitHub Copilot, Claude, or Cursor can call `run_sdlc_pipeline` as a native tool. The developer asks their AI assistant to build a feature; the assistant calls our pipeline; the pipeline runs its Planner → FE → BE → QA → Infra graph; the result comes back as structured data the AI can summarise and present.

This is the **next natural evolution** of this project — turning the standalone script into an MCP server completes the "AI-Augmented SDLC" pillar from the requirements document.
