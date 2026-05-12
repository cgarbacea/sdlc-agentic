---
tags: [feature, module structure, folder layout, barrel export, index.ts, self-contained, public API]
executor: fe
---

# Feature Module Structure

Every domain feature lives under `features/<feature-name>/` and follows this layout:

```
features/<feature-name>/
├── api/
│   └── <Feature>Service.ts      # HTTP service class
├── components/
│   ├── <ComponentName>/
│   │   ├── <ComponentName>.tsx
│   │   └── index.ts             # re-export
│   └── index.ts                 # barrel: export * from './<ComponentName>'
├── hooks/
│   ├── <domainName>Keys.ts      # TanStack Query key factory
│   ├── use<QueryName>.ts        # one hook per query/mutation
│   └── index.ts
├── schemas/
│   └── <feature>Schema.ts
├── stores/                      # (only if local UI state needed)
├── types/
│   └── index.ts                 # feature-local types
├── context/                     # (only if shared React context needed)
└── index.ts                     # barrel export — the feature's public API
```

## Barrel Export Pattern

```typescript
// features/<name>/index.ts
export * from "./components";
export * from "./hooks";
export { createMyEntitySchema } from "./schemas/myEntitySchema";
export type { CreateMyEntityFormData } from "./schemas/myEntitySchema";
```

```typescript
// features/<name>/components/index.ts
export { MyComponent } from "./MyComponent/MyComponent";
export { MyList } from "./MyList/MyList";
```

## Rules

- Features are **self-contained** — a feature never imports from another feature directly
- Cross-feature communication: `lib/stores/` (Zustand) or URL state only
- `index.ts` barrel is the only public surface — consumers import from the feature root
- Standalone domain capabilities (video, messaging) belong in `modules/` — not `features/`
- Reusable UI primitives belong in the design system (`libs/ui/`) — not `features/`
