---
tags: [service, use case, transactional, readOnly, application layer, @Service, @Transactional]
executor: be
---

# Application Service Pattern

## Code Pattern

```java
// <module>/application/<Name>Service.java
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)  // default: all reads are read-only transactions
public class MyEntityService {

    private final MyEntityRepository repository;  // domain port — never JpaMyEntityRepository

    @Transactional  // overrides readOnly for writes
    public MyEntity create(UUID tenantId, String name) {
        if (repository.existsByTenantIdAndName(tenantId, name)) {
            throw new MyEntityAlreadyExistsException("Entity '%s' already exists".formatted(name));
        }
        var entity = MyEntity.create(tenantId, name);
        var saved = repository.save(entity);
        log.info("Entity created: id={} tenant={}", saved.getId(), tenantId);
        return saved;
    }

    public MyEntity getById(UUID id) {
        return repository.findById(id)
                .orElseThrow(() -> new MyEntityNotFoundException("Entity not found: " + id));
    }
}
```

## Rules

- Class-level `@Transactional(readOnly = true)` — all methods are reads unless overridden
- Write methods get `@Transactional` (no `readOnly`)
- Never returns domain entities to callers outside the module — controller maps to DTOs
- Depends only on the domain repository port, never the JPA adapter
- One method per use case — if a method name needs "and", split it
