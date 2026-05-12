---
tags: [response, DTO, record, mapping, from factory, request validation, Bean Validation, NotBlank]
executor: be
---

# Response DTO Pattern

## Response Record

```java
// <module>/api/<Name>Response.java
public record MyEntityResponse(
        String id,
        String name,
        String status,
        Instant createdAt
) {
    /** Maps from domain entity to API response — only place domain is accessed from api layer */
    public static MyEntityResponse from(MyEntity entity) {
        return new MyEntityResponse(
                entity.getId().toString(),
                entity.getName(),
                entity.getStatus().name(),
                entity.getCreatedAt()
        );
    }
}
```

## Request Record

```java
// <module>/api/Create<Name>Request.java
public record CreateMyEntityRequest(
        @NotBlank String name,
        @NotNull UUID tenantId
) {}
```

## Rules

- Response and request types are Java `record` — immutable, no boilerplate
- `from(DomainEntity)` static factory is the only bridge between domain and API layers
- Never expose domain entity fields directly — always map
- Bean Validation annotations (`@NotBlank`, `@NotNull`, `@Size`) on request records
- Response field names use camelCase to match FE TypeScript interfaces directly
- Jackson serialises Java records to JSON out of the box — no extra config needed
