---
tags: [exception, error handling, RestControllerAdvice, global handler, local handler, ExceptionHandler]
executor: be
---

# Exception Handling — Global vs Local

Two valid approaches. Choose one and apply it consistently across the entire project.

## Option A — Local @ExceptionHandler (per controller)

Each controller handles its own exceptions:

```java
@ExceptionHandler(MyEntityNotFoundException.class)
public ProblemDetail handleNotFound(MyEntityNotFoundException ex) {
    return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
}
```

**When to use:** Modules have distinct exception vocabularies. Good default for Spring Modulith.

## Option B — Global @RestControllerAdvice

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(NotFoundException.class)
    public ProblemDetail handleNotFound(NotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }
}
```

**When to use:** Multiple modules throw the same exception types. Check `shared/` for an existing handler before creating a new one.

## Rules

- **Never mix both** — pick one approach per project and apply it everywhere
- Always use `ProblemDetail` (RFC 9457) — no custom error envelopes
- Before adding a local handler, check `shared/` for an existing `GlobalExceptionHandler`
- Domain exceptions (`UserNotFoundException`) over raw exceptions (`RuntimeException`)
