---
tags: [module layout, hexagonal, package structure, domain, application, infrastructure, api, hexagonal architecture]
executor: be
---

# Spring Modulith — Canonical Module Layout

Each module is a self-contained vertical slice of the domain with four internal layers. Never mix responsibilities across layers.

## Package Structure

```
com/<company>/<service>/
├── <module>/
│   ├── domain/              # Pure Java — no Spring, no JPA
│   │   ├── <Aggregate>.java # @AggregateRoot — business logic lives here
│   │   ├── <Repo>.java      # Repository interface (port) — pure Java
│   │   └── <ValueObject>.java
│   ├── events/              # Public contract of this module
│   │   ├── <Name>Event.java # @DomainEvent records — no domain types in payload
│   │   └── package-info.java # @NamedInterface("events")
│   ├── application/         # Use cases — orchestrates domain
│   │   └── <Name>Service.java # @Service, @Transactional
│   ├── infrastructure/      # JPA adapters — package-private
│   │   └── Jpa<Name>Repository.java
│   └── api/                 # REST layer
│       ├── <Name>Controller.java
│       └── <Name>Response.java
└── shared/                  # Cross-cutting: SecurityConfig, exception handlers
```

## The Hexagonal Rule

```
domain/         ← pure Java only. Zero Spring, zero JPA imports.
application/    ← depends on domain interfaces (ports), never on infrastructure
infrastructure/ ← package-private. Never imported by application or api layers.
api/            ← depends on application only. Never imports domain entities directly.
```

**Cross-module communication:**
- Module A **may NOT** import `moduleB.domain.*`, `moduleB.application.*`, or `moduleB.infrastructure.*`
- Module A **may** import `moduleB.events.*` (the `@NamedInterface("events")` surface only)
- All cross-module side effects go through domain events, never direct bean injection

## Known Trade-off: JPA on the Aggregate

The pragmatic approach: JPA annotations (`@Entity`, `@Table`, `@Column`) live directly on the aggregate, and the aggregate extends `AbstractAggregateRoot`.

**Rationale:** Eliminates a mapping layer without meaningful benefit at this scale. Spring Modulith still enforces cross-module boundaries. ArchUnit still catches business logic Spring dependencies.

**The boundary that must hold:**
- `domain/` must not import `org.springframework.stereotype.*`, `org.springframework.web.*`, or transaction annotations
- `@Entity`, `@Table`, `@Column`, and `AbstractAggregateRoot` are the only Spring/JPA imports permitted in domain
