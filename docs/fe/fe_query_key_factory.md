---
tags: [query key, React Query, TanStack, key factory, cache, invalidation, useQuery]
executor: fe
---

# Query Key Factory Pattern

```typescript
// features/<name>/hooks/<domainName>Keys.ts
import type { MyFilterParams } from "@/types/api";

export const myEntityKeys = {
  all: ["my-entities"] as const,
  lists: () => [...myEntityKeys.all, "list"] as const,
  filtered: (params: MyFilterParams) => [...myEntityKeys.all, "filter", params] as const,
  details: () => [...myEntityKeys.all, "detail"] as const,
  detail: (id: string) => [...myEntityKeys.details(), id] as const,
};
```

## Rules

- Always use a key factory — never inline string arrays in `useQuery` calls
- `as const` on the base array ensures TypeScript infers literal types
- Hierarchical structure enables targeted invalidation: `invalidateQueries({ queryKey: myEntityKeys.all })` clears everything
- One key factory per domain — lives in `hooks/<domainName>Keys.ts`
