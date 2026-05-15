# How to Add a New Coding Language to the SDLC Agentic Pipeline

This guide is the practical playbook for adding any new programming language (for example Flutter/Dart, Kotlin, Swift, Go) to the pipeline without breaking existing FE/BE flows.

## 1) Decide the Integration Shape First

Pick one of these models before coding:

1. Replace an existing executor behavior for a specific stack (for example FE web vs FE mobile).
2. Add a new dedicated executor node (recommended for a new language).
3. Add a language-specific sub-flow behind an existing node.

Use a dedicated node when the language has unique lint/build/test gates or architecture rules.

## 2) Define the Minimum Language Contract

For each new language, define:

- Repository path env var (for example `FLUTTER_REPO_PATH`).
- Prompt file (for example `prompts/flutter_executor.md`).
- Node implementation (for example `nodes/flutter_executor.py`).
- Output field in state (for example `mobile_output`).
- RAG knowledge namespace under `docs/<language>/`.
- Validation command(s) and quality gates.

If any of these are missing, language support is incomplete.

## 3) Update Runtime Plumbing (Code-Level Checklist)

### Config and Tool Access

1. Add new repo path env vars in `config.py`.
2. Extend `ALLOWED_ROOTS` so executor `write_file` can write to the new repo.
3. Add optional GitHub repo vars if PR automation is required.

### State and Routing

1. Add language target fields to `state.py` (for example `frontend_stack`, `mobile_output`).
2. Make `architect_node` emit explicit target stack labels in the plan.
3. Add conditional routing in `graph.py` (for example web FE route vs Flutter route).

### Node and Prompt

1. Create new node by cloning the FE/BE executor pattern.
2. Wire tools needed by that node.
3. Add prompt with strict scope boundaries and search hints.
4. Keep existing FE/BE prompts unchanged unless search hints must be expanded.

### Tests and Documentation

1. Add node-level tests for routing behavior and skip conditions.
2. Update `README.md` graph and project structure.
3. Update `.env.example` with new env vars.
4. Add/refresh docs under `docs/plans/` for rollout tracking.

## 4) Add Knowledge Base Content Correctly

`search_company_knowledge_base` only indexes `./docs/**/*.md`.

Therefore:

1. Import language skills into `docs/<language>/` (do not leave them only under `guideline/skills/...`).
2. Normalize each file with concise rules and examples for retrieval.
3. Rebuild embeddings with `python build_knowledge_base.py`.
4. Validate retrieval using 5 to 10 representative queries.

If docs are not in `./docs`, the executors cannot retrieve them.

## 5) Language Quality Gates (Non-Negotiable)

For every language, define three gates:

1. Static analysis/lint gate
2. Unit/integration test gate
3. Build/compile gate

Add these gates to either:

- The language executor loop (preferred for immediate correction), or
- CI validation with hard fail.

## 6) Rollout Pattern (Safe)

1. Dry run in stub mode with new routing path enabled.
2. Real run in non-stub mode on one scoped feature.
3. Verify commit and PR automation.
4. Collect evidence pack (logs + outputs + QA report).
5. Expand to full language support after 2 to 3 successful runs.

## 7) PR Checklist Template (Copy/Paste)

- Added env vars and repo roots
- Added node + prompt
- Added graph routing
- Added state fields
- Added docs under `docs/<language>/`
- Rebuilt RAG DB
- Added tests for routing and executor behavior
- Updated README and `.env.example`
- Demonstrated one end-to-end run

## 8) Common Failure Modes

1. Adding prompt only, but no graph routing.
2. Adding skills under `guideline/skills`, but not importing to `docs`.
3. Forgetting `ALLOWED_ROOTS` update, causing write failures.
4. No language-specific validation gates.
5. Architect plan not declaring stack target, causing wrong executor selection.

## 9) Definition of Done for a New Language

Language support is done when:

1. Requirements/architect flow can signal the target stack.
2. Graph routes to the correct executor deterministically.
3. Executor can read/write/commit in the target repo.
4. Language docs are retrievable via RAG.
5. Quality gates run and can block bad output.
6. One full feature run completes with reproducible evidence.
