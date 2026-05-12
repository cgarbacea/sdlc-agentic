---
tags: [record, Builder, toBuilder, domain type, immutable, Instant, Lombok, value type]
executor: be_module
---

# Domain Type Patterns

```java
// core/src/.../Rule.java — immutable value type with builder
@Builder
public record Rule(
        UUID ruleId,
        String tenantId,
        String code,
        String version,
        String definition,
        SeverityLevel severity,
        Short priority,
        String outputTopic,
        Integer throttleMs,     // nullable — null means "use system default"
        Instant effectiveFrom,
        Instant effectiveTo,
        Instant createdAt,
        Instant updatedAt
) {}

// toBuilder() for creating modified copies
@Builder(toBuilder = true)
public record Alert(
        UUID alertId,
        String tenantId,
        SeverityLevel severity,
        String message,
        String parentEntityId,
        Instant createdAt,
        UUID ruleId,
        String ruleCode,
        String ruleVersion,
        String outputTopic,
        Integer throttleMs,     // null means use system default
        Instant ruleUpdatedAt   // tracks rule changes to reset throttle state
) {}
```

## Rules

- Domain types are Java `record` — immutable, equals/hashCode/toString for free
- `@Builder` for construction; `@Builder(toBuilder = true)` when you need modified copies
- Comment record components that have non-obvious semantics
- Nullable fields documented inline: `// null means use system default`
- `Instant` for all timestamps — never `Date` or `LocalDateTime` (no timezone ambiguity)
