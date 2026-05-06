# Next Agentic — Multi-Repo Reconciliation & Unified Development Plan

## The Problem

The current POC assumes a clean-slate FE + BE. The real world looks like this:

| Repo              | Stack                          | Status                                                     |
| ----------------- | ------------------------------ | ---------------------------------------------------------- |
| `fe-nextjs-a`     | Next.js + TypeScript           | Has styles and components duplicated in `fe-nextjs-b`      |
| `fe-nextjs-b`     | Next.js + TypeScript           | The "other" FE — needs styles merged from `a`              |
| `be-java`         | Java (Spring Boot)             | The canonical BE — target for all service consolidation    |
| `be-python`       | Python (FastAPI)               | Duplicate of Java services — must be merged into `be-java` |
| `infra-terraform` | Terraform                      | Standalone infra repo                                      |
| `monorepo`        | Python BE + Next.js FE + Infra | All-in-one repo — overlaps with every other repo           |

These repos do the same things in different ways. The goal is not to rewrite them — it is to **reconcile** them: understand what each one does, decide the canonical approach, and execute a migration plan across all of them without breaking anything.

---

## Why a Simple Prompt Won't Work

A single prompt to an LLM asking "merge these repos" will produce:

- Hallucinated APIs it has never seen
- Ignored domain-specific patterns that exist only in your codebase
- A plan that makes sense in isolation but breaks integration contracts
- No awareness of what files actually exist, what's duplicated, what's conflicting

What we need instead:

1. **A knowledge base per repo** — each repo's architecture, patterns, and decisions indexed into RAG so agents can query them
2. **A reconciliation agent** — reads all knowledge bases, identifies overlaps and conflicts, produces a unified canonical plan
3. **A plan file** — a single, human-approved, structured document that defines the end state and the migratiosalut, ni
4. **Executor agents** — one per repo, each receiving the canonical plan + its own repo's knowledge base, executing only its part

---

## The Core Idea: "Build the Knowledge, Build the Plan, Execute the Plan"

```
PHASE 0 — UNDERSTAND
    For each repo:
        → Crawl the repo (read files, structure, dependencies)
        → Build a RAG knowledge base specific to that repo
        → Generate a "Repo Summary" — what it does, how, what patterns it uses

PHASE 1 — RECONCILE
    Reconciliation Agent reads all Repo Summaries
        → Identifies: duplications, conflicts, canonical patterns
        → Proposes: what survives, what merges, what gets deleted
        → Human reviews + corrects (Gate 1 — iterative, like current system)
        → Produces: THE CANONICAL PLAN FILE

PHASE 2 — PLAN
    The Canonical Plan File defines:
        → Target architecture (what each repo looks like at the end)
        → Migration steps per repo (ordered, with dependencies)
        → Contracts between repos (API specs, shared types, event schemas)
        → What must not change (backwards compatibility requirements)

PHASE 3 — EXECUTE
    For each repo (parallelisable where dependencies allow):
        → Repo Executor reads: Canonical Plan + its own RAG + current codebase
        → Executes only its section of the plan
        → Commits to a branch, opens a PR
        → Human reviews per repo (Gate 2)

PHASE 4 — VALIDATE
    Cross-repo QA Agent:
        → Verifies contracts between repos are satisfied
        → Checks that the FE calls endpoints that the BE now actually exposes
        → Checks that infra provisions what the apps expect
        → Produces a cross-repo integration report
```

---

## What Makes This Different From the POC

| POC                                     | Next Agentic                                      |
| --------------------------------------- | ------------------------------------------------- |
| 1 FE repo, 1 BE repo (tmp folders)      | N real repos, each with history                   |
| Plan generated from a 2-sentence prompt | Plan generated from deep codebase analysis        |
| Executors write from scratch            | Executors modify existing code                    |
| No cross-repo awareness                 | Contracts and dependencies tracked explicitly     |
| Single knowledge base                   | One RAG per repo + one unified reconciliation RAG |
| Sequential execution                    | Parallel execution where repo dependencies allow  |

---

## The Knowledge Base Strategy (Per-Repo RAG)

Each repo gets its own `docs/<repo-name>/` folder and its own ChromaDB collection (or a namespaced partition of the shared DB). The ingestion agent crawls the repo and generates:

### What Gets Indexed

| Document type      | What it captures                                             |
| ------------------ | ------------------------------------------------------------ |
| `repo_summary.md`  | What the repo does, its domain, its primary responsibilities |
| `architecture.md`  | Folder structure, key modules, design patterns used          |
| `api_contracts.md` | All exposed endpoints / events / exports with signatures     |
| `dependencies.md`  | External libs, internal services this repo calls             |
| `patterns.md`      | Coding conventions, naming, error handling, auth patterns    |
| `tech_stack.md`    | Framework versions, build tools, test frameworks             |

These are **agent-generated** (the ingestion agent reads the codebase and writes the summaries), then **human-reviewed** before being indexed. This is Gate 0 — before the plan is even built.

---

## The Canonical Plan File

The single most important artefact in this system. It is the source of truth that every executor reads.

### Structure

```markdown
# Canonical Migration Plan — [Project Name]

## 1. End State Architecture

What each repo will contain when done.
What gets deleted / archived.

## 2. Contracts (must not break)

- API: /api/v1/users → stays in be-java, Python version removed
- Shared types: UserDTO → canonical version in be-java, FE uses OpenAPI-generated client
- Events: auth.login → Kafka topic spec

## 3. Migration Steps (ordered by dependency)

Step 1: [be-python] Identify all endpoints not yet in be-java → list them
Step 2: [be-java] Port missing endpoints from be-python
Step 3: [be-python] Deprecation — remove ported endpoints, add redirect stubs
Step 4: [fe-nextjs-a] Update API client to use be-java URLs only
...

## 4. Per-Repo Instructions

### be-java

- Add: [list of new endpoints]
- Modify: [list of files to change]
- Do not touch: [list of stable files]

### be-python

- Remove: [list of deprecated endpoints]
- Redirect: [mapping old → new URLs]
- Archive: [files to move, not delete]

### fe-nextjs-a

- Merge from fe-nextjs-b: [list of style files]
- Update imports: [search/replace patterns]
  ...
```

