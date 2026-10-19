---
id: SAN-1922
title: "aktu admin panel can't connect to its tenant DB — PDO 1045 \"Access denied for user 'aktu'\" (SC-SAAS-ADMIN-14)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1922
sentry: [SC-SAAS-ADMIN-14]
repos: [admin]
related: [SAN-1562, SAN-1557, SAN-1757, SAN-1932]
commit: sc-saas-admin@f7020899 (branch ai_native_setup_vishali, pushed) — config/config.php
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1922: tenant DB "Access denied" took down the aktu admin panel

## Investigation
* **Sentry:** `PDOException: SQLSTATE[HY000] [1045] Access denied for user 'aktu'@'10.0.21.242' (using password: YES)`.
  * 158 events, 2026-10-14 16:08–16:24 UTC, production, `GET http://adm.aktu.sanchiapp.com/`.
  * Stack: `index.php:41` → `config/config.php:155` (`connectWithRetryOnTooManyConnections` → `new Medoo([... database_name sc_saas_aktu ...])`) → `core/db.php:278`, which rethrows the exception. Nothing caught it.
* **Where the credentials come from:** `config.php` takes all four tenant-DB values (`database_name`, `database_host`, `database_user`, `database_password`) **only** from the `tenant_users` row that matches `admin_domain`/`admin_custom_domain` with `active='1'` (lines 96-103, 155-160). No `.env` value is involved.
* **Why 1045 isn't retried:** `connectWithRetryOnTooManyConnections` (lines 59-75) only retries on 1040 / "Too many connections". 1045 is permanent and is rethrown at once, so every request was a fatal error: 158 events in 16 minutes.
* **Classification:** ENV_ERROR (ops). MySQL no longer accepts the password stored for `aktu`. The most likely cause is the credential rotation (SAN-1562 / SAN-1557) not updating `tenant_users.database_password`.

## Fix
### Ops (the actual outage, still open)
1. Open the `tenant_users` row for `admin_domain = adm.aktu.sanchiapp.com`, `active = 1`. Note its `database_user` (expected `aktu`), `database_name` (expected `sc_saas_aktu`), `database_host` and `database_password`.
2. On that host, run `SELECT user, host, plugin, password_last_changed, account_locked, password_expired FROM mysql.user WHERE user='aktu';` and check:
   - a host entry covers 10.0.21.242;
   - whether `password_last_changed` falls around 2026-10-14 16:08 UTC;
   - the account is not locked or expired.
3. `SHOW GRANTS` must cover `sc_saas_aktu`.
4. Make the two match. Preferred: update `tenant_users.database_password` through tenants-admin. Make sure the rotation runbook also updates `tenant_users`.
5. Check the aktu backend deployment and the `sc-saas-admin/cli/*` workers, which read the same row.
6. Events stopped at 16:24 UTC, so check whether someone already fixed it before acting.

### Code hardening (uncommitted)
`sc-saas-admin/config/config.php` (+34/-13):
* The existing tenant-DB connect is wrapped, unchanged, in `try { … } catch (PDOException $tenantConnectException)`.
* On catch it:
  * sends one Sentry event inside `\Sentry\withScope`, with tag `alert=admin-tenant-db-connect-failed` and context `{hostname}`. It captures the same exception, so it keeps grouping with ADMIN-14.
  * returns `http_response_code(503)` with `Retry-After: 30` and the existing `modules/database-connectivity-error.php` page, then `exit`.
* This mirrors the tenant-lookup 503 block at lines 129-142 (commit `6dcd70f9`).

## Blast radius
* **Success path:** same closure, arguments and `$database` assignment.
* **1040 retry:** untouched, still runs inside the `try`. Only the final outcome changes after all retries fail: a 503 page instead of a fatal error.
* **Main tenants-DB connect at `config.php:91`:** not changed.
* No backend API, flag or contract is involved.

## Verification
* `php -l config/config.php` (XAMPP PHP 8.2.12): no syntax errors, exit 0.
* Scratch run against a refused port (repo `core/db.php` + vendor Sentry SDK): the `PDOException` was caught and exactly one capture was made. This was a refused connection, not a real 1045.
* `php composer.phar gates`: exit 1.
  * Exit 127 for composer, phpstan and phpcs: the tools are not installed locally.
  * auth-gates found 0 module files, which points to the Windows checkout, not to this change.
  * platform, php-lint and ai-credit-writes passed.
  * CI must confirm.
* No automated test: there is no harness for `config.php` bootstrap.

## Open
* **Possible secret exposure:** the Sentry PHP SDK records function arguments in stack frames, and the original event shows the `new Medoo([...])` options. `core/sentry.php` `before_send` does not scrub frame vars. Check whether the tenant DB password is visible in ADMIN-14 / ADMIN-5 events; if so, scrub frame vars and rotate. Needs its own ticket.
* Follow-up: give the main-DB connect at `config.php:91` the same 503 handling.
* The 503 page says "refresh in a few seconds", which is misleading for a credentials fault. Cosmetic.
