---
tags: [domain event, cross-module, NamedInterface, events package, DomainEvent, jMolecules, Spring Modulith]
executor: be
---

# Domain Event Pattern

## Event Record

```java
// <module>/events/MyEntityCreatedEvent.java
@DomainEvent  // jMolecules
public record MyEntityCreatedEvent(UUID entityId, UUID tenantId, String name) {
    // Java record: immutable, auto-generated equals/hashCode/toString
    // Payload contains only primitive/value types — never domain entity references
}
```

## Package Declaration

```java
// <module>/events/package-info.java
@NamedInterface("events")  // Spring Modulith — declares this package as the public API surface
package com.company.service.mymodule.events;

import org.springframework.modulith.NamedInterface;
```

## Rules

- Event payloads use only primitives, `UUID`, `String`, `Instant` — never domain entity references
- The `events/` package is the **only** thing another module may import from this module
- `@NamedInterface("events")` must be declared in `package-info.java` — Spring Modulith enforces this
- Events are Java records — immutable, equals/hashCode/toString for free
- Version events explicitly when the schema changes: `UserCreatedEventV2`
