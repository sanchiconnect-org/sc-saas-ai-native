---
id: SAN-1932
title: "PDO 1040 \"Too many connections\" recurred after the SAN-1757 retry fix (SC-SAAS-TENANTS-ADMIN-4)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1932
sentry: [SC-SAAS-TENANTS-ADMIN-4]
repos: [tenants-admin]
related: [SAN-1757, SAN-413, SAN-414, SAN-1922]
commit: sanchiconnect-saas-tenants-admin@55fa313 (branch ai_native_setup_vishali, pushed) — .htaccess
created: 2026-10-15
updated: 2026-10-16
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

## Root cause (confirmed 2026-10-16 from the Sentry events)
* All 7 events in the 14-day window landed within **3 seconds** (2026-10-10 20:43:27-29 UTC).
* They all came from container `aeba05ccafd9` on **`adm.tenants.sanchidev.in`**, tagged `environment: local`.
* **The requests were a vulnerability-scanner burst, not operator traffic:**
  * user agents rotate between spoofed DuckAssistBot, Bravebot, Bytespider, PerplexityBot and Baiduspider;
  * URLs are `/@fs/.env`, `/@fs/app/.env`, `/@fs/var/task/.env`, `/@fs/src/.env`, `/@fs/proc/self/cmdline` and `/@fs/..%252f…/proc/self/environ`. That is Vite `@fs` path traversal plus `.env` hunting.
* **The SAN-1757 retry *is* deployed.** The stack shows `config.php(80) connectWithRetryOnTooManyConnections` → `config.php(67)` → `db.php(289)`, so all 3 attempts hit 1040.
* **Mechanism:**
  * `.htaccess` rewrites every non-existent path to `index.php`.
  * `index.php` loads `config/config.php`, which opens the tenants-DB connection before routing can reach `modules/404.php`.
  * So every junk request costs one MySQL connection, and a parallel scanner burst saturates the shared dev MySQL.
  * Live check: `/@fs/.env` on the dev host returns 302 (PHP ran and redirected to login), not 404.
* **Side finding (security):** `GET /phpinfo.php` returns **200** on `adm.tenants.sanchidev.in`.
  * `phpinfo.php` (`<?php phpinfo();`, initial commit) is tracked in the docroot, and nothing links to it.
  * `phpinfo()` prints the loaded environment, which includes the `.env` DB credentials and keys.
  * The body was deliberately not fetched.

## Fix (tenants-admin `.htaccess`, `55fa313`)
New rules go after the adminer rule and before the `index.php` catch-all, so they are answered by Apache with no PHP and no DB connection:
* `^@fs/` → 404.
* Any dot-segment `(^|/)\.` except `/.well-known/` → 404. This covers `/.env`, `/.git/…` and library dotfiles.
* `(^|/)proc/(self|<pid>)/` → 404.
* `^phpinfo\.php$` → 403.

No module route starts with `@`, contains a dot-segment or has a `proc/<pid>/` segment (checked against `modules/`), and nothing references `phpinfo.php`. Real routes are untouched.

### Verification
* Ran an isolated XAMPP Apache 2.4 + PHP 8 instance on `127.0.0.1:8099`. It used this exact `.htaccess` with a stub `index.php` (no `.env`, no DB), and was torn down afterwards.
  * All 6 Sentry scanner URLs, plus `/.env`, `/.git/config`, `/proc/self/environ` and `/foo/proc/1/environ` → **404**, without reaching `index.php`.
  * `/phpinfo.php` and `/PHPINFO.PHP` → **403**.
  * These are **unchanged** (200 via `index.php` with the right `action`): `/`, `/auth/login` (with a query string), `/client_stats/list`, `/ai_credits/packages`, `/tenants/edit/12`, `/process/list`, `/procurement`, `/some/file.csv`.
  * Static assets: `/themes/…/a.css` → 200; `/adminer/adminer.css` → 200.
  * `/adminer/adminer.php` → 403 (existing SAN-1913 rule still applies).
  * `/.well-known/acme-challenge/*` → 200.
* `httpd -t`: Syntax OK.
* `scripts/gates.sh`:
  * passed: platform 0, php-lint 0, ai-credit-writes 0;
  * not installed on this machine: composer 127, phpstan 127, phpcs 127;
  * auth-gates 1 is a **Windows-local false failure**. Git Bash rejects the `':!:vendor'` pathspec (`fatal: Invalid path`), so the file list is empty and existing files show as "no longer exists". The gate only reads PHP, and no PHP file changed. CI (Linux) is the authority.
* No automated test added: there is no `.htaccess` test harness in the repo. The Apache run above is the verification.
* Contract checks: no flag, API/DTO or tenant-scoped query touched.

## Remaining infra and code follow-ups (not needed to close this issue)
**Infra:**
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
* ~~Confirm the tenants-admin deploy date relative to 2026-10-11.~~ Answered: the retry frame is in the stack, so `0ccd8af` is deployed.
* ~~Confirm whether the Sentry events show the retry frame.~~ Answered: yes, and all 3 attempts hit 1040.
* The dev host reports `environment: local` to Sentry. `SENTRY_ENVIRONMENT` in the dev server's `.env` should be `development`, so dev noise can be filtered from production triage.
* phpinfo exposure: after the `.htaccess` deploy, consider deleting `phpinfo.php` and rotating the dev `.env` secrets. Anyone could read them while the page was public.
