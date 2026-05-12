---
tags: [multi-module, Gradle, project structure, core, impl, pipeline, settings.gradle, subproject]
executor: be_module
---

# Multi-Module Project Layout

```
<project-root>/
├── build.gradle.kts            # Root build — plugins, shared config, subprojects
├── settings.gradle.kts         # Lists all submodules
├── version.properties          # Single source of truth for project version
├── gradle/
│   ├── libs.versions.toml      # Version catalog — all dependency versions
│   ├── migration.versions.toml # Separate catalog per concern
│   └── service.versions.toml
├── config/
│   └── checkstyle/
│       ├── checkstyle.xml
│       └── suppressions.xml
├── <core-module>/              # Pure interfaces and domain types — zero framework deps
│   └── src/main/java/.../core/
├── <impl-module>/              # Concrete implementation of core interfaces
│   └── src/main/java/.../execution/
└── <pipeline-module>/          # Deployment entry point (Flink, Spring Boot, etc.)
```

## Rules

- The `core` module has **zero framework dependencies** — only JDK + utility libs (Vavr, Lombok)
- Implementation modules depend on `core` — never the other way around
- The deployment/pipeline module is the composition root — depends on all others
- Each module has its own `build.gradle.kts` — shared config lives in root build
- Project version in `version.properties` — loaded by root build, never duplicated
