---
tags: [controller, endpoint, REST, ProblemDetail, ExceptionHandler, X-Tenant-ID, JWT, versioning]
executor: be
---

# REST Controller Pattern

## Code Pattern

```java
// <module>/api/<Name>Controller.java
@RestController
@RequestMapping("/api/v1/my-entities")
@RequiredArgsConstructor
@Slf4j
public class MyEntityController {

    private final MyEntityService service;

    @GetMapping("/{id}")
    public MyEntityResponse getById(
            @RequestHeader("X-Tenant-ID") UUID tenantId,
            @PathVariable UUID id) {
        return MyEntityResponse.from(service.getById(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public MyEntityResponse create(
            @RequestHeader("X-Tenant-ID") UUID tenantId,
            @Valid @RequestBody CreateMyEntityRequest req) {
        var entity = service.create(tenantId, req.name());
        return MyEntityResponse.from(entity);
    }

    @ExceptionHandler(MyEntityNotFoundException.class)
    public ProblemDetail handleNotFound(MyEntityNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(MyEntityAlreadyExistsException.class)
    public ProblemDetail handleConflict(MyEntityAlreadyExistsException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
    }
}
```

## Rules

- All endpoints versioned under `/api/v1/`
- Every request includes `@RequestHeader("X-Tenant-ID") UUID tenantId` — multi-tenant isolation
- Use `@AuthenticationPrincipal Jwt jwt` when the JWT subject (user ID) is needed
- `@ExceptionHandler` in the controller — keeps exceptions local to the module
- `ProblemDetail` is the standard error response (RFC 9457) — no custom error envelopes
- See `be_spring_exception_handling.md` for global vs local handler decision
