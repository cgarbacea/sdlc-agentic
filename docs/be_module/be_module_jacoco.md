---
tags: [JaCoCo, coverage, test coverage, minimum, 80 percent, build gate, jacocoTestCoverageVerification]
executor: be_module
---

# JaCoCo Test Coverage Enforcement

```kotlin
// build.gradle.kts (root) — applied to all subprojects
val minimumLimitTestCoverage = BigDecimal("0.8")   // 80% minimum, build fails below this

tasks.jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = minimumLimitTestCoverage
            }
        }
    }
}

tasks.check {
    dependsOn(tasks.jacocoTestCoverageVerification)
}
```

## Excluded from Coverage

```kotlin
val jacocoExcludePackages = listOf(
    "**/config/**",
    "**/Pipeline.class",
    "**/Job.class"
)
```

## Rules

- 80% line coverage minimum — enforced at build time, not "nice to have"
- Exclude config/wiring/generated classes — coverage there is noise
- `tasks.check` depends on `jacocoTestCoverageVerification` — checked on every `./gradlew check`
- Applied in root build to all subprojects — no module can opt out
