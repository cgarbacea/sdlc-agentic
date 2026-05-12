---
tags: [pagination, cursor, offset, Pageable, PageableDefault, unbounded list, Page, totalElements]
executor: be
---

# Pagination Patterns

Never return unbounded lists from API endpoints. Always paginate.

## Offset Pagination

```java
@GetMapping
public Page<MyEntityResponse> list(
        @RequestHeader("X-Tenant-ID") UUID tenantId,
        @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable) {
    return service.list(tenantId, pageable).map(MyEntityResponse::from);
}
```

## Pattern Comparison

| Pattern | When to use | Tradeoff |
|---|---|---|
| **Offset** (`page=0&size=20`) | Admin tables, known dataset | Simple but slow on large offsets; records can shift between pages |
| **Cursor** (opaque token) | Infinite scroll, large datasets, real-time data | Consistent; no count query; cannot jump to arbitrary page |

## Rules

- Use `@PageableDefault` on every list endpoint — never return all records with no `Pageable`
- Default page size ≤ 50 — protect against accidental full-table requests
- Expose `totalElements` and `totalPages` from `Page<T>` — clients need them for pagination UI
- Use cursor-based pagination when the dataset can exceed 10,000 rows or when real-time consistency matters
- Never use `findAll()` without `Pageable` in a controller-facing service method
