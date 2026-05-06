# how MCP works

```bash
┌─────────────────────────────────────────────────────┐
│ Your message in Copilot Chat                        │
│ "Use the sdlc pipeline to build dark mode..."       │
└─────────────────┬───────────────────────────────────┘
                  │ Copilot decides to call a tool
                  ▼
┌─────────────────────────────────────────────────────┐
│ VS Code MCP client │
│ Reads .vscode/mcp.json │
│ Starts: venv/bin/python mcp_server.py │
│ Sends JSON-RPC over stdin/stdout │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ mcp_server.py (running as a subprocess)             │
│ Receives: start_pipeline("dark mode toggle")        │
│ Calls: LangGraph pipeline → Planner runs            │
│ Returns: { thread_id, plan_preview, status }        │
└─────────────────────────────────────────────────────┘
```

---

## Step-by-Step: How to Test It Right Now

### Step 1 — Check VS Code sees the server

Open the **Command Palette** (`Cmd+Shift+P`) and type:

```
MCP: List Servers
```

You should see `sdlc-pipeline` listed. If it shows a ⚠️ or ✗, the server failed to start — the output log will tell you why.

Alternatively open the **Output** panel (`Cmd+Shift+U`) and select **"MCP: sdlc-pipeline"** from the dropdown — you'll see the server's stderr logs there in real time.

### Step 2 — Confirm the tools are visible

In the Command Palette:

```
MCP: List Tools
```

You should see all 4: `start_pipeline`, `get_pipeline_state`, `approve_plan`, `list_threads`.

### Step 3 — Where to type the prompt

Open **GitHub Copilot Chat** — the chat panel on the left sidebar (the speech bubble icon), **not** the inline editor suggestion. Make sure you're in **Agent mode** (the dropdown at the bottom of the chat box should say "Agent" not "Ask" or "Edit").

Then type:

```
Use the sdlc pipeline to start building a dark mode toggle feature
```

Copilot will:

1. Recognise it needs to call `start_pipeline`
2. Ask your permission (you'll see a "Run tool?" confirmation)
3. Call the tool → your pipeline runs → returns the plan
4. Summarise the plan in the chat

### Step 4 — What you'll see if it's working

The chat response will contain something like:

> "The pipeline has started. Thread ID: `build-a-dark-mode-toggle-f`. The planner produced the following architecture plan: [plan text]. Call `approve_plan` to proceed with code generation."

---

## If the Server Doesn't Appear

Most common reasons:

| Problem                         | Fix                                                                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| mcp.json not loaded             | Open this workspace folder directly (`code /path/to/sdlc-agentic`) — mcp.json only applies to the workspace it's in |
| VS Code needs a reload          | `Cmd+Shift+P` → "Developer: Reload Window"                                                                          |
| `ANTHROPIC_API_KEY` not in .env | The pipeline will fail on first tool call — check Output panel logs                                                 |
| Not in Agent mode               | Switch the chat dropdown from "Ask" to "Agent"                                                                      |

Go check **MCP: List Servers** in the Command Palette first — that's the definitive answer on whether VS Code has picked it up. What do you see?
