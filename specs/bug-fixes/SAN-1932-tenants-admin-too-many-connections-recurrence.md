---
id: SAN-1932
title: "PDO 1040 \"Too many connections\" recurred after the SAN-1757 retry fix (SC-SAAS-TENANTS-ADMIN-4)"
type: bug-fix
status: in-progress
linear: https://linear.app/sanchiconnect/issue/SAN-1932
sentry: [SC-SAAS-TENANTS-ADMIN-4]
repos: [tenants-admin]
related: [SAN-1757, SAN-413, SAN-414, SAN-1922]
commit: none — read-only investigation; infra follow-up open
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1932: tenants-admin connection exhaustion

## Investigation
* **Sentry:** `PDOException: SQLSTATE[08004] [1040] Too many connections` in `core/db.php` (Medoo constructor), 7 events around 2026-10-11.
* **The retry fix is on main.** SAN-1757 `0ccd8af` is an ancestor of tenants-admin `origin/main` `f5ca0c4` (2026-10-08 22:09 IST). The events are after it, *if* that build was deployed.
* **Retry behaviour** (`config/config.php:62-91`): 3 attempts, 200 ms × attempt plus jitter (about 0.3-0.8 s in total), 1040 only, bootstrap connect only.
  * `core/db.php:325-422` reconnects once on 2006/2013 errors, but those reconnects open new connections and are not 1040-aware.
* **What it means:** if the events carry the `connectWithRetryOnTooManyConnections` frame, all 3 attempts hit 1040. The shared tenants MySQL was at `max_connections` for at least about a second, several times. That is real exhaustion, and more retries won't fix it.
* **Where connection pressure on the shared tenants MySQL comes from:**
  1. **Tenants NestJS** (`src/core/database/database.module.ts:23-28`): no pool settings, so the mysql2 default of 10 connections per process × replicas applies. `synchronize: true` also takes metadata locks on every restart.
  2. **sc-saas-admin**, on every admin page load of every tenant:
     * 1 tenants-DB connection, held for the whole request;
     * 1 tenant-DB connection;
     * up to 2 more during the tenant-lookup retry;
     * CLI workers open their own pairs.
  3. **tenants-admin:**
     * 1 bootstrap connection per request;
     * per-tenant connection loops in `client_stats/list.php:95` and `cors_domain_management/backfill.php:119`;
     * one connection per request in `sql_script_execute.php:126` and `_data_export_generate.php:2275`.
  4. **Per-tenant sc-saas-backend TypeORM pools**, if tenant DBs share the same instance.

## Fix
No code change.

**Infra first:**
* Check `max_connections`, `Max_used_connections`, `Threads_connected` and the RDS `DatabaseConnections` metric around 2026-10-11.
* Group `PROCESSLIST` by user and host to see who holds the connections.
* Lower `wait_timeout`.
* Raise `max_connections` or the instance class if the load is legitimate.

**Code follow-ups:**
* Set an explicit `extra: { connectionLimit, connectTimeout }` in tenants `database.module.ts`.
* Release `$mainDatabase` early, or open it lazily, in sc-saas-admin.
* Give the tenants-admin bootstrap connect the same catch → 503 + single Sentry event added to sc-saas-admin in SAN-1922.
* Disable `synchronize` in prod.

## Open
* Confirm the tenants-admin deploy date relative to 2026-10-11.
* Confirm whether the Sentry events show the retry frame.