---

## The Agents Needed

### New agents (beyond the POC)

| Agent                      | Role                                                                               |
| -------------------------- | ---------------------------------------------------------------------------------- |
| `repo_crawler_node`        | Reads a real repo's file tree, generates structured summaries                      |
| `reconciliation_node`      | Reads all repo summaries, identifies overlaps/conflicts, drafts the canonical plan |
| `contract_extractor_node`  | Extracts API signatures, shared types, event schemas from each repo                |
| `dependency_resolver_node` | Orders migration steps by dependency (can't migrate FE until BE endpoint exists)   |
| `cross_repo_qa_node`       | After all executors run, verifies inter-repo contracts are satisfied               |

### Adapted from POC

| Agent                     | Adaptation needed                                                                        |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| `fe_executor_node`        | Must modify existing files, not just create new ones. Needs `read_file` + diff awareness |
| `be_java_executor_node`   | Java-specific — different tools (Maven/Gradle, not pip)                                  |
| `be_python_executor_node` | Deprecation mode — removes code safely rather than adding                                |
| `infra_executor_node`     | Terraform-aware — `terraform plan` output before applying                                |

---

## The Critical New Tool: `read_repo`

The POC only writes to the repo. The next system needs to **read and understand** what's already there.

```python
@tool
def read_repo_structure(repo_path: str, max_depth: int = 4) -> str:
    """
    Returns a structured tree of the repo with file types and sizes.
    Used by the crawler agent to understand what exists before planning.
    """

@tool
def search_in_repo(repo_path: str, pattern: str) -> str:
    """
    Searches for a pattern (function name, endpoint, class) across all files.
    Used to find duplications and locate what needs migrating.
    """

@tool
def diff_files(file_a: str, file_b: str) -> str:
    """
    Returns a structured diff between two files across repos.
    Used by the reconciliation agent to compare implementations.
    """
```

---

## Human Gates in This System

| Gate          | When                          | What human does                                                                    |
| ------------- | ----------------------------- | ---------------------------------------------------------------------------------- |
| **Gate 0**    | After each repo is crawled    | Reviews the generated repo summary — corrects misunderstandings                    |
| **Gate 1**    | After reconciliation          | Reviews the canonical plan — approves or corrects the migration strategy           |
| **Gate 2a–N** | After each repo executor runs | Reviews the PR for that repo                                                       |
| **Gate 3**    | After cross-repo QA           | Reviews the integration report — confirms contracts are satisfied before any merge |

---

## Implementation Phases

### Phase A — Repo Understanding (build this next)

- `repo_crawler_node` that reads a real repo and generates the summary docs
- Per-repo RAG collections in ChromaDB (namespaced by repo name)
- Gate 0 review loop (same iterative rewrite pattern as Gate 1 in the POC)

### Phase B — Reconciliation

- `reconciliation_node` that reads all repo RAGs and drafts the canonical plan
- `contract_extractor_node` for API/type/event contracts
- Gate 1 — canonical plan review with iterative correction (identical pattern to POC Gate 1)

### Phase C — Parallel Execution

- Adapt executor nodes to modify existing code (not just create)
- `dependency_resolver_node` to order execution
- Per-repo Git branches + PRs (Phase 2 of POC, already partially built)

### Phase D — Cross-Repo Validation

- `cross_repo_qa_node`
- Integration contract verification
- Gate 3 — final human sign-off before any merges

---

## What Carries Over From the POC

Everything we built is reusable:

- **Iterative plan correction** (Gate 1 rewrite loop) → same pattern for Gate 0 and Gate 1 here
- **RAG knowledge base** → extend to per-repo collections
- **Executor node pattern** → same structure, adapted tools
- **HITL checkpointer + breakpoints** → same LangGraph primitives
- **Prompt files per agent** → `prompts/reconciliation_agent.md`, `prompts/repo_crawler.md` etc.
- **`search_company_knowledge_base` tool** → extend to accept a `repo_name` filter parameter

---

## The Biggest Risk: Modifying Existing Code

The POC only creates files. This system modifies files that already have history, tests, and live users depending on them. The safeguard strategy:

1. **Always read before write** — executor must call `read_file` before `write_file` on any existing file
2. **Diff before commit** — `git diff` output reviewed at Gate 2 alongside the PR
3. **Never delete, only deprecate** — removed code moves to `_deprecated/` folder with a comment and date
4. **Backwards-compatible steps only** — the canonical plan must specify that each step leaves the system in a working state
5. **Rollback branch** — before each repo executor runs, a `backup/<timestamp>` branch is created automatically

---

## Open Questions to Resolve Before Building

1. **How do we handle Java?** The POC uses Python-only tools. Java repos need Maven/Gradle awareness. Do we shell out to `mvn` / `gradle`, or do we treat Java files as text only?
2. **Repo access** — the real repos need to be cloned or mounted. Where do they live relative to this project?
3. **ChromaDB namespacing** — one collection per repo, or one DB file per repo? (One DB per repo is simpler to manage and rebuild independently)
4. **Parallelism** — FE and BE executors can run in parallel if they don't share files. The dependency resolver needs to express this as a LangGraph `Send()` graph.
5. **Plan file format** — should the canonical plan be a structured YAML (machine-readable) or Markdown (human-readable)? Probably both: Markdown for Gate 1 review, YAML for executor parsing.
