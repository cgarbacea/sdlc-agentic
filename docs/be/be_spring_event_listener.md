---
tags: [event listener, ApplicationModuleListener, outbox, REQUIRES_NEW, transactional outbox, Spring Modulith]
executor: be
---

# Cross-Module Event Listener Pattern

## Code Pattern

```java
// <other-module>/application/OtherService.java
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class OtherService {

    @ApplicationModuleListener             // Spring Modulith transactional outbox
    @Transactional(propagation = Propagation.REQUIRES_NEW)  // required — runs in its own tx
    public void onMyEntityCreated(MyEntityCreatedEvent event) {
        log.info("Handling MyEntityCreatedEvent: entityId={}", event.entityId());
        // React to the event — never call MyEntityService directly
    }
}
```

## Rules

- `@ApplicationModuleListener` must always be paired with `@Transactional(propagation = Propagation.REQUIRES_NEW)` — Spring enforces this at startup
- The event listener only imports from `mymodule.events.*` — never from `mymodule.domain.*`
- Failed listeners are retried via the `event_publication` table (transactional outbox pattern)
- Never call the source module's service directly from the listener — use only the event payload
- The `event_publication` table must exist in the DB schema (Liquibase changeset required)
