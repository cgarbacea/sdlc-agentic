---
tags: [Zod, schema, validation, form, i18n error messages, factory, API response]
executor: fe
---

# Zod Schema Pattern

## Form Schema (with i18n error messages)

```typescript
// features/<name>/schemas/<feature>Schema.ts
import { z } from "zod";

export const createMyEntitySchema = (ctx: { required: string; tooShort: string }) =>
  z.object({
    name: z.string().min(2, ctx.tooShort).max(100),
    description: z.string().optional(),
  });

export type CreateMyEntityFormData = z.infer<ReturnType<typeof createMyEntitySchema>>;
```

## API Response Schema (plain)

```typescript
export const myEntitySchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  status: z.enum(["ACTIVE", "INACTIVE"]),
  createdAt: z.string().datetime(),
});
```

## Rules

- Schemas needing translated error messages are factories accepting message strings
- Schemas for API response validation are plain `z.object({...})`
- Export both the schema and the inferred type
- Cross-feature schemas live in `schemas/` at the app level, not inside a feature
