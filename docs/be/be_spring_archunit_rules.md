---
tags: [ArchUnit, architecture rules, boundary, self-check, violations, package, layer]
executor: be
---

# ArchUnit Rules Reference

The project runs these rules as JUnit tests on every build. Your code must not violate any of them.

## The Five Rules

1. **Domain layer has no Spring/JPA dependencies** — `domain/` classes must not import `org.springframework.*` or `jakarta.persistence.*` (except `@Entity`/`@Table`/`@Column` on the aggregate itself)
2. **Controllers do not access infrastructure** — `@RestController` classes must not import any class from `*.infrastructure.*`
3. **Cross-module domain isolation** — module A must not import from `moduleB.domain.*` or `moduleB.application.*`
4. **Controllers live in `api/` packages** — `@RestController` classes must reside in a package ending in `.api`
5. **Application services live in `application/` packages** — `@Service` classes must reside in a package ending in `.application`

## Self-Check Before Writing

Mentally validate the code you are about to write against all five rules above. If it would violate any of them, restructure the code first — do not write the violation expecting a later fix.

Ask yourself: "Would ArchUnit's `noClasses().that()...should()` rule catch this?" If yes, move the class or remove the import before writing.

## Module Integration Test

```java
@ApplicationModuleTest
class UsersModuleTest {
    @Test
    void verifyModuleStructure(ApplicationModules modules) {
        modules.getModuleByName("users").ifPresent(module ->
            module.verify() // fails if module boundaries are violated
        );
    }
}
```

This runs faster than a full Spring context and catches boundary violations before ArchUnit does.
