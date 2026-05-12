---
tags: [aggregate, domain entity, registerEvent, AbstractAggregateRoot, factory method, AggregateRoot, jMolecules]
executor: be
---

# Aggregate Root Pattern

## Code Pattern

```java
// <module>/domain/<Name>.java
@AggregateRoot          // jMolecules — signals DDD aggregate
@Entity
@Table(name = "entities")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED) // JPA requires no-arg; protected prevents misuse
public class MyEntity extends AbstractAggregateRoot<MyEntity> {

    @Identity
    @Id
    @Column(updatable = false, nullable = false)
    private UUID id;

    // All state changes go through business methods — no public setters
    public static MyEntity create(UUID tenantId, String name) {
        var entity = new MyEntity();
        entity.id = UUID.randomUUID();
        entity.tenantId = tenantId;
        entity.name = name;
        entity.createdAt = Instant.now();
        entity.updatedAt = Instant.now();
        // Register domain event — published automatically on repository.save()
        entity.registerEvent(new MyEntityCreatedEvent(entity.id, tenantId, name));
        return entity;
    }

    public void updateName(String newName) {
        this.name = newName;
        this.updatedAt = Instant.now();
    }
}
```

## Rules

- `AbstractAggregateRoot` + `registerEvent()` = automatic event publishing on `save()`
- No public setters — all mutation goes through named business methods
- `@NoArgsConstructor(access = AccessLevel.PROTECTED)` — required by JPA, restricted from misuse
- Factory method (`create()`) is the only way to construct valid entities
- All timestamps use `Instant` — never `Date` or `LocalDateTime`
