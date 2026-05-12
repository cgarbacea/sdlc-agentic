---
tags: [versioning, API version, deprecation, Sunset header, breaking change, v1, v2]
executor: be
---

# API Versioning Strategy

All endpoints are versioned from day one. Versioning after the fact is painful.

## Pattern

```java
// All endpoints live under /api/v1/
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController { ... }

// Breaking change: new version, old version kept in parallel during transition
@RestController
@RequestMapping("/api/v2/orders")
public class OrderV2Controller { ... }
```

## Breaking vs Non-Breaking Changes

**Requires a new version:**
- Removing or renaming a field in the response
- Changing a field's type
- Removing an endpoint
- Making an optional field required

**Does NOT require a new version:**
- Adding a new optional field to the response
- Adding a new endpoint
- Adding a new optional query parameter

## Rules

- All public endpoints versioned under `/api/v{n}/` from the first commit — never `/api/` unversioned
- Deprecate before removing: add `Deprecation` + `Sunset` response headers to inform clients
- Keep the previous version alive for at least one release cycle after announcing deprecation
- Internal endpoints (service-to-service) may use `/internal/` prefix without strict versioning
