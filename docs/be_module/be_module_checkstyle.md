---
tags: [Checkstyle, style, EmptyCatchBlock, VisibilityModifier, MissingOverride, code style, build gate]
executor: be_module
---

# Checkstyle Rules

Checkstyle runs on every build and **fails the build on violation**. Applied to all submodules from the root build.

## Key Rules

```xml
<!-- config/checkstyle/checkstyle.xml -->
<module name="TreeWalker">
    <!-- No empty catch blocks — never silently swallow exceptions -->
    <module name="EmptyCatchBlock"/>

    <!-- Class design -->
    <module name="FinalClass"/>          <!-- Utility classes must be final -->
    <module name="VisibilityModifier"/>  <!-- Fields must be private -->
    <module name="MutableException"/>    <!-- Exception fields must be final -->

    <!-- Coding -->
    <module name="DeclarationOrder"/>    <!-- Fields → constructors → methods -->
    <module name="DefaultComesLast"/>    <!-- switch default at the end -->
    <module name="MissingSwitchDefault"/> <!-- Every switch needs a default -->
    <module name="SimplifyBooleanReturn"/>
    <module name="StringLiteralEquality"/> <!-- Use .equals(), not == on strings -->

    <!-- @Override always required -->
    <module name="MissingOverride"/>
</module>
```

## What This Enforces

- No silent exception swallowing (`EmptyCatchBlock`)
- No mutable public fields (`VisibilityModifier`)
- `@Override` always present (`MissingOverride`)
- Switch statements always have a `default` case
- No `==` on String literals
