# Career Plan — Technical Architect: AI-Native Enterprise Systems

**Goal:** Become a hands-on Technical Architect who can walk into a capital markets / enterprise client and immediately add value across all five pillars of the role — AI-Augmented SDLC, Modular Architecture, Autonomous Agent Design, Domain-Centric Design, and Governance.

**Starting point:** You have a working Python/LangGraph SDLC pipeline POC. You understand agents, RAG, HITL, and MCP. You are missing Java/Spring depth, formal DDD practice, and production-grade observability and governance tooling.

**Approach:** Build in public. Every phase produces a real artefact you can show — a GitHub repo, a demo, a blog post, an ADR log. Theory without artefacts doesn't land in interviews or client conversations.

---

## The Five Pillars You Must Own

| Pillar                                              | Weight in role | Current level          | Target                    |
| --------------------------------------------------- | -------------- | ---------------------- | ------------------------- |
| 1. AI-Augmented SDLC                                | Very high      | ★★★☆☆ (POC works)      | ★★★★★ (MCP + CI/CD wired) |
| 2. Modular Architecture (Spring Modulith, ArchUnit) | High           | ★☆☆☆☆ (no Java)        | ★★★★☆                     |
| 3. Autonomous Agent / API Design                    | High           | ★★★☆☆ (graph exists)   | ★★★★★ (MCP server live)   |
| 4. Domain-Centric Design (DDD, CQRS, Events)        | High           | ★★☆☆☆ (concepts known) | ★★★★☆                     |
| 5. Governance & Quality (ArchUnit, ADRs, templates) | Medium         | ★☆☆☆☆                  | ★★★★☆                     |

---

## Phase 0 — Consolidate What You Have (Weeks 1–2)

**Goal:** Make the existing POC production-presentable. Right now it is a script. By end of this phase it is a project someone can clone, run, and understand.

### Tasks

- [x] Clean up `main.py` — `argparse` with `--feature`, `--thread-id`, `--non-interactive` + structured logging
- [x] Write a proper `README.md` with: what it does, architecture diagram (Mermaid), how to run, what each node does
- [x] Add a `Makefile` with targets: `make run`, `make build-kb`, `make test`, `make ci-run`
- [x] Add `.env.example` (never commit real keys)
- [x] Add `pyproject.toml` with metadata, ruff config, pytest config
- [x] Add `tests/test_smoke.py` — 5 passing smoke tests (no LLM calls)
- [x] Pushed to https://github.com/cgarbacea/sdlc-agentic
- [x] Tag the repo `v0.1.0-poc`
- [ ] Screen recording (Loom, 3 mins) of the pipeline running end-to-end

### Why

A recruiter or client looking at the GitHub repo in 30 seconds should understand: this person built a multi-agent SDLC pipeline with HITL. If the repo looks like a scratch pad, the work is invisible.

### Artefacts

- Public GitHub repo with README, diagram, working demo
- A short screen recording (Loom, 3 mins) of the pipeline running end-to-end

---

## Phase 1 — Complete the HITL Gates (Weeks 3–5)

**Goal:** Implement Gate 1 (plan approval) properly in the CLI. This is the highest-leverage remaining feature — it demonstrates the most important production safety pattern.

### Tasks

- [x] Implement the interactive HITL loop in `main.py` — already done in POC
- [x] `_rewrite_plan_with_corrections()` — LLM rewrites plan cleanly on each round
- [x] `app.update_state()` correctly (state field: `architect_plan`)
- [x] `app.stream(None, config)` for the resume path
- [x] Swap `MemorySaver` → `SqliteSaver` — state persists to `.checkpoints/sdlc.db`, survives restarts
- [x] Tag `v0.2.0-hitl-gate1`

### Concepts you will solidify

- LangGraph checkpointing and state resumption
- The "rewrite, don't append" correction pattern
- Persistent workflow state management

### Artefact

- Screen recording of Gate 1: plan shown, human corrects it twice, plan rewritten, executors run with corrected plan

