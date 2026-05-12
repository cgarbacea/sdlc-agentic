---
tags: [page, route, Next.js, App Router, Server Component, thin shell, metadata, i18n route]
executor: fe
---

# Page / Route Pattern

```tsx
// app/[lng]/<feature>/page.tsx
import type { Metadata } from "next";
import { MyFeaturePage } from "@/features/my-feature/components/MyFeaturePage";

export const metadata: Metadata = { title: "My Feature" };

export default function Page() {
  return <MyFeaturePage />;
}
```

## Rules

- Pages are thin shells — all logic lives in the feature module
- Server Components by default — add `'use client'` only when hooks or browser APIs are required
- If the project uses i18n route segments (e.g. `[lng]`), confirm the convention from existing pages before creating new routes
- `export const metadata` for SEO — every page should have a title
- The page file should be ≤ 15 lines — if longer, move logic to a feature component
