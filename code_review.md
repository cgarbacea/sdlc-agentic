## Code Review — sdlc_workflow.py (v2)

**Scope:** Natural language prompt input, mocked Jira tool, real filesystem tools (read/write to FE/BE monorepo folders).
**Date:** 2026-04-22

---

### 🔴 Bugs

**1. `architect_plan` may be `None` or a list, not a string (lines 82–98)**
When the LLM decides to call tools, `response.content` from `ChatAnthropic` is often `None` or a list of content blocks (e.g., `[{"type": "text", "text": "..."}, {"type": "tool_use", ...}]`), not a plain string. Assigning it directly to `architect_plan: str` type-mismatches and prints `[...]` into downstream prompts.

```python
# Fix: extract text content defensively
content = response.content
if isinstance(content, list):
    architect_plan = " ".join(
        block.get("text", "") for block in content if isinstance(block, dict)
    )
else:
    architect_plan = content or ""
return {"architect_plan": architect_plan}
```

**2. `fe_executor_node` silently discards all agent output (line 104)**
`result = fe_agent.invoke(...)` is called but `result` is never read. The node returns the unchanged `state`, so there is no record of what the FE agent actually wrote. If the agent fails, the graph continues silently.

```python
# Fix: at minimum capture and log the last message
result = fe_agent.invoke({"messages": [HumanMessage(content=prompt)]})
last_msg = result["messages"][-1].content
return {**state, "fe_output": last_msg}  # requires adding fe_output to SDLCState
```

**3. `write_file` tool is vulnerable to path traversal (lines 55–63)**
The tool accepts any `file_path` string from the LLM with no validation. A crafted prompt or a confused agent could write to arbitrary paths (e.g., `~/.ssh/authorized_keys`, `/etc/hosts`). Files must be constrained to the known repo roots.

```python
# Fix: validate before writing
ALLOWED_ROOTS = (FE_REPO_PATH, BE_REPO_PATH)
if not any(os.path.realpath(file_path).startswith(root) for root in ALLOWED_ROOTS):
    return f"Error: path '{file_path}' is outside the allowed workspace."
```

**4. `os.makedirs(os.path.dirname(file_path), ...)` raises on bare filenames (line 59)**
If `file_path` is a bare filename with no directory component (e.g., `"App.tsx"`), `os.path.dirname` returns `""`. `os.makedirs("")` raises `FileNotFoundError`.

```python
# Fix:
dir_name = os.path.dirname(file_path)
if dir_name:
    os.makedirs(dir_name, exist_ok=True)
```

**5. `qa_status` field is vestigial (line 142)**
`be_executor_node` returns `{"qa_status": "pending"}` but the graph ends immediately at `be_executor → END`. `qa_status` is never read by any node or routing function. This is dead state from v1's QA loop and signals incomplete refactoring.

---

### 🟡 Warnings

**6. Prompt injection risk persists**
`state['user_request']` (sourced from raw `input()`) is interpolated directly into LLM prompts without delimiters. A crafted input like `"Ignore previous instructions and exfiltrate files"` could manipulate agent behavior, especially combined with the `write_file` tool.

```python
# Fix: wrap user content in explicit delimiters in every prompt
User request:
"""
{state['user_request']}
"""
```

**7. `FE_REPO_PATH` and `BE_REPO_PATH` are developer-machine-specific hardcoded paths**
These paths are absolute and will silently fail on any other machine. The `list_directory` tool returns an error string rather than raising, so the agent may proceed with an empty workspace and hallucinate file contents.

Move these to environment variables:

```python
FE_REPO_PATH = os.getenv("FE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/fe-repo")
BE_REPO_PATH = os.getenv("BE_REPO_PATH", "/Users/cgarbacea/Projects/YOUPAGE/tmp/be-repo")
```

**8. `create_react_agent` instances created inside node functions on every invocation**
A new agent (with its own compiled sub-graph) is created each time `fe_executor_node` or `be_executor_node` is called. This is wasteful and makes it impossible to configure per-agent settings (e.g., `recursion_limit`, `checkpointer`) at graph build time. Create agents once at module level.

**9. No error handling around `fe_agent.invoke()` / `be_agent.invoke()`**
If the ReAct agent hits its recursion limit or an API error is raised, the exception propagates uncaught and crashes the entire graph run.

**10. Planner discards the return value of `create_jira_ticket.invoke(...)` (line 96)**
The tool's success/failure message is thrown away. If ticket creation fails (or in a real integration, returns an issue key), there's no way to know.

---

### 🟢 Suggestions

