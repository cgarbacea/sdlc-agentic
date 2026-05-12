---
tags: [migration, Liquibase, changeset, master changelog, db.changelog-master.xml, schema, SQL]
executor: be
---

# Liquibase Migration Pattern

## Migration File

```sql
-- src/main/resources/db/changelog/migrations/NNN_create_my_entities_table.sql
-- Always add as a new changeset — never modify existing ones

-- changeset author:NNN_create_my_entities_table
CREATE TABLE my_entities (
    id          UUID        NOT NULL PRIMARY KEY,
    tenant_id   UUID        NOT NULL,
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    created_at  TIMESTAMPTZ  NOT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL,
    CONSTRAINT uq_my_entities_tenant_name UNIQUE (tenant_id, name)
);

CREATE INDEX idx_my_entities_tenant_id ON my_entities (tenant_id);
```

## Master Changelog Registration

After creating the migration file, register it in the master changelog:

```xml
<!-- src/main/resources/db/changelog/db.changelog-master.xml -->
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog">
    <include file="migrations/001_create_users_table.sql" relativeToChangelogFile="true"/>
    <include file="migrations/002_create_workspaces_table.sql" relativeToChangelogFile="true"/>
    <!-- Add new migration at the END — order is execution order -->
    <include file="migrations/NNN_create_my_entities_table.sql" relativeToChangelogFile="true"/>
</databaseChangeLog>
```

## Rules

- Every schema change is a new changeset — never modify an applied changeset
- Every new migration file must be added to `db.changelog-master.xml` — Liquibase only runs files listed there
- Add includes at the **end** of the master changelog — order is execution order
- All tables have `id UUID PRIMARY KEY`, `tenant_id UUID NOT NULL`, `created_at`, `updated_at`
- Use `TIMESTAMPTZ` (not `TIMESTAMP`) for all timestamps
- Add `CREATE INDEX` for every foreign key and frequently-queried column
