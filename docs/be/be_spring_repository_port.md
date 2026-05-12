---
tags: [repository, port, JPA adapter, infrastructure, Spring Data, domain interface, package-private]
executor: be
---

# Repository Port Pattern

## Domain Port (pure Java)

```java
// <module>/domain/<Name>Repository.java
// Pure Java interface — no Spring, no JPA annotations
public interface MyEntityRepository {

    MyEntity save(MyEntity entity);

    Optional<MyEntity> findById(UUID id);

    Optional<MyEntity> findByTenantIdAndName(UUID tenantId, String name);

    Page<MyEntity> findByTenantId(UUID tenantId, Pageable pageable);

    boolean existsByTenantIdAndName(UUID tenantId, String name);
}
```

## JPA Adapter (package-private)

```java
// <module>/infrastructure/JpaMyEntityRepository.java
// Package-private — application layer never imports this directly
@Repository
interface JpaMyEntityRepository extends JpaRepository<MyEntity, UUID>, MyEntityRepository {
    // Method signatures only — Spring Data generates the SQL
    Optional<MyEntity> findByTenantIdAndName(UUID tenantId, String name);
    Page<MyEntity> findByTenantId(UUID tenantId, Pageable pageable);
    boolean existsByTenantIdAndName(UUID tenantId, String name);
}
```

## Rules

- The domain repository interface has zero Spring imports — it is a pure port
- The JPA adapter is `interface` (not class) extending both `JpaRepository` and the domain port
- The JPA adapter is **package-private** — forces all access through the domain port
- Spring Data registers the JPA adapter as a bean at runtime via the domain port interface
- Application services depend on the domain port, never on the JPA adapter directly