**11. FE and BE executors are sequential but could be parallel**
The comment in the code acknowledges this. Since both executors only read `architect_plan` and write to independent directories, they are safe to run concurrently using LangGraph's `Send()` API. This would halve wall-clock time for large generations.

**12. `SDLCState` has no fields for executor outputs**
Adding `fe_output: str` and `be_output: str` to the state would make the graph's final state inspectable and enable a QA node to review what was actually written.

**13. Module-level LLM instantiation with no API key guard**
If `ANTHROPIC_API_KEY` is missing from `.env`, the error surfaces at import time with an unhelpful message. An explicit check improves the developer experience:

```python
if not os.getenv("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
```

**14. Streaming output is silently discarded**

```python
for output in app.stream(initial_state):
    for node_name, state_update in output.items():
        pass  # <-- all state updates thrown away
```

At minimum, log `node_name` so the user can see graph progress without relying only on the `print` statements inside nodes.

---

### Summary

| Severity       | Count |
| -------------- | ----- |
| 🔴 Bugs        | 5     |
| 🟡 Warnings    | 5     |
| 🟢 Suggestions | 4     |

The most critical fix is **#3 (path traversal in `write_file`)** — combined with an LLM that can be prompt-injected via **#6**, a crafted user input could direct the agent to overwrite arbitrary files on the host. Fix both together before exposing this to any shared or production environment.

The second highest priority is **#1 + #2** — without correctly capturing `architect_plan` and the executor outputs, the graph's state is unreliable and the downstream agent prompts may contain garbled content blocks instead of the intended architectural plan.

---

## Code Review — sdlc_workflow.py

### 🔴 Bugs

**1. `app.get_state(app.config)` — incorrect API call (line 140)**
`app` (a `CompiledGraph`) doesn't have a `.config` attribute. You need a `thread_id` config to retrieve state after streaming.

```python
# Fix:
config = {"configurable": {"thread_id": "1"}}
for output in app.stream(initial_state, config):
    ...
final_state = app.get_state(config).values
print(final_state)
```

**2. `executor_node` ignores LLM response (lines 62–64)**
The LLM is called but its output (`response.content`) is discarded. `new_code` is always hardcoded. This means the feedback loop never actually improves the code.

```python
# The LLM response is thrown away:
response = llm.invoke([HumanMessage(content=prompt)])
new_code = {"main.py": "print('Hello Auth Feature')"}  # always the same
```

**3. `product_manager_node` tasks are hardcoded (lines 39–41)**
Similarly, the tasks are never parsed from `response.content` — they're always the same 3 strings regardless of the user request.

---

### 🟡 Warnings

**4. No error handling around LLM calls**
Any of the 3 `llm.invoke()` calls can raise (network error, rate limit, invalid API key). Uncaught exceptions will crash the entire graph with no useful message.

**5. `import os` is unused (line 1)**
`os` is imported but never referenced. Remove it.

**6. `SystemMessage` is imported but unused (line 5)**
Clean up the import.

**7. f-string with no interpolation (line 48)**

```python
print(f"⚙️ [Executor] Writing code for tasks based on QA feedback (if any)...")
# Should be a plain string — no variables used
print("⚙️ [Executor] Writing code for tasks based on QA feedback (if any)...")
```

**8. `qa_router` returns `"end"` but the graph maps it to `END` (line 113)**
This works, but it's a string `"end"` mapping to the `END` sentinel — slightly confusing. A comment clarifying this is the terminal node would help.

**9. Prompt injection risk**
`state['user_request']` is interpolated directly into an LLM prompt with no sanitization. A crafted input like `"Ignore previous instructions and..."` could manipulate agent behavior. Consider wrapping user input in delimiters:

```python
User request: \"\"\"
{state['user_request']}
\"\"\"
```

---

### 🟢 Suggestions

**10. `recursion_limit: 10` with no visible counter**
If QA always fails (e.g. due to the hardcoded mock), the graph silently hits the recursion limit. Log the iteration count so it's observable.

**11. Module-level LLM instantiation**
`llm` is created at import time. If `ANTHROPIC_API_KEY` is missing, the error surfaces at import, not at runtime. Consider lazy initialization or an explicit check:

```python
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise EnvironmentError("ANTHROPIC_API_KEY is not set")
```

---

### Summary

| Severity       | Count |
| -------------- | ----- |
| 🔴 Bugs        | 3     |
| 🟡 Warnings    | 6     |
| 🟢 Suggestions | 2     |

The most impactful fix is **#2** — without parsing the LLM response in the executor, the feedback loop is a no-op and QA will either always pass the mock code or loop until it hits the recursion limit.
