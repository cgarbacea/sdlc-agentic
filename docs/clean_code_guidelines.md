# Clean Code Guidelines

## General Principles

- Functions should do one thing only and do it well.
- Prefer explicit over implicit. Variable names must be descriptive.
- No magic numbers — use named constants.
- Keep functions under 30 lines. If longer, extract into helpers.
- Delete dead code instead of commenting it out.

## TypeScript / Frontend

- All React components must be functional components using hooks. No class components.
- Use TypeScript strict mode. No `any` types.
- All UI components must be wrapped in an error boundary.
- Use `react-query` for all data fetching. Never fetch data directly in a component.
- All forms must use `react-hook-form` with `zod` schema validation.
- Data grids must use the Ag-Grid library wrapped in our custom `<DataTable />` component.
- Styles must use Tailwind CSS utility classes. No inline styles.
- Component files must export a single default component.

## Python / Backend

- Use `FastAPI` for all API endpoints.
- All endpoints must have Pydantic request/response models.
- Use dependency injection via FastAPI's `Depends()` for shared resources (DB session, auth).
- All database access must go through a repository pattern. No raw SQL in route handlers.
- Use `httpx` for any external HTTP calls. Never use `requests` in async contexts.
- Errors must be raised as `HTTPException` with appropriate status codes.
- Environment variables must be loaded via a `Settings` class using `pydantic-settings`.

## API Design

- All endpoints must be versioned: `/api/v1/...`
- Use plural nouns for resources: `/api/v1/users`, not `/api/v1/user`.
- POST endpoints return `201 Created` with the created resource.
- DELETE endpoints return `204 No Content`.
- All list endpoints must support pagination via `?page=` and `?limit=` query params.
- CORS must be explicitly configured — never use wildcard `*` in production.

## Testing

- All new features must have unit tests with at least 80% coverage.
- Use `pytest` for backend and `vitest` for frontend.
- Integration tests must use a dedicated test database, never the development database.
- Mock all external HTTP calls in tests using `respx` (backend) or `msw` (frontend).

## Git & PR Standards

- Branch names must follow the pattern: `feat/<jira-ticket-id>-short-description`.
- Commit messages must follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`.
- Every PR must have a description referencing the Jira ticket.
- No PR may be merged without at least one approving review.
- Squash and merge only — no merge commits on `main`.
