from langchain_core.messages import HumanMessage

from config import FE_REPO_PATH, BE_REPO_PATH, CURRENT_DATE
from llm_factory import get_llm, is_stub_mode, get_provider_name
from state import SDLCState


def _build_stub_architect_plan(state: SDLCState) -> str:
    feature = state.get("user_request", "").strip()
    requirements = state.get("requirements", "").strip()
    return f"""## 1. Overview
This feature delivers: {feature}. This architecture plan was generated in stub mode and should be refined in Gate 1 before execution.

## 2. Backend - What to Build
- Endpoint: Define one primary endpoint supporting this feature.
- Request fields: Capture all required user input fields from requirements.
- Response fields: Return a success payload and stable identifier fields.
- Auth: Apply existing authenticated user policy.
- Error cases: Return validation, authorization, and server error responses.

## 3. Frontend - What to Build
- Page/route: Add a route matching existing routing conventions.
- Components: Create one page container and focused presentational components.
- Form fields: Mirror backend request fields and validation constraints.
- API integration: Create a service class and one hook for read/write operations.
- State: Keep server state in React Query and UI-only state in existing client store.

## 4. FE <-> BE Communication
- Request format: JSON body aligned with validated input fields.
- Response format: JSON containing data fields needed for rendering and status display.
- Token handling: Use current auth token flow in client HTTP layer.
- CORS: No special handling unless route is served from a different origin.

## 5. Error Handling Strategy
- Backend returns structured error payload with code and message.
- Frontend maps validation errors to field feedback and generic errors to a user-visible alert.

## 6. Open Questions / Risks
- Confirm final request/response field list with product requirements.
- Confirm whether this is frontend-only or requires backend persistence.

### Requirements Snapshot
{requirements}
"""


def architect_node(state: SDLCState) -> SDLCState:
    """
    Phase 2 — Architecture Plan.

    Produces a structured architectural plan describing WHAT to build:
    - API contracts (endpoint paths, request/response shapes as prose or tables)
    - Component names and responsibilities
    - Data models (field names and types — prose, not code)
    - FE ↔ BE communication protocol
    - Auth and error handling decisions

    STRICT RULE: This plan contains NO code examples.
    Code is written by the executor nodes using the knowledge base.
    """
    print("\n🏛️  [Architect] Writing architectural plan...")

    if is_stub_mode():
        print(
            f"   ↳ [Architect] Stub mode active (provider={get_provider_name()}).")
        return {"architect_plan": _build_stub_architect_plan(state)}

    llm = get_llm(temperature=0.1)
    try:
        plan_response = llm.invoke([HumanMessage(content=f"""
You are the Lead Architect. Your job is to write an architectural plan for the development team.

Feature requirements:
\"\"\"
{state['requirements']}
\"\"\"

Today's date is {CURRENT_DATE}.
Frontend repository path: {FE_REPO_PATH}
Backend repository path: {BE_REPO_PATH}

Write a structured architectural plan with the following sections:

## 1. Overview
One paragraph. What this feature does and which systems are involved.

## 2. Backend — What to Build
- Endpoint: method + path (e.g. POST /api/v1/users/search)
- Request fields: name, type, required/optional, validation rule — as a table
- Response fields: name, type — as a table
- Auth: required role/scope
- Error cases: list the HTTP status codes and conditions

## 3. Frontend — What to Build
- Page/route: path and file location
- Components to create: name and single-sentence responsibility for each
- Form fields: name, type, validation rule — as a table
- API integration: which service class and hook to create (names only)
- State: which state is server-state (React Query) vs client-state (Zustand)

## 4. FE ↔ BE Communication
- Request format: describe the JSON shape in prose or a field table
- Response format: describe the JSON shape in prose or a field table
- Token handling: describe how auth token flows (prose only)
- CORS: any special requirements

## 5. Error Handling Strategy
- What the BE returns for each error case
- How the FE surfaces each error to the user

## 6. Open Questions / Risks
List any assumptions made and risks the team should be aware of.

---

CRITICAL CONSTRAINT: Do NOT write any code. No TypeScript, no Java, no YAML, no JSON examples.
Describe everything in prose, tables, or bullet points.
The development team will write the code — your job is to tell them what to build and why.
""")])
    except Exception as exc:
        print(
            f"   ⚠️ [Architect] LLM call failed ({exc}). Falling back to stub mode.")
        return {"architect_plan": _build_stub_architect_plan(state)}

    architect_plan = plan_response.content if isinstance(
        plan_response.content, str) else ""

    return {"architect_plan": architect_plan}
