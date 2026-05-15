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

## AAA Structure (Arrange, Act, Assert)

Every unit test should have a clear Arrange, Act, Assert flow.

```java
@Test
void execute_whenRuleMatches_returnsAlert() {
    // Arrange
    var rule = Rule.builder()
            .ruleId(UUID.randomUUID())
            .tenantId("tenant-1")
            .definition("SELECT ...")
            .severity(SeverityLevel.HIGH)
            .build();

    executor.registerRule(rule);

    // Act
    var result = executor.execute("entity-1", someEntityChange());

    // Assert
    assertThat(result.isSuccess()).isTrue();
    assertThat(result.get()).hasSize(1);
}
```

Rules:

- Keep blank lines between Arrange, Act, and Assert sections
- One behavior per test method
- Test names should describe expected behavior and condition

## JUnit + AssertJ + Mockito Baseline

- JUnit 5 (`junit-jupiter`) for test execution
- AssertJ for fluent assertions (`assertThat(...)`)
- Mockito (`@Mock`, `@InjectMocks`) for dependency isolation in unit tests

Prefer AssertJ for readability:

```java
assertThat(payment.getStatus()).isEqualTo(PaymentStatus.COMPLETED);
assertThat(payment.getTransactionId()).isNotBlank();
```

## Testcontainers Base Pattern

Use reusable container wiring for integration tests, then override app properties dynamically.

```java
@Testcontainers
@Tag("integration")
abstract class BaseIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void registerProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

Rules:

- Never connect integration tests to development databases
- Keep container lifecycle deterministic and isolated per suite
- Use fixed test data setup (factory/builders) instead of depending on execution order

## Coverage Gate (Minimum 80%)

Enforce coverage in the build so quality cannot regress silently.

```kotlin
tasks.jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = "0.80".toBigDecimal()
            }
        }
    }
}

tasks.check {
    dependsOn(tasks.jacocoTestCoverageVerification)
}
```

Rules:

- Coverage gate runs in CI and locally via `check`
- Exclusions must be minimal and explicit
- Do not use broad exclusion patterns to artificially pass the gate
