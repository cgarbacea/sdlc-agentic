# Agentic SDLC — Stakeholder Briefing

**"We are not replacing our engineers. We are giving them a superpower."**

---

## The Problem We Are Solving

Every software team faces the same invisible tax. Before a single line of code is written, your senior engineers spend hours — sometimes days — on work that follows a pattern they have done hundreds of times before:

- Writing the PRD from scratch after a 30-minute brief
- Creating Jira tickets and estimating effort
- Setting up boilerplate files and folder structures
- Writing the first draft of unit tests
- Configuring Dockerfiles that look nearly identical to the last project

This is not creative work. It is **pattern-matching work** — and it is consuming the most expensive hours of your most experienced people.

The result: your Lead Engineers spend 30–40% of their sprint on scaffolding, not on the hard problems only they can solve.

---

## What We Have Built

We have built an **AI-powered development assistant** — a system of specialised agents that handles the repetitive, pattern-driven phases of the Software Development Life Cycle automatically, while your engineers remain in full control of every decision that matters.

Think of it as a highly capable, never-tired junior team that works overnight and hands your senior engineers a fully structured, reviewed, and documented starting point every morning.

### What it does in a single run:

1. Takes a plain-English feature description — the same 2-3 sentences your Product Analyst already writes in Slack
2. Writes and publishes a structured PRD to Confluence
3. Creates and assigns Jira tickets for the Frontend and Backend teams
4. Writes the initial frontend and backend code directly into your monorepo folders
5. Writes the first draft of unit and integration tests
6. Runs an automated quality review against your team's own coding guidelines
7. Generates the Dockerfile and docker-compose configuration

All of this — from feature description to reviewed, tested, deployable scaffold — **in under 15 minutes**.

---

## The Human Is Always in Charge

This is not autonomous AI. This is **AI with mandatory human checkpoints**.

We have designed **seven checkpoints** across the workflow where your engineers review, correct, or explicitly approve before anything moves forward. Two of these are foundational gates that every run passes through. Five are safety valves that activate only when they are needed.

### Gate 1 — The Strategy Gate: Before any code is written

After the AI produces the PRD, architecture plan, and Jira tickets, **the workflow pauses**. Your Lead Engineer reads the plan, corrects anything that is wrong or missing, and only then approves it. The AI codes exactly what the human approved — nothing more.

> _"Add a rate-limiting column to the User table."_ — the engineer types this correction, the AI incorporates it, and every downstream file reflects it automatically.

### Gate 2 — The Quality Gate: Before anything merges

After the AI writes the code, it opens a real GitHub Pull Request — the same PR your team already reviews today. Your senior engineers review the diff, leave comments, and approve or reject as they always have. If changes are requested, the AI reads the comments and pushes a new commit. The human merges.

**No AI-generated code reaches production without a human approving it.**

### Gate 3 — The Loop Breaker: When the AI gets stuck

If the AI fails its own automated quality check more than five times in a row, it stops trying and escalates to the engineer: _"I cannot resolve this error. Here is what I know. What should I do?"_ The engineer provides a one-line hint and the AI continues. This prevents runaway loops and ensures a human is never surprised by an agent silently burning time.

### Gate 4 — The Infrastructure Gate: Before any cloud change

Any action that touches cloud infrastructure — AWS, Kubernetes, IAM permissions, environment secrets — is blocked until your DevOps engineer explicitly types `yes`. The AI proposes the change and explains it. Nothing is applied until a human approves it. A misconfigured cloud resource is irreversible; this gate ensures it never happens without eyes on it.

### Gate 5 — The Visual Gate: Before any UI reaches users

After the frontend code is written, the system automatically deploys it to a temporary private preview URL and sends it to your engineer: _"Here is what it looks like. Approve the layout or describe what to change."_ Automated tests can verify a button exists. They cannot tell you it is the wrong colour, too small on mobile, or visually broken. Human eyes catch what tests cannot.

### Gates 6 & 7 — Async and webhook-driven (production)

Once in production, the PR review cycle (Gate 2) extends to include automatic re-triggering when an engineer leaves a review comment on GitHub — the AI reads the comment, applies the fix, and pushes a new commit without anyone having to restart a process. Auto-merge on approval, deploy to staging, and a full audit trail of every decision are included.

**Every gate is a conversation, not a blocker. The AI does the work. The human makes the call.**

---

## The Value

### Time saved per feature