---

## Phase 2 — Build the MCP Server (Weeks 6–8)

**Goal:** Expose the pipeline as an MCP server so GitHub Copilot / Claude can call it as a tool. This is the single most impressive technical demo for the role — it is exactly what "MCP integrations to orchestrate AI-based tooling in CI/CD" means.

### Tasks

- [x] Install `mcp` Python SDK (FastMCP v1.27.0)
- [x] Create `mcp_server.py` with 4 tools: `start_pipeline`, `get_pipeline_state`, `approve_plan`, `list_threads`
- [x] Lazy pipeline loading — fast MCP handshake, model loads on first tool call
- [x] Logging to stderr only (MCP servers must not pollute stdout)
- [x] Register in `.vscode/mcp.json` — Copilot can call tools from this workspace
- [x] `Dockerfile` (multi-stage, non-root user) + `.dockerignore`
- [x] 5 MCP smoke tests — 12/12 passing total
- [x] Tag `v0.3.0-mcp-server`
- [ ] Screen recording: Copilot calls `start_pipeline` live (the "wow demo")

### Concepts you will solidify

- MCP protocol (stdio transport, tool schema, JSON-RPC)
- Async Python server patterns
- How AI clients discover and call tools

### Artefact

- Screen recording: ask GitHub Copilot in chat "build me a dark mode toggle feature", Copilot calls the MCP tool, pipeline runs, code appears in the monorepo
- This is your "wow demo" — record it cleanly, it goes in every application

---

## Phase 3 — Real Git + GitHub PRs (Weeks 9–11)

**Goal:** Replace the mocked git tools with real ones. The pipeline should commit to a feature branch and open a real GitHub PR. This closes the loop on the SDLC — the agent doesn't just write files, it ships them through the proper engineering workflow.

### Tasks

