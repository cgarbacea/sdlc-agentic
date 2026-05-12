---
tags: [component, isLoading, isError, design system, presentational, container, error state, loading state]
executor: fe
---

# Component Pattern

```tsx
// features/<name>/components/<ComponentName>/<ComponentName>.tsx
"use client"; // only if using hooks or browser APIs

import { Button, Text } from "@company/ui"; // project's design system
import { Trans } from "@lingui/react/macro";
import { useMyEntity } from "../../hooks/useMyEntity";

interface MyComponentProps {
  entityId: string;
  onSuccess?: () => void;
}

export function MyComponent({ entityId, onSuccess }: MyComponentProps) {
  const { data: entity, isLoading, isError, error } = useMyEntity(entityId);

  // Always handle all three states — never let isError render silently
  if (isLoading) return <div className="flex items-center justify-center p-24">...</div>;
  if (isError) return <div className="flex p-24 text-functional-error">{error?.message}</div>;

  return (
    <div className="flex flex-col gap-16 p-24">
      <Text variant="title-2" weight="strong">{entity?.name}</Text>
      <Button variant="solid" size="medium" onPress={onSuccess}>
        <Trans>Confirm</Trans>
      </Button>
    </div>
  );
}
```

## Styling Rules

- **Never** write custom CSS files or inline `style={{}}` props
- **Never** create new CSS class names — use design system utility classes only
- **Always** use design system components — check `libs/ui/` for what's available
- If you think you need custom CSS, you're looking in the wrong place — check the design system first

## Presentational vs Container Split

```tsx
// ❌ Mixed — hard to test
function PatientTable() {
  const { data: patients } = usePatients();
  return <table>...</table>;
}

// ✅ Split
function PatientsContainer() {
  const { data: patients, isLoading, isError } = usePatients();
  if (isLoading) return <Skeleton />;
  if (isError) return <ErrorMessage />;
  return <PatientTable patients={patients ?? []} />;
}
function PatientTable({ patients }: { patients: Patient[] }) {
  return <table>...</table>;
}
```
