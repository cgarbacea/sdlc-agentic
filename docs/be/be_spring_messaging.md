---
tags: [Kafka, messaging, consumer, outbox, broker, idempotency, DLQ, RabbitMQ, SQS, transactional outbox]
executor: be
---

# Inter-Service Messaging Patterns

## Two Levels of Communication

**Level 1 — In-Process (same service):** `@ApplicationModuleListener` (see `be_spring_event_listener.md`)

**Level 2 — Cross-Service:** Message broker (Kafka, RabbitMQ, AWS SQS/SNS, Azure Service Bus)

Always verify what broker the project uses — check `pom.xml` for `spring-kafka`, `spring-amqp`, or cloud-specific starters.

## Outbound — Transactional Outbox

```java
@Transactional
public Order create(CreateOrderCommand cmd) {
    var order = Order.create(cmd.customerId(), cmd.items());
    var saved = repository.save(order);
    // Publish in-process event — outbox relay forwards to external broker
    internalBus.publishEvent(new OrderCreatedEvent(saved.getId(), saved.getCustomerId()));
    return saved;
}
```

Never publish directly to the broker inside `@Transactional`. Write the event to the outbox table in the same transaction; a relay forwards it to the broker.

## Inbound — Thin Consumer

```java
// infrastructure/messaging/<Name>EventConsumer.java
@Component
@RequiredArgsConstructor
@Slf4j
public class PaymentEventConsumer {

    private final OrderService orderService;

    @KafkaListener(topics = "payments.completed", groupId = "${spring.kafka.consumer.group-id}")
    public void onPaymentCompleted(PaymentCompletedMessage message) {
        log.info("Received PaymentCompletedMessage: orderId={}", message.orderId());
        orderService.markAsPaid(message.orderId(), message.paymentId());
    }
}
```

## Rules

- Consumer classes live in `infrastructure/messaging/` — adapters, not business logic
- Always handle idempotency — broker may deliver the same message more than once
- DLQ must be configured — unconsumed messages must not silently disappear
- External message schemas are separate from internal `@DomainEvent` records
- Version external message schemas: `PaymentCompletedV1`, `PaymentCompletedV2`
- Never put database IDs in external messages without accompanying business identifiers
