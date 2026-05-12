---
tags: [hook, useQuery, useMutation, error state, isError, React Query, TanStack, toast]
executor: fe
---

# Hook Pattern

```typescript
// features/<name>/hooks/useMyEntity.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { myFeatureService } from "../api/MyFeatureService";
import { myEntityKeys } from "./myEntityKeys";

export function useMyEntity(id: string) {
  return useQuery({
    queryKey: myEntityKeys.detail(id),
    queryFn: () => myFeatureService.getEntity(id),
    enabled: Boolean(id),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateMyEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (req: CreateMyEntityRequest) => myFeatureService.createEntity(req),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: myEntityKeys.lists() });
    },
    // Toast notifications are the responsibility of the consuming component, not the hook
  });
}
```

## Rules

- Hooks return the raw React Query result — they do not catch errors or show toasts
- Toast/error display is the responsibility of the component that calls the hook
- Zustand store updates (e.g. syncing auth state) done in `useEffect` watching `query.data`
- One hook per query/mutation — not one hook per feature
- Always destructure `isLoading`, `isError`, `error` in the consuming component — never ignore them
