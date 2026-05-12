---
tags: [N+1, lazy loading, JOIN FETCH, EntityGraph, FetchType, EAGER, JPA performance, BatchSize]
executor: be
---

# JPA Query Patterns — Avoiding N+1

The N+1 problem is the most common Spring JPA performance bug: one query to load N entities, then N additional queries to load their associations.

## Examples

```java
// ❌ N+1 — for 100 orders, this fires 101 SQL queries
List<Order> orders = orderRepository.findAll();
orders.forEach(o -> o.getItems().size()); // each access fires a new query

// ✅ JOIN FETCH — single query with a join
@Query("SELECT o FROM Order o JOIN FETCH o.items WHERE o.tenantId = :tenantId")
List<Order> findAllWithItems(@Param("tenantId") UUID tenantId);

// ✅ @EntityGraph — declarative, avoids modifying the JPQL
@EntityGraph(attributePaths = {"items"})
List<Order> findByTenantId(UUID tenantId);
```

## Rules

- Never use `FetchType.EAGER` on `@OneToMany` or `@ManyToMany` — it causes unbounded joins
- Use `JOIN FETCH` or `@EntityGraph` when you know the association will be accessed in the same request
- Enable `spring.jpa.show-sql=true` and `spring.jpa.properties.hibernate.format_sql=true` in dev to detect N+1
- Batch-fetch associations with `@BatchSize(size = 20)` when JOIN FETCH is impractical
- Never call a lazy-loaded association outside a `@Transactional` boundary — throws `LazyInitializationException`
