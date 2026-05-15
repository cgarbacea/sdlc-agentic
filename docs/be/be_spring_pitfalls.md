---
tags: [spring, pitfalls, anti-patterns, performance, transactions, kafka, concurrency, modulith, oome]
executor: be
---

# Spring Boot Pitfalls and Anti-Patterns

Use this as a pre-implementation checklist for things to avoid. These rules are intentionally defensive and complement the positive patterns in the rest of the backend knowledge base.

## Module Boundary Pitfalls

- Do not import another module's `domain` or `application` package directly.
- Cross-module calls must go through published events (`events` package / named interface), never direct bean wiring.
- Do not place event classes inside `domain` if they are consumed cross-module.
- Avoid circular module dependencies. If module A and B need each other, extract a shared contract or convert one side to an event listener.

## Transaction Pitfalls

- Do not perform external I/O (HTTP, email, Kafka publish) inside a long-running `@Transactional` block.
- Keep transaction scope small and deterministic.
- Never publish to an external broker directly from domain logic while the DB transaction is still open. Use outbox + relay.
- Avoid transaction methods that process huge batches in one unit of work.

```java
// Anti-pattern: long transaction + network I/O
@Transactional
public void processPayment(Payment payment) {
    repository.save(payment);
    notificationClient.sendReceipt(payment.id()); // external I/O inside transaction
}
```

## Data Access Pitfalls

- Never call `findAll()` on unbounded tables for user-facing endpoints.
- Always enforce pagination with a hard max page size.
- Watch for N+1 queries on collection access. Use fetch joins or projections.
- Never rely on `ddl-auto=update` in production. Use Liquibase migrations.
- Add indexes for frequent `WHERE`, `ORDER BY`, and join columns.

## Memory and Throughput Pitfalls

- Do not load large files fully into memory. Stream them.
- Do not build huge strings in loops with `+`; use `StringBuilder`.
- Always use try-with-resources for files, streams, and clients.
- Do not keep large in-memory collections where paged iteration is possible.

## Concurrency Pitfalls

- Avoid mutable shared state in singleton beans.
- Use optimistic locking (`@Version`) for concurrent aggregate updates.
- Configure timeout for pessimistic locking to avoid deadlock hangs.
- For highly concurrent counters or registries, use thread-safe primitives.

## Reactive and Threading Pitfalls

- Never block event-loop threads in reactive flows.
- If blocking is unavoidable, explicitly offload to `Schedulers.boundedElastic()`.
- Prefer reactive clients (`WebClient`) in reactive code paths.
- Avoid `Thread.sleep()` in production retry logic; use scheduled or reactive delay.

## Kafka and Messaging Pitfalls

- Do not enable auto-commit for critical business consumers.
- Every consumer must be idempotent (dedupe by event id / business key).
- Do not retry deserialization or validation failures as if they were transient.
- Always configure DLT handling with alerting, not just logs.
- Never couple external event schemas to internal domain object shape.

## Spring Framework Pitfalls

- Prefer constructor injection over field injection.
- Keep configuration externalized; no hardcoded hosts, URLs, secrets, or timeouts.
- Keep active configuration clean; remove dead commented properties.
- Avoid overusing `@Component` for stateless utility classes.

## Pre-Commit Self-Check

1. Any cross-module import into `domain` or `application`? If yes, redesign.
2. Any endpoint returning unbounded lists? If yes, paginate.
3. Any external I/O inside transactions? If yes, split the flow.
4. Any consumer without idempotency + DLT strategy? If yes, fix before merge.
5. Any blocking call in reactive code? If yes, replace or offload.

## See Also

- `be_spring_archunit_rules.md`
- `be_spring_event_listener.md`
- `be_spring_jpa_n_plus_one.md`
- `be_spring_messaging.md`
- `be_spring_pagination.md`
