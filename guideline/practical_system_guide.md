# Practical System Guide

This guide is for learning the system by using it, not by reading all the source first.

The goal is simple:

1. Understand what each part does.
2. Run the system safely.
3. Learn how the pauses, retries, and checkpoints work.
4. Get comfortable enough to record a polished demo later.

---

## 1. What This System Is

This repo is a LangGraph-based SDLC pipeline. You give it a feature request, and it:

1. Writes requirements and tickets.
2. Produces a no-code architecture plan.
3. Stops for human review at Gate 1.
4. Runs FE, BE, Test, QA, and Infra executors.
5. Uses checkpoints so you can resume later.
6. Uses retry and escalation logic when QA gets stuck.

The important idea is that you do not need to understand every file before you start using it. You need a working mental model, then you learn by running it.

---

## 2. Start Here

If you only read five files, read these:

1. [README.md](../README.md)
2. [main.py](../main.py)
3. [graph.py](../graph.py)
4. [state.py](../state.py)
5. [mcp_server.py](../mcp_server.py)

Those files tell you:

- how the graph is wired,
- how the CLI works,
- what state moves between nodes,
- and how AI clients call the system through MCP.

The executors live in [nodes/](../nodes) and the reusable prompts live in [prompts/](../prompts).

---

## 3. The Mental Model

Think of the system as four layers.

### Layer 1: Input

You provide a feature request, either interactively or via CLI.

### Layer 2: Planning

Requirements and architecture are generated first. This is where Gate 1 happens.

### Layer 3: Execution

The FE, BE, Test, QA, and Infra nodes do the work.

### Layer 4: Review and Recovery

The system can pause, resume, retry, and escalate when QA fails too many times.

If you remember only one thing, remember this:

the system is meant to be paused, inspected, corrected, and resumed.

---

## 4. What Each Major File Does

### [main.py](../main.py)

This is the CLI runner.

Use it when you want to:

- start a new feature run,
- inspect the Gate 1 plan,
- approve or correct the plan,
- resume a paused run,
- or handle a QA escalation pause.

### [graph.py](../graph.py)

This is the workflow wiring.

It tells you:

- which node runs first,
- where the pauses happen,
- and how execution routes after QA.

### [state.py](../state.py)

This is the shared memory between nodes.

It holds fields such as:

- user_request,
- requirements,
- architect_plan,
- qa_report,
- attempt_count,
- human_escalation,
- pr_urls.

### [mcp_server.py](../mcp_server.py)

This exposes the workflow as tools for AI clients.

Use it when you want Copilot or another MCP client to call the pipeline directly.

### [nodes/](../nodes)

Each node is one role in the pipeline.

- requirements_node: creates PRD and Jira artifacts.
- architect_node: writes the plan.
- fe_executor: frontend work.
- be_executor: backend work and ArchUnit validation loop.
- test_executor: test generation.
- qa_executor: QA report generation.
- infra_executor: infra artifacts.
- human_escalation: pause-and-resume recovery when QA fails too many times.

---

## 5. The Normal Workflow

### Step 1: Check provider status

Run this first if you are not sure what LLM provider is active.

```bash
python main.py --provider-check-only
```

This shows the configured provider, the effective provider, and any missing environment variables.

### Step 2: Start in stub mode if you want safe practice

Stub mode is the fastest way to learn the flow without depending on external APIs.

```bash
LLM_PROVIDER=stub python main.py --feature "practice run" --non-interactive
```

Use this to learn:

- what the plan looks like,
- how checkpoints behave,
- how the output is structured.

### Step 3: Run interactively

```bash
python main.py --feature "Add dark mode toggle"
```

You will see:

1. Requirements phase.
2. Architecture plan.
3. Gate 1 review prompt.
4. Executor progress.
5. Final PR URLs when available.

### Step 4: Correct the plan if needed

At Gate 1, you can type corrections instead of `yes`.

Use this to learn how the plan rewrite behaves.

### Step 5: Resume a paused thread

If the run is paused, use the thread id to continue it.

```bash
python main.py --thread-id <existing-thread-id>
```

This is the normal recovery path when you stop a run and want to continue later.

---

## 6. How Gate 1 Works

Gate 1 is the first human checkpoint.

What you will see:

- a generated plan,
- a prompt asking for approval or corrections,
- a rewrite if you provide feedback,
- then the executors continue.