- [x] Replace mock `git_commit_to_branch` with real `gitpython` — creates branch, stages, commits
- [x] `create_github_pr` uses `PyGithub` — opens real PR when `GITHUB_ENABLED=True`, degrades gracefully to simulation when credentials not set
- [x] `GITHUB_ENABLED` flag — dual-mode design: never crashes without credentials
- [x] `config.py`: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_FE_REPO`, `GITHUB_BE_REPO`, `GITHUB_BASE_BRANCH`
- [x] `.env.example` documents all GitHub vars with setup instructions
- [x] `tests/test_git_tools.py`: 7 tests (offline, no GitHub API calls) — 19/19 total passing
- [ ] GitHub Actions workflow in target monorepo (runs tests on PR, posts results as comment)
- [ ] Webhook handler — triggers new LangGraph thread on "request changes" review
- [ ] Tag `v0.4.0-real-git`

### Concepts you will solidify

- Git branching strategy (feature branches, PR workflow)
- GitHub Actions basics
- Webhook-driven event architecture (async trigger → new agent thread)

### Artefact

- End-to-end demo: feature request → plan approved → code written → PR opened on GitHub → PR visible with files changed

---

## Phase 4 — Java / Spring Modulith Fundamentals (Weeks 12–18)

**Goal:** Build a minimal but real Spring Boot application using Spring Modulith and ArchUnit. This is the most important skill gap — the role is explicitly about Java/Spring architecture. You don't need to be a Spring expert; you need to understand the architectural patterns well enough to design and evaluate them.

### Why Java at all?

The requirements mention Spring Modulith, jMolecule, and ArchUnit by name. These are Java-specific. Capital markets firms run Java. Your AI pipeline tools (agents, MCP) are language-agnostic — but the systems they operate on are Java. To be a Technical Architect in this space, you need to understand the codebase your agents will generate and review.

### Learning path

**Week 12–13: Spring Boot baseline**

- Build a simple `OrderManagement` service: REST API, JPA entities, service layer
- Tools: Spring Initializr, IntelliJ/VS Code with Java extension, Maven
- Resource: [spring.io/guides](https://spring.io/guides) — "Building a RESTful Web Service" + "Accessing Data with JPA"

**Week 14–15: Spring Modulith — enforceable module boundaries**

- Restructure the OrderManagement service into Spring Modulith modules: `orders`, `inventory`, `payments`
- Rule: modules communicate only through published events, not direct bean injection
- Add `@ApplicationModuleTest` — verify module isolation in tests
- Resource: [spring.io/projects/spring-modulith](https://spring.io/projects/spring-modulith) — official docs + Juergen Hoeller's talks

**Week 16: ArchUnit — rules as code**

- Add ArchUnit dependency
- Write rules:
  - "No class in `inventory` may import from `orders`"
  - "All service classes must be in the `service` package"
  - "No direct Spring Data repo access from controllers"
- Run rules as JUnit tests — they break the build if violated
- Resource: [archunit.org/userguide](https://archunit.org/userguide/html/000_Index.html)

**Week 17–18: jMolecule — DDD language in code**

- Annotate entities with `@AggregateRoot`, `@Entity`, `@ValueObject`
- Add `@DomainEvent` to published events
- Add `@BoundedContext` to each module
- Run jMolecule ArchUnit rules — they enforce DDD conventions automatically
- Resource: [github.com/xmolecules/jmolecule](https://github.com/xmolecules/jmolecule)

### Tasks

- [x] Using real domain: `backend-modulith` (YOUPAGE platform BE) instead of toy `order-service`
- [x] Spring Boot 3.5.0 + Java 25 + Spring Modulith 1.4.11 scaffolded via start.spring.io
- [x] 3 modules: `users`, `workspaces`, `notifications` (hexagonal, event-driven)
- [x] pom.xml: ArchUnit 1.3.0 + jMolecules 2.0.0-RC1 added
- [x] `users/domain/`: User @AggregateRoot, UserStatus, UserRepository port (ThemePreference removed — not in FE contract)
- [x] Domain events: UserCreatedEvent (tenantId), UserDeactivatedEvent (@DomainEvent records)
- [x] Permission.java: 5 RBAC constants matching FE UserPermission enum exactly
- [x] Liquibase: 8 changesets — users, user_language_codes, user_certifications, user_specialties, thumbnails, RBAC tables, event_publication, phone_numbers
- [x] application.yml + application-local.yml (Keycloak JWT + local PostgreSQL)
- [x] Pushed to https://github.com/cgarbacea/backend-modulith
- [x] Keycloak 26.2 running on Docker port 8180 — realm youpage-dev, client admin-portal (PKCE), test user dev@youpage.com
- [x] PostgreSQL youpage_dev database created on localhost:5432, all 8 changesets applied
- [x] JpaUserRepository — Spring Data JPA adapter, tenant-aware queries
- [x] UserService — all use cases: createUser, getById, getByKeycloakId, updateProfile, deactivate etc.
- [x] UserController — 6 endpoints, X-Tenant-ID header, JWT @AuthenticationPrincipal, ProblemDetail errors
- [x] UserResponse — matches FE UserProfile TypeScript interface exactly (nested EmailInfo, PhoneInfo)
- [x] SecurityConfig — stateless JWT resource server, CSRF disabled
- [x] **Server starts and responds:**
    - `GET /actuator/health` → `{"status": "UP"}`
    - `GET /api/v1/users` → HTTP 401 (Keycloak JWT required)
    - `GET /actuator/modulith` → Spring Modulith module graph (users + shared)
- [ ] ArchUnit test suite (5+ rules enforced)
- [ ] Spring Modulith @ApplicationModuleTest (verify workspaces cannot import users.domain)
- [ ] `workspaces` module (domain + event listener for UserCreatedEvent)
- [ ] `notifications` module
- [ ] Tag `v1.0.0` on backend-modulith

### Artefact

- GitHub repo `order-service` with: architecture diagram, ArchUnit tests, jMolecule annotations, Spring Modulith module graph (auto-generated — Modulith can render this as a diagram)
- This repo is your "Java architecture portfolio piece"

---

## Phase 5 — Wire the AI Pipeline to the Java Service (Weeks 19–22)

**Goal:** The LangGraph pipeline's BE executor should be capable of generating code that respects Spring Modulith boundaries, jMolecule annotations, and ArchUnit rules. This is the "AI-native engineering" pillar made real.

### Tasks

- [ ] Update `prompts/be_executor.md` to include:
  - Spring Modulith module structure rules
  - jMolecule annotation requirements
  - "Do not cross module boundaries — use events via `ApplicationEventPublisher`"
- [ ] Add `docs/java_architecture_guidelines.md` to the RAG knowledge base — index the rules the BE executor must follow
- [ ] Add a post-generation step: run ArchUnit tests against generated code; if they fail, feed the failure back to the BE executor for a retry
- [ ] This creates a **feedback loop**: Agent generates code → ArchUnit validates → if fail, agent sees the error and tries again
- [ ] Tag `v0.5.0-java-aware`

### Concepts you will solidify

- Closing the code-generation loop with automated validation
- Using existing test frameworks as agent feedback signals
- LLM-compatible project structures (what the requirements call out explicitly)

### Artefact

- Demo: agent generates a new module for the Java service → ArchUnit runs → violations reported → agent fixes → clean build

---

## Phase 6 — Observability + Production Hardening (Weeks 23–26)

**Goal:** Make the system observable. A Technical Architect must be able to answer "how do I know the agents are working correctly in production?" This phase adds the instrumentation to answer that question.

### Tasks

**Python pipeline (LangGraph)**

- [ ] Add LangSmith tracing — every LLM call, tool call, and node transition is logged
- [ ] Add structured logging with `structlog` — JSON logs that can be ingested by Datadog/Splunk
- [ ] Add a health check endpoint (FastAPI, 3 lines) for the MCP server
- [ ] Add retry logic to all tool calls (exponential backoff, max 3 attempts)
- [ ] Add an escalation node: if QA fails 3 times, pause and alert a human rather than looping forever

**Java service**

- [ ] Add Spring Actuator — `/health`, `/metrics`, `/info` endpoints
- [ ] Add Micrometer metrics exported to Prometheus format
- [ ] Add distributed tracing with OpenTelemetry

### Artefact

- LangSmith dashboard screenshot showing a full pipeline run with timing per node
- Architecture diagram showing the observability stack

---

## Phase 7 — Golden Templates + Governance Framework (Weeks 27–30)

**Goal:** Package everything you've built into reusable templates that a team can adopt in one day. This is what "golden project templates optimised for AI-driven engineering teams" means in the requirements.

### Tasks

- [ ] Create a `cookiecutter` Python template for a new LangGraph agent project:
  - Pre-wired: RAG, HITL gates, MCP server, LangSmith tracing, structured logging
  - One command: `cookiecutter gh:your-username/sdlc-agent-template`

- [ ] Create a Maven archetype for a new Spring Modulith service:
  - Pre-wired: ArchUnit rules, jMolecule annotations, Actuator, OpenTelemetry, module test structure
  - One command: `mvn archetype:generate -DarchetypeArtifactId=spring-modulith-ddd`

- [ ] Write an ADR (Architectural Decision Record) template and 5 example ADRs documenting the decisions made in both projects

- [ ] Write a 2-page "LLM-Compatible Project Structure" guide: how to name things, structure folders, write docstrings, and organise modules so AI pair-programmers and agents get maximum context

### Artefact

- Two published templates (Python + Java) with READMEs
- ADR log with 5+ real decisions
- The "LLM-Compatible Project Structure" guide — this is a genuinely novel document that doesn't exist well anywhere; writing it positions you as someone who has thought deeply about this

---

## Phase 8 — The Portfolio Pitch (Weeks 31–32)

**Goal:** Assemble everything into a story a client or hiring manager can follow in 20 minutes.

### The narrative arc

> "I built an AI-native SDLC system from scratch. It takes a plain-English feature request and autonomously produces a plan, frontend code, backend code, tests, QA report, and infrastructure config — with human review gates at critical points. I then exposed it as an MCP server so any AI development tool can call it as a native capability. I built a companion Java service using Spring Modulith, ArchUnit, and jMolecule to demonstrate that the generated code respects enforced module boundaries and DDD conventions. Everything is observable, testable, and packaged as reusable templates a team can adopt in a day."

### Artefacts

- [ ] A 5-minute demo video covering the full loop: feature request → AI pipeline → PR opened → ArchUnit passes
- [ ] A technical blog post: "Building an AI-Native SDLC Pipeline with LangGraph, MCP, and Spring Modulith"
- [ ] A LinkedIn post with the Mermaid architecture diagram embedded
- [ ] A `portfolio.md` in the root of your main repo linking all repos, the demo video, and the blog post

---

## Timeline Summary

| Phase                      | Duration      | Key Artefact                              |
| -------------------------- | ------------- | ----------------------------------------- |
| 0 — Consolidate POC        | 2 weeks       | Presentable GitHub repo + README          |
| 1 — HITL Gate 1            | 3 weeks       | Working plan approval loop                |
| 2 — MCP Server             | 3 weeks       | Copilot calls the pipeline live           |
| 3 — Real Git + GitHub PRs  | 3 weeks       | PR opened from agent run                  |
| 4 — Java / Spring Modulith | 7 weeks       | `order-service` with ArchUnit + jMolecule |
| 5 — Wire AI to Java        | 4 weeks       | Agent generates Modulith-compliant code   |
| 6 — Observability          | 4 weeks       | LangSmith dashboard + Actuator metrics    |
| 7 — Golden Templates       | 4 weeks       | cookiecutter + Maven archetype + ADRs     |
| 8 — Portfolio Pitch        | 2 weeks       | Demo video + blog post + LinkedIn         |
| **Total**                  | **~32 weeks** | **Full role capability demonstrated**     |

32 weeks is 8 months. That is aggressive but achievable working 10–15 hours per week outside a day job, or 4–5 months full-time.

---

## Daily Practice (Every Day, 20 Minutes)

The biggest risk is stalling on Phase 4 (Java). The antidote is daily small practice:

- **Mon/Wed/Fri:** Read one section of the Spring Modulith or ArchUnit docs. Write one class. Commit it.
- **Tue/Thu:** Review one ADR from a real project (Netflix, Spotify engineering blogs). Write one sentence about what architectural decision it records and why.
- **Weekend:** One focused session of 2–3 hours on the current phase task.

Consistency beats intensity. 20 minutes daily compounds into fluency; 4-hour binge sessions once a month do not.

---

## The Skills You Will Have at the End

After completing all phases you will be able to:

1. **Demo live:** "Here is a pipeline that takes a feature request and ships a PR to a Spring Modulith service, with ArchUnit validation in the loop, all orchestrated through an MCP server callable from GitHub Copilot."

2. **Speak architecture:** Explain bounded contexts, module boundary enforcement, event-driven decoupling, and CQRS in concrete terms with code examples.

3. **Write governance:** Produce ArchUnit rule suites, ADR logs, and LLM-compatible project structure guides that a team can adopt.

4. **Mentor teams:** Show a developer how to set up LangSmith tracing, write an ArchUnit rule, or structure a LangGraph agent — from working code, not slides.

5. **Own the lifecycle:** From the initial domain model through generated code, automated validation, PR review, deployment observability, and retrospective ADR.

That is the full Technical Architect role. Everything in the requirements document maps to at least one phase above.

---

## What to Do This Week

Focus only on Phase 0. Open the POC repo and do three things:

1. Write the `README.md` with the Mermaid architecture diagram
2. Add `argparse` to `main.py`
3. Create the `Makefile`

Do not touch Java yet. Do not start the MCP server yet. Finish the foundation first. A clean, documented POC is worth more than 5 half-finished features.
