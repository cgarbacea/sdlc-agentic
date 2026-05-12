---
tags: [SonarQube, quality, sonar, quality gate, coverage report, code smells, duplications]
executor: be_module
---

# SonarQube Integration

## Gradle Configuration

```kotlin
// build.gradle.kts (root)
plugins {
    id("org.sonarqube") version "4.0.0.2929"
}

// Run: ./gradlew sonar -Dsonar.host.url=<url> -Dsonar.token=<token>
```

## sonar-project.properties

```properties
sonar.projectKey=<org>_<project>
sonar.coverage.jacoco.xmlReportPaths=**/build/reports/jacoco/test/jacocoTestReport.xml
sonar.java.checkstyle.reportPaths=**/build/reports/checkstyle/*.xml
```

## Quality Gates SonarQube Enforces

- Coverage ≥ 80% (mirrors JaCoCo minimum)
- Zero new bugs in new code
- Zero critical/blocker code smells
- Duplicated lines < 3%

## Rules

- SonarQube applied in root build alongside JaCoCo and Checkstyle
- Reports uploaded as part of CI pipeline after tests complete
- Quality gate failure blocks merge to main
