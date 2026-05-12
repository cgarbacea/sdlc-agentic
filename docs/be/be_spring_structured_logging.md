---
tags: [logging, MDC, structured logs, correlation, JSON format, request ID, logstash, observability]
executor: be
---

# Structured Logging and Observability

## MDC Pattern

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderService {

    public Order create(UUID tenantId, CreateOrderCommand cmd) {
        MDC.put("tenantId", tenantId.toString());
        MDC.put("userId", cmd.userId().toString());
        try {
            log.info("Creating order: customerId={} itemCount={}", cmd.customerId(), cmd.items().size());
            var order = Order.create(tenantId, cmd);
            var saved = repository.save(order);
            log.info("Order created: orderId={}", saved.getId());
            return saved;
        } finally {
            MDC.clear(); // always clear — thread pool reuse means stale MDC leaks across requests
        }
    }
}
```

## Rules

- Use MDC (`org.slf4j.MDC`) to attach `tenantId`, `requestId`, `userId` at the request entry point — all downstream logs inherit the context automatically
- Always `MDC.clear()` in a `finally` block — thread pools reuse threads; stale MDC corrupts subsequent requests
- Log enough to reproduce the problem: entity IDs, operation name, key input parameters — not the full object
- Never log sensitive data: passwords, tokens, full request bodies containing PII
- Use JSON logging format in production (`logstash-logback-encoder` or equivalent) — log aggregators parse structured JSON, not plain text
- Add a correlation/request ID header (`X-Request-ID`) at the API gateway level and propagate it through MDC

## Log Levels

| Level | When |
|---|---|
| ERROR | Unexpected failures — requires immediate attention |
| WARN | Expected business rejections (invalid input, conflict) |
| INFO | Significant state changes (entity created, status changed) |
| DEBUG | Diagnostic detail — disabled in production |
