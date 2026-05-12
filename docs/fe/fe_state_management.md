---
tags: [state, Zustand, React Query, store, stable selector, server state, client state, useStore]
executor: fe
---

# State Management Rules

## Two Types of State

| Type | Tool | When |
|---|---|---|
| Server state (API data) | TanStack Query | `useQuery` / `useMutation` |
| Client state (UI, auth, preferences) | Zustand | `useStore((s) => s.value)` |

## Rules

- **Server state**: TanStack Query only — never copy API data into a Zustand store
- **Client state**: Zustand stores in `lib/stores/` 
- Exception: auth store may hold tokens/user for middleware/cookie consumption — intentional
- Use stable Zustand selectors: `useStore((s) => s.value)` — never `useStore()` (whole store reference causes infinite re-renders on any state change)
- React Query cache is the source of truth for server data — Zustand for UI-only state

## Stable Selector Pattern

```typescript
// ✅ Correct — only re-renders when accessToken changes
const accessToken = useAuthStore((s) => s.accessToken);

// ❌ Wrong — re-renders on any store change
const { accessToken, user } = useAuthStore();
```
