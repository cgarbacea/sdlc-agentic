---
tags: [implementation, executor, ConcurrentHashMap, Try.flatMap, constructor injection, AutoCloseable]
executor: be_module
---

# Implementation Module Pattern

```java
// execution/src/.../DbRulesExecutor.java
public class DbRulesExecutor implements RulesExecutor {

    private final EventsState state;
    private final Config config;
    // ConcurrentHashMap for thread-safe rule registry — no external locking needed
    private final Map<UUID, Rule> rules = new ConcurrentHashMap<>();

    public DbRulesExecutor(EventsState state, Config config) {
        this.state = state;
        this.config = config;
    }

    @Override
    public Try<Set<Alert>> execute(@NonNull String parentEntityId, @NonNull EntityChange event) {
        var queries = rules.values().stream()
                .collect(Collectors.toMap(Rule::ruleId, Rule::definition));

        return state.insert(parentEntityId, event)
                .flatMap(v -> rules.isEmpty()
                        ? Try.success(Collections.<BasicAlert>emptySet())
                        : state.query(parentEntityId, queries))
                .map(this::mapToAlerts);
    }

    @Override
    public Try<Void> registerRule(@NonNull Rule rule) {
        return Try.run(() -> {
            rules.put(rule.ruleId(), rule);
            state.invalidateCache(rule.ruleId());
        });
    }

    @Override
    public void close() {
        state.close();
    }
}
```

## Rules

- Constructor injection only — no `@Autowired` fields, no Spring dependency if module is library-level
- `ConcurrentHashMap` for thread-safe in-memory registries — documented why, not just what
- `Try.flatMap()` chains instead of nested try/catch
- `implements AutoCloseable` — `close()` delegates resource cleanup to collaborators
