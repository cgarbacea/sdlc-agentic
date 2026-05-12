---
tags: [test, unit test, integration test, TestContainers, H2, in-memory, Awaitility, Tag integration]
executor: be_module
---

# Testing Strategy for Multi-Module Projects

## Unit Tests (src/test/) — Fast, No I/O

```java
class H2RulesExecutorTest {

    private RulesExecutor executor;

    @BeforeEach
    void setup() throws Exception {
        var state = new H2EventsState(H2DataSource.create());
        executor = new H2RulesExecutor(state, Config.defaults());
    }

    @Test
    void execute_withMatchingRule_producesAlert() {
        var rule = Rule.builder()
                .ruleId(UUID.randomUUID())
                .tenantId("tenant-1")
                .definition("SELECT ...")
                .severity(SeverityLevel.HIGH)
                .build();

        executor.registerRule(rule);
        var result = executor.execute("entity-1", someEntityChange());

        assertThat(result.isSuccess()).isTrue();
        assertThat(result.get()).hasSize(1);
    }
}
```

## Integration Tests (src/integration/) — Real Dependencies

```java
@Tag("integration")
class AlertVisualizerIntegrationTest {

    static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.4.0"));

    @BeforeAll
    static void startKafka() { kafka.start(); }

    @Test
    void consumer_receivesAlertFromTopic() {
        // Real Kafka, real topics, real serialization
    }
}
```

## Rules

- Unit tests use in-memory implementations (`H2`, `ConcurrentHashMap`) — zero I/O
- Integration tests use TestContainers — separate Gradle source set
- Integration tests tagged `@Tag("integration")` — excluded from default `./gradlew check`
- Run integration tests explicitly: `./gradlew integrationTest`
- Use `awaitility` for async assertions in integration tests
