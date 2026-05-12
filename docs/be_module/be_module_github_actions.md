---
tags: [GitHub Actions, CI, pipeline, workflow, path trigger, skip ci, composite action, workflow_dispatch]
executor: be_module
---

# GitHub Actions CI Pattern

## Path-Based Trigger

```yaml
name: "CI/CD: <Module> Pipeline"

on:
  push:
    branches: [main]
    paths:
      - "<module>/**"
      - "core/**"                  # core changes affect all modules
      - ".github/actions/**"
      - "build.gradle.kts"
      - "gradle/**"
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, stg, qa, prod]
        default: dev

jobs:
  check-skip:
    outputs:
      should_skip: ${{ steps.check.outputs.should_skip }}
    steps:
      - name: Check for [skip ci]
        id: check
        run: |
          if [[ "${{ github.event.head_commit.message }}" == *"[skip ci]"* ]]; then
            echo "should_skip=true" >> "$GITHUB_OUTPUT"
          else
            echo "should_skip=false" >> "$GITHUB_OUTPUT"
          fi

  checkstyle:
    needs: check-skip
    if: needs.check-skip.outputs.should_skip != 'true'
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/java         # composite action: setup JDK + Gradle
      - uses: ./.github/actions/checkstyle

  unit-tests:
    needs: checkstyle
    steps:
      - uses: ./.github/actions/unit-test
        with:
          module: <module>
```

## Rules

- `paths:` filter is mandatory in multi-module repos — without it every push runs every pipeline
- Always include `core/**` and `gradle/**` in paths — changes there affect all modules
- `[skip ci]` in commit message bypasses expensive steps (automated version bumps)
- Composite actions in `.github/actions/` share setup steps — no duplication
- Pipeline is linear: check-skip → checkstyle → unit-tests → integration-tests → deploy
