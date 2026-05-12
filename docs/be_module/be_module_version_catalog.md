---
tags: [version catalog, libs.versions.toml, bundles, dependency versions, Gradle catalog, toml]
executor: be_module
---

# Gradle Version Catalog Pattern

```toml
# gradle/libs.versions.toml
[versions]
slf4j          = "2.0.16"
vavr           = "0.11.0"
lombok         = "1.18.42"
junit          = "5.10.0"
assertj        = "3.27.6"
mockito        = "5.21.0"
testcontainers = "2.0.3"
awaitility     = "4.3.0"

[libraries]
slf4j-api          = { module = "org.slf4j:slf4j-api",                    version.ref = "slf4j" }
vavr               = { module = "io.vavr:vavr",                           version.ref = "vavr" }
lombok             = { module = "org.projectlombok:lombok",               version.ref = "lombok" }
junit-bom          = { module = "org.junit:junit-bom",                    version.ref = "junit" }
junit-jupiter      = { module = "org.junit.jupiter:junit-jupiter" }
assertj            = { module = "org.assertj:assertj-core",               version.ref = "assertj" }
mockito            = { module = "org.mockito:mockito-core",               version.ref = "mockito" }
testcontainers-bom = { module = "org.testcontainers:testcontainers-bom",  version.ref = "testcontainers" }
awaitility         = { module = "org.awaitility:awaitility",              version.ref = "awaitility" }

[bundles]
unit-testing        = ["junit-jupiter", "assertj", "mockito"]
integration-testing = ["junit-jupiter", "assertj", "testcontainers-bom", "awaitility"]
```

## Rules

- All dependency versions in a Version Catalog — never hardcode versions in module `build.gradle.kts`
- Use separate catalog files per concern (libs, migration, service, pipeline)
- Bundles group commonly used libs — module build files import a bundle, not individual libs
- Quality plugins (`checkstyle`, `jacoco`, `sonarqube`) applied in root to ALL subprojects — no per-module exceptions
