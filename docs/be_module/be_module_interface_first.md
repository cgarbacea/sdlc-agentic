---
tags: [interface, core module, Try, Vavr, AutoCloseable, NonNull, interface-first, pure Java]
executor: be_module
---

# Interface-First Module Design

The `core` module defines **what** a capability does, not **how**. Implementations are swappable.

```java
// core/src/.../RulesExecutor.java
// Pure Java interface — zero Spring, zero JPA, zero Kafka imports
public interface RulesExecutor extends AutoCloseable {

    /**
     * Returns Try to force callers to handle failure explicitly — no unchecked exceptions.
     */
    Try<Set<Alert>> execute(@NonNull String parentEntityId, @NonNull EntityChange event);

    Try<Void> registerRule(@NonNull Rule rule);

    Try<Void> removeRule(@NonNull Rule rule);
}
```

## Why `Try<T>` Instead of Checked Exceptions

- Forces callers to handle failure at the call site — no `try/catch` chains
- Composable: `Try.flatMap()`, `Try.map()`, `Try.recover()`
- Makes failure modes visible in the type signature
- Use `io.vavr.control.Try` (Vavr library)

## Rules

- Core interfaces extend `AutoCloseable` when they hold resources (DB connections, thread pools)
- All methods return `Try<T>` or `Optional<T>` — never throw from interface implementations without wrapping
- `@NonNull` (Lombok or JSpecify) on all parameters — fail fast at boundaries
- Zero framework imports in the core module — only JDK + Vavr + Lombok
