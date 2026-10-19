# Plan: `synchronize: false` outside local development, schema changes as migrations (SAN-1630)

Status: **draft for approval** (2026-10-19). Covers sc-saas-backend and sanchiconnect-saas-tenants. Related: SAN-1605 (migrations as a deploy step), SAN-713/714 (the unique index that could have stopped production booting).

## Today

| | sc-saas-backend | sanchiconnect-saas-tenants |
|---|---|---|
| `synchronize` | `true`, hard-coded for every `NODE_ENV`, production included (`src/core/database/database.module.ts`) | same |
| Databases | **one per tenant deployment**: about 26 client databases on production, plus demo, SanchiConnect and the dev ones | one shared cockpit database |
| Entities | 337 | 61, including **23 `spa_*` tables that tenants-admin (PHP) also writes to** |
| TypeORM | **0.3.6** (no `migration:run --fake`) | 0.3.17 (has `--fake` and `migration:generate --check`) |
| Schema migrations | none. `src/modules/migrations/` holds HTTP-triggered *data* fixes, not schema changes | none |
| Data source for the CLI | none | none |

**Every boot, each app compares its entities with the live database and runs `ALTER`s to match.** Consequences:
- a renamed column is dropped and re-created empty;
- a column that the PHP panels added to an entity table is dropped;
- an index that existing data violates (SAN-714) fails the boot;
- nothing records what changed, or when.

## Target

- `synchronize` is `true` only when `NODE_ENV=LOCAL`.
- Schema changes are migration files, committed with the entity change, and run by a step in each Jenkins job **before** the app restarts.
- A PR that changes an entity without a migration fails CI.
- A production boot whose entities don't match the database **fails loudly**, instead of altering it.

## Phases

### Phase 0: drift inventory (read-only; needs database access)

`synchronize` should leave every database matching its entities. Where it failed silently (e.g. an index it couldn't create) or someone changed a table by hand, the database has drifted. A baseline can only be faked onto a database with **no drift**.

- New script in each repo, `scripts/schema-drift.ts`. It builds a DataSource with `synchronize: false` and prints `driver.createSchemaBuilder().log()`: the SQL `synchronize` *would* run now, without running it. Read-only.
- Run it against dev 1, dev 2, demo, SanchiConnect, **every production tenant database**, and the cockpit database. The backend can loop over `tenant_users` for the per-tenant credentials.
- Record the result per database. Empty means ready. Anything else is resolved first: apply it deliberately, or fix the entity.

### Phase 1: tooling, no change in behaviour

- `src/core/database/data-source.ts` (env-driven, the same settings as the app) for the TypeORM CLI.
- npm scripts: `migration:generate`, `migration:create`, `migration:run`, `migration:revert`, `migration:show`.
- A `src/database/migrations/` folder, with `migrationsTableName: 'typeorm_migrations'` and `migrationsRun: false`.
- **Backend:** upgrade TypeORM 0.3.6 → 0.3.17 (the version tenants uses) in its own PR, tested on dev, to get `--fake` and `--check`. (Alternative: no upgrade, and insert the baseline row into `typeorm_migrations` by hand on each database.)
- `synchronize` stays `true`.

### Phase 2: baseline migration

- Generate `…-Baseline.ts` from the entities against an **empty** MySQL 8 database. It is the full `CREATE` script.
- **New databases** (new tenant, new environment): `migration:run` builds the schema. This replaces `synchronize` building it on first boot.
- **Existing databases** with zero drift in Phase 0: `migration:run --fake` records the baseline as applied without running it.

### Phase 3: CI guard

- New CI step (reusing the MySQL 8 service that `api-contract.yml` already starts in the backend):
  1. empty database;
  2. `migration:run`;
  3. `migration:generate --check`, which must find nothing.
- An entity change without its migration fails the PR. This becomes a required check later (SAN-1583).

### Phase 4: switch it off, per environment

- `synchronize: process.env.NODE_ENV === 'LOCAL'`. An escape hatch, `DB_SYNCHRONIZE=true`, exists for a one-off emergency only.
- **Boot check:** in non-local environments, the app runs the schema-builder log at start.
  - `SCHEMA_CHECK_MODE=log` (first): non-empty is logged as an error.
  - `enforce` (later): non-empty stops the app with the pending SQL in the log.
- **Each Jenkins job:** `npm run migration:deploy` before the pm2 restart (SAN-1605, built 2026-10-19; see `docs/DEPLOYMENT.md` → Database migrations step). For the backend, that's every client job, each against its own database. The step adopts each database on its first run, so Phase 2's `--fake` happens through it rather than by hand; jobs can run it before this phase, while `synchronize` is still on.
- **Order:** dev 1 → dev 2 → demo → one production client → all production clients → cockpit. Same release path as `docs/RELEASE-PLAN-SAN-1939.md`.
- **Tenant provisioning:** onboarding a new tenant must run `migration:run` on its new database. Update the onboarding steps.

### Phase 5: prove it

- Ship one real schema change (the next additive column) as a migration, through the Jenkins step, on every environment.
- Then set `SCHEMA_CHECK_MODE=enforce`.

## Done when (from SAN-1630)

- `synchronize` is false on staging and production for both services.
- A schema change has shipped as a migration through the deploy step.
- A boot with a mismatched entity fails loudly instead of altering the database.

## Risks

- **Drift found in Phase 0:** some databases may need manual reconciliation first. That is why Phase 0 comes before anything else.
- **TypeORM upgrade in the backend:** 0.3.6 → 0.3.17 has behaviour changes between minors. It goes in its own PR, through dev and the e2e run.
- **PHP writers:** sc-saas-admin (tenant databases) and tenants-admin (`spa_*`) change tables without TypeORM. After the switch, their columns are no longer dropped, but they also aren't in any migration. Schema changes made from PHP must go through a migration in the owning NestJS repo from then on.
- **Many databases:** a migration that fails on one tenant leaves the tenants out of step. `migration:show` per job, and the deploy log, show which database is on which version.

## Decisions needed

1. **Backend TypeORM upgrade** to 0.3.17 (recommended), or a manual baseline insert per database.
2. **Who runs Phase 0** against the production databases (needs database access).
3. **Who edits the Jenkins jobs** (the migration step before restart).
4. **Timing:** start after the current release (SAN-1939) reaches production, so the two changes don't overlap.
