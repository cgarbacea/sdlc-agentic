---
tags: [react, nextjs, performance, waterfalls, bundle, rendering, rerender, cache, suspense]
executor: fe
---

# React and Next.js Performance Rules

This is a focused rule set for high-impact frontend performance decisions. Use these rules before adding new data fetching, components, or heavy dependencies.

## Priority 1: Eliminate Async Waterfalls

1. Start independent async work in parallel with `Promise.all`.
2. Do cheap synchronous checks before awaiting remote calls.
3. Await as late as possible and only in branches that require the value.
4. Use Suspense boundaries to stream partial UI instead of blocking the whole page.
5. In API routes and server actions, start promises early and gather late.

```ts
// Good: parallel fetching
const [profile, settings] = await Promise.all([getProfile(userId), getSettings(userId)]);
```

## Priority 2: Bundle Size Control

6. Avoid barrel imports on hot paths; import from concrete module paths.
7. Use dynamic imports for heavy/rarely used UI.
8. Defer analytics and non-critical third-party scripts until after hydration.
9. Load modules conditionally for feature-gated flows.
10. Preload likely-next resources on hover/focus.

```tsx
const HeavyChart = dynamic(() => import("./HeavyChart"), { ssr: false });
```

## Priority 3: Server-Side Throughput

11. Use request-scoped deduplication (`cache`) for repeated identical server calls.
12. Keep server mutable state out of module scope.
13. Minimize serialized data crossing server-to-client component boundaries.
14. Hoist static I/O and constants to module level where safe.
15. Parallelize nested fetches when item-level dependencies allow it.

## Priority 4: Client Fetching Discipline

16. Use TanStack Query/SWR deduping; avoid manual duplicate fetches.
17. Set explicit stale times and retry policy per query criticality.
18. Handle loading and error states explicitly for every query.
19. Keep browser storage payloads versioned and minimal.
20. Deduplicate global listeners and mark scroll/touch listeners as passive when possible.

## Priority 5: Re-render Control

- Avoid inline component definitions inside render functions.
- Use stable selectors for state stores to prevent broad rerenders.
- Move expensive pure computation to memoized boundaries.
- Use functional state updates for callback stability.
- Derive simple booleans in render instead of syncing them through effects.

## Priority 6: Rendering Efficiency

- Use `content-visibility` for long, scroll-heavy content sections.
- Hoist static JSX and config objects where possible.
- Prefer transition APIs for non-urgent updates to keep input responsive.
- Keep SVGs optimized (precision/size), especially icon-heavy views.

## PR Review Checklist

1. Did we introduce any sequential waits that could run in parallel?
2. Did we increase client bundle for a low-frequency interaction?
3. Are query keys and cache policies explicit and consistent?
4. Are loading/error/empty states all handled?
5. Did we add any rerender hotspots (broad store subscriptions, unstable props)?

## See Also

- `fe_query_key_factory.md`
- `fe_service_class.md`
- `fe_component_pattern.md`
- `fe_state_management.md`
- `fe_hook_pattern.md`
