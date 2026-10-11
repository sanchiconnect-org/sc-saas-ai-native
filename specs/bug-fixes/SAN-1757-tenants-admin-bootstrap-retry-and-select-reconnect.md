# SAN-1757 — tenants-admin: bootstrap connects once and a dropped connection is fatal

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1757 (Sentry SC-SAAS-TENANTS-ADMIN-4 / -A / -8) · **Repo:** sanchiconnect-saas-tenants-admin · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (client resilience) over shared-MySQL capacity

## Evidence
- -4: `[1040] Too many connections` at bootstrap; -A / -8: `[2006] MySQL server has gone away` / 2013 on queries (observed in Sentry). Same shared tenants MySQL as SAN-1736 / SAN-140.
- `config.php`'s `"error" => PDO::ERRMODE_SILENT` is not read by this Medoo copy, so PDO runs in exception mode and a dead connection throws an uncaught `PDOException` (observed in `core/db.php`).

## Root cause
1. The bootstrap connection in `config/config.php` was attempted exactly once, so one 1040 refusal killed the request.
2. `core/db.php` `exec()` had no handling for a connection dropped before a query.
Underlying capacity (`max_connections`) is an infra decision.

## Fix
Commit `0ccd8af`. `config/config.php`: `connectWithRetryOnTooManyConnections()` retries only 1040 (message match), 3 attempts, `200 ms * attempt` + up to 100 ms jitter (about 0.8 s max), same as SAN-1736. `core/db.php`: connection args kept in `$reconnectArgs`; `exec()` goes through `prepareAndExecute()` and, on 2006/2013 for a plain `SELECT` (not `FOR UPDATE` / `LOCK IN SHARE MODE` / `INTO OUTFILE`, not inside a transaction), calls `reconnectForRetry()` and retries once. Everything else is rethrown. Module spec updated in the same commit.

## Not fixed
Capacity. Not covered: writes on a dead connection, transactions, direct `$database->pdo` use, and other connection sites (`modules/cors_domain_management/backfill.php`, `modules/developer/_actions/_data_export_generate.php`, `modules/scrapper.php`, `modules/tenant_management/sql_script_execute.php`).

## Contract impact
None. Same tenants database; no API, flag or auth change.

## Verification
- `php -l` clean on `config/config.php` and `core/db.php`.
- Fake-PDO simulation: 2006/2013 once => retried and succeeded; twice => thrown after 1 reconnect; 1146, INSERT, UPDATE, FOR UPDATE => thrown, no reconnect.
- NOT run against a real MySQL or a browser; no automated tests (repo has none).

## Commit
sanchiconnect-saas-tenants-admin `0ccd8af`. Not deployed.

## Sentry
-4 / -A / -8 resolved under the 2026-10-07 policy. Reopen on recurrence from a build with `0ccd8af`: then it is capacity or an uncovered connection site.
