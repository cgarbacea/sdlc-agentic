---
tags: [distributed patterns, saga, cqrs, circuit breaker, outbox, resilience4j, eventual consistency]
executor: be
---

# Spring Distributed Patterns for Modulith and Services

These patterns apply when a feature crosses module or service boundaries and cannot be handled as a single local transaction.

## 1) Database Ownership and Data Boundaries

- One owner per data set: each module/service owns its write model.
- Never query another module/service private tables directly.
- Exchange data through APIs or domain/integration events.
- Schema evolution is owned by the module/service via migration scripts.

Inside a modulith, treat module boundaries with the same discipline as service boundaries.

## 2) Saga Pattern (Distributed Transaction Coordination)

Use saga when one business operation spans multiple local transactions.

Two styles:

- Choreography: services/modules react to events.
- Orchestration: one coordinator issues explicit commands.

Use choreography for simpler flows and loose coupling.
Use orchestration when ordering, timeout policy, and compensation logic are complex.

### Saga Rules

- Every step must be idempotent.
- Define compensation for each non-reversible side effect.
- Persist saga state or correlation identifiers for observability.
- Add timeouts and dead-letter handling for stuck workflows.

```java
public record UserCreatedEvent(UUID userId, UUID tenantId) {}
public record WorkspaceCreatedEvent(UUID workspaceId, UUID ownerUserId) {}
public record WorkspaceCreationFailedEvent(UUID userId, String reason) {}
```

## 3) CQRS (Command/Query Separation)

Use CQRS when read and write concerns have different scaling or modeling needs.

- Command side: validates invariants and writes aggregate state.
- Query side: optimized read projections and search views.
- Read model may be eventually consistent relative to writes.

When using event-driven projections:

- Version events explicitly (`UserProfileUpdatedV1`, `UserProfileUpdatedV2`).
- Keep projection handlers idempotent.
- Support projection replay from durable event history.

Do not introduce CQRS by default. Apply it when read complexity/performance justifies added operational cost.

## 4) Circuit Breaker for External Dependencies

Use circuit breakers for synchronous external calls to prevent cascading failures.

### Minimal Resilience4j Setup

```yaml
resilience4j:
  circuitbreaker:
    instances:
      identityService:
        failure-rate-threshold: 50
        slow-call-rate-threshold: 50
        slow-call-duration-threshold: 2s
        wait-duration-in-open-state: 10s
        minimum-number-of-calls: 5
        sliding-window-size: 10
```

```java
@CircuitBreaker(name = "identityService", fallbackMethod = "fallback")
public UserProfile fetchUserProfile(UUID userId) {
    return identityClient.fetch(userId);
}

private UserProfile fallback(UUID userId, Exception ex) {
    throw new ServiceUnavailableException("Identity service temporarily unavailable", ex);
}
```

### Circuit Breaker Rules

- Required for synchronous inter-service HTTP calls.
- Set strict client timeout lower than user-request timeout.
- Fallback must be semantic (cached data or explicit degradation), never silent success.
- Emit metrics/traces for state changes (closed/open/half-open).

## 5) Outbox and Reliable Event Delivery

When state changes and event publication must be atomic:

- Write domain state and outbox row in one local transaction.
- Relay publishes outbox rows to broker.
- Mark published rows idempotently.

Do not publish directly to broker from domain/application flow if delivery guarantees matter.

## 6) Communication Decision Guide

Use synchronous API + circuit breaker when:

- You need immediate response for user flow.
- You need strict request-time validation against external state.

Use asynchronous events when:

- Work is decoupled or eventual consistency is acceptable.
- Throughput and resilience are more important than immediate response.
- Consumers should evolve independently.

## 7) Observability Requirements

For every distributed flow include:

- Correlation id propagated in logs/events/HTTP headers.
- Metrics for success, failure, retry, timeout, and DLQ counts.
- Trace spans around external calls and event handlers.
- Audit-friendly event metadata (event id, occurred at, version, producer).

## Common Failure Modes

- Calling remote service inside a wide transaction.
- Missing idempotency in consumer handlers.
- No compensation path for partial saga failures.
- Circuit breaker missing on mandatory upstream dependency.
- Read model exposed as strongly consistent when it is eventual.

## See Also

- `be_spring_event_listener.md`
- `be_spring_messaging.md`
- `be_spring_archunit_rules.md`
- `be_spring_repository_port.md`