What to practice:

1. Run a feature.
2. Ask for one small correction.
3. Observe how the plan changes.
4. Approve it.
5. Watch the downstream nodes continue.

This is the safest place to learn the system because nothing has been written to the target repos yet.

---

## 7. How the QA Escalation Loop Works

The system now has a loop breaker.

If QA fails repeatedly:

1. The graph increments attempt count.
2. After the threshold, it pauses at human escalation.
3. You provide human guidance.
4. The system resumes with that feedback injected.

This is useful when you want to learn how the system recovers from repeated failures instead of spinning forever.

When testing this behavior, use the focused integration test in [tests/test_escalation_loop.py](../tests/test_escalation_loop.py) as your reference for expected behavior.

---

## 8. How to Use MCP

MCP is the easiest way to let an AI client drive the workflow.

The available tools include:

- health_check
- start_pipeline
- get_pipeline_state
- approve_plan
- resolve_escalation
- list_threads

### Practical use cases

Use MCP when you want to:

1. Start a run from Copilot.
2. Inspect a paused run.
3. Approve or correct the plan.
4. Recover from a QA escalation pause.

### Health check

Before using the MCP server in a client, confirm it responds:

```bash
make run-health
```

Then check:

```text
http://127.0.0.1:8081/health
```

---

## 9. How to Learn the System Fast

Use this learning order.

### Session 1: Read-only understanding

1. Read [README.md](../README.md).
2. Read [main.py](../main.py).
3. Run `python main.py --provider-check-only`.

### Session 2: Safe execution

1. Run stub mode.
2. Observe Gate 1.
3. Approve a simple plan.

### Session 3: Pause and resume

1. Start a run.
2. Stop after Gate 1 or a pause.
3. Resume with `--thread-id`.

### Session 4: Failure recovery

1. Observe the QA loop-breaker test.
2. Learn how human escalation works.
3. Use the MCP `resolve_escalation` flow if needed.

### Session 5: AI-client integration

1. Start the MCP server.
2. Call `start_pipeline` from a client.
3. Read state with `get_pipeline_state`.

---

## 10. What to Watch For

When you run the system, pay attention to these signals:

1. The current phase name in the terminal.
2. Whether you are paused at Gate 1 or escalation.
3. The thread id.
4. The plan text.
5. The QA report.
6. Any PR URLs printed at the end.

If the output looks confusing, do not jump straight into code. First ask:

- Which phase am I in?
- Is this a Gate 1 pause or a QA escalation pause?
- Do I need to correct the plan or resume the thread?

---

## 11. Common Problems and What They Mean

### Problem: The run stops early

Likely cause:

- Gate 1 pause is waiting for approval.

What to do:

- read the plan,
- correct it if needed,
- then approve or resume.

### Problem: The run keeps failing QA

Likely cause:

- a validation issue keeps repeating.

What to do:

- inspect the QA report,
- provide escalation feedback,
- resume the thread.

### Problem: MCP starts slowly

Likely cause:

- lazy loading is importing the pipeline on first tool call.

What to do:

- use `health_check` first,
- then call `start_pipeline`.

### Problem: No PR URL appears

Likely cause:

- GitHub credentials are missing, so the system is in safe fallback mode.

What to do:

- verify `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_FE_REPO`, and `GITHUB_BE_REPO`.

---

## 12. Practical Learning Path

If your goal is to become comfortable enough to demo this confidently, do this:

1. Run stub mode once.
2. Run a normal feature once.
3. Trigger one Gate 1 correction.
4. Trigger one QA escalation flow.
5. Start and inspect one MCP thread.
6. Read the resulting outputs.

After that, the system will feel much less abstract.

---

## 13. When You Are Ready For A Demo

You are ready to record a demo when you can do these steps without hesitation:

1. Start a feature run.
2. Explain what Gate 1 is.
3. Make one correction to the plan.
4. Resume the run.
5. Explain what a QA escalation pause means.
6. Recover from it once.
7. Show the final output or PR URL.

If you cannot do those steps smoothly yet, that is normal. Keep practicing runs first.

---

## 14. Best Next Move

Do not start by trying to produce a perfect demo.

Start by doing three or four real runs and learning the shape of the workflow.

That will make the later demo much easier to record cleanly.