| Activity                  | Today (manual) | With AI assistant |
| ------------------------- | -------------- | ----------------- |
| PRD + Jira tickets        | 2–4 hours      | 3 minutes         |
| Boilerplate code scaffold | 3–6 hours      | 8 minutes         |
| First-draft unit tests    | 2–4 hours      | 5 minutes         |
| Dockerfile + compose      | 1–2 hours      | 4 minutes         |
| **Total per feature**     | **8–16 hours** | **~20 minutes**   |

For a team shipping 2 features per sprint, this recovers **16–32 senior engineer hours per sprint** — time that moves directly into architecture decisions, performance work, security hardening, and the complex problems that actually require expertise.

### Cost

|                            | POC (today)         | Full production                |
| -------------------------- | ------------------- | ------------------------------ |
| Infrastructure             | MacBook, local only | Cloud hosting (~$50–200/month) |
| AI API cost per feature    | ~$0.10–0.50         | ~$0.50–2.00                    |
| Engineering time to set up | Done                | 4–6 weeks to production        |

At current pricing, running the full pipeline for a medium-complexity feature costs **less than a cup of coffee**. The break-even point against one hour of senior engineer time is reached on the very first run.

---

## What This Is Not

**It is not a replacement for your engineers.**

The AI cannot make product decisions. It does not understand your users. It cannot debug a subtle race condition at 2am. It does not know when a technically correct solution is the wrong business decision. It has no intuition about technical debt. It cannot run a sprint retrospective.

What it does is remove the work that does not require those capabilities — so the people who have them spend more time using them.

---

## Your Team, Enhanced

The same 6–7 person Scrum team you run today still runs the project end to end. The roles do not change. The accountability does not change. What changes is **how much of their day is spent on work that matches their level**.

### The Scrum Team — Roles and How They Are Enhanced

| Role                                   | What they do today                                                  | What changes with AI                                                                                                                                                                                                     |
| -------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Product Owner / Product Analyst**    | Writes feature briefs, manages backlog, defines acceptance criteria | Their 2-sentence Slack message becomes the input to the system. PRD and Jira tickets are drafted instantly for their review — they edit and approve rather than write from scratch.                                      |
| **Lead Engineer / Tech Lead**          | Reviews architecture, defines standards, mentors the team           | Reviews the AI's architecture plan at Gate 1 before any code is written. Their approved plan is what gets built. Their coding standards are baked into the AI's knowledge base — every agent follows them automatically. |
| **Senior Frontend Engineer**           | Designs and implements UI, owns the FE codebase                     | Reviews and improves generated React/TypeScript code in a PR rather than writing boilerplate from scratch. Spends their hours on UX complexity, performance, and the edge cases that require taste and experience.       |
| **Senior Backend Engineer**            | Designs APIs, owns data models and business logic                   | Reviews generated FastAPI endpoints and data models. Focuses on security, edge cases, and performance — not on writing the 40th CRUD endpoint of their career.                                                           |
| **QA Engineer**                        | Writes test plans, finds bugs, ensures quality                      | The AI writes the first draft of unit and integration tests. The QA Engineer reviews, extends, and improves them — and focuses their manual testing effort on exploratory and user-journey testing.                      |
| **DevOps / Infrastructure Engineer**   | Manages CI/CD, Dockerfiles, cloud infrastructure                    | Reviews generated Dockerfiles and compose files. All cloud and infrastructure changes are blocked until they explicitly approve them — Gate 6 ensures nothing touches production infrastructure without their sign-off.  |
| **Scrum Master / Engineering Manager** | Facilitates sprints, removes blockers, tracks delivery              | Sprint velocity improves. Less time is spent on "why isn't the scaffold ready yet" conversations. More time is available for planning, process improvement, and the work that actually moves the team forward.           |

---

## The Ask

We are not asking for a budget to replace anyone. We are asking for **4–6 weeks of engineering time** to move from this working proof-of-concept to a production-ready system that every engineer on the team uses every sprint.

The return on that investment is measurable from week one — in hours recovered, in features shipped faster, and in senior engineers spending their time on the work that made you hire them.

---

## Summary

|                                                   | Before                     | After                                  |
| ------------------------------------------------- | -------------------------- | -------------------------------------- |
| Time from feature brief to reviewed code scaffold | 1–2 days                   | Under 1 hour                           |
| Who approves the plan                             | —                          | Your Lead Engineer (Gate 1)            |
| Who approves the code                             | Your engineers (PR review) | Your engineers (PR review) — unchanged |
| Who owns the codebase                             | Your engineers             | Your engineers — unchanged             |
| Risk of AI error reaching production              | —                          | Zero — no merge without human approval |
| Cost per feature                                  | Senior engineer hours      | ~$0.50–2.00 in API costs               |

**The same team. The same standards. Dramatically more output — on the work that matters.**
