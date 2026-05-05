# ADR 0001 — Row-Level Security via PostgreSQL RLS

**Date:** 2026-05-04
**Status:** Accepted

## Context

catalog-ai is a multi-tenant SaaS. Every table that holds tenant data carries a `tenant_id` column. We need to guarantee that one tenant can never read or write another tenant's data, even if application code contains a bug that omits a `WHERE tenant_id = ?` clause.

## Decision

We use PostgreSQL native **Row-Level Security (RLS)** as a defence-in-depth layer.

### How it works

1. Every table has `ALTER TABLE … ENABLE ROW LEVEL SECURITY`.
2. A single `POLICY tenant_isolation` is created per table using `USING` (read + write).
3. The policy reads `app.current_tenant_id` from the Postgres session configuration:

   ```sql
   -- Standard tenant-scoped table
   CREATE POLICY tenant_isolation ON products
   USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

   -- Tables where tenant_id IS NULL means "global / system-owned"
   -- (categories, attribute_definitions, model_personas)
   CREATE POLICY tenant_isolation ON categories
   USING (
       tenant_id IS NULL
       OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
   );
   ```

4. The FastAPI auth middleware sets the session variable after resolving the JWT:

   ```python
   await db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": str(tenant_id)})
   ```

   `SET LOCAL` scopes the variable to the current transaction, which is what we want.

5. The `tenants` table is a special case: the policy checks the **primary key** (`id`), not a `tenant_id` column, so a tenant can only see its own row.

### Superuser bypass

PostgreSQL superusers bypass RLS by default. This means:
- Alembic migrations run as superuser and are not blocked.
- The seed script runs as superuser and is not blocked.
- **The application database role should NOT be a superuser in production.** Create a dedicated non-superuser role and grant it only `SELECT / INSERT / UPDATE / DELETE` on application tables.

In local dev we use the `postgres` superuser for convenience; this is acceptable because RLS is still defined and will enforce correctly once a non-superuser role is used in staging/prod.

If you need to enforce RLS even for superuser accounts (e.g., for testing), run:

```sql
ALTER TABLE <table> FORCE ROW LEVEL SECURITY;
```

Do this only in test environments — never in prod, as it prevents the migration user from running schema changes.

### Tables with nullable tenant_id

Three tables hold global system data that all tenants share:

| Table | Global rows | Tenant-specific rows |
|-------|-------------|----------------------|
| `categories` | Default garment tree seeded at startup | Custom categories a tenant adds |
| `attribute_definitions` | Attributes for global categories | Attributes for tenant categories |
| `model_personas` | 8 system-managed personas | Personas a tenant creates |

For these tables, the policy allows `tenant_id IS NULL` (system rows) in addition to matching tenant rows.

## Consequences

**Good:**
- Tenant isolation is enforced at the database layer, independent of application bugs.
- No changes needed to existing queries — the filter is transparent.
- Adding a new table only requires `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY`.

**Bad / Watch out for:**
- `current_setting('app.current_tenant_id', true)` returns `NULL` when the variable is not set, making `tenant_id = NULL` always false (no rows visible). Any route that forgets to set the session variable returns empty results instead of an error. The auth middleware must always set it before executing queries.
- Bulk admin operations (e.g., cross-tenant reporting, migrations, seeding) must either run as superuser or explicitly set a "bypass" context. Document these cases.
- Connection pooling: the session variable is connection-scoped. When using a connection pool, always set the variable at the start of every transaction (`SET LOCAL`), not once per connection.
