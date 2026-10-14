# SAN-1913 — tenants-admin: DB Administration link puts the tenants (cockpit) DB password in the URL, and adminer/adminer.php is publicly reachable

- Linear: https://linear.app/sanchiconnect/issue/SAN-1913 (Urgent; assignee vishali kashyap; label Bug + Repo: Tenants-Admin). Found while working on SAN-1557. Sibling of SAN-852 (sc-saas-admin).
- Repo: sanchiconnect-saas-tenants-admin. Classification: CODE_ERROR (plus ops: credential rotation).

## Problem
- `includes/core_functions.php:104` `getDeveloperMenus()` built `../adminer/adminer.php?server=<db_host>&username=<db_user>&db=<db_name>&password=<db_pass>`. These are the `.env` credentials of the **tenants DB**, shared with `sanchiconnect-saas-tenants`. The link was in the HTML of every page showing the Developer menu, and in browser history, Referer headers and access logs.
- `adminer/adminer.php` is a real file, so the `.htaccess` front-controller rule (`!-f`) never touched it. Locally it returned **200** (Adminer login page) with no session, including the `ADMINER.PHP`, `adminer.php/x`, `adminer//adminer.php` and `adminer%2ephp` variants.

## Fix
- New `db_admin.php` (app root), ported from sc-saas-admin `b29a7bf1` and adapted to this repo:
  - bootstrap: autoload, dotenv, sentry, `core/db.php`, `core_functions.php`, `config/config.php`, using the same `SCRIPT_NAME` trick so `main_url` resolves
  - login check `$_SESSION['admin_user_id']` (same as `checkLoggedIn()`), then `checkRoleUpdates()` + `checkRole("is_dev")`
  - Adminer gets its own file-based `adminer_sid` session, because the admin session is DB-backed and both use `$_SESSION["token"]`
  - auto-login with a placeholder password. `credentials()` returns the real ones server-side, and `login()` only allows the configured DB user
  - adapted for **Adminer 4.8.1** (this repo; sc-saas-admin has 5.4.2): extends the global `Adminer` class, and `css()` returns a plain URL list
- `includes/core_functions.php`: link is now `../db_admin.php`.
- `.htaccess`: `RewriteRule "^adminer/(?!adminer\.css$)" - [NC,F,L]` (same as sc-saas-admin SAN-1557 `b67d4f4a`).
- `CLAUDE.md`: Adminer guardrail updated to describe the new path.

## Verification
- Local XAMPP with a temporary vhost (removed afterwards; `httpd-vhosts.conf` restored from backup). Before: 200 for `adminer.php`, `ADMINER.PHP`, `adminer.php/x`, `adminer//adminer.php`, `adminer%2ephp`. After: all 403, `adminer/` 403, `adminer.css` 200. sc-saas-admin vhost unaffected.
- **End-to-end, old flow kept** (scratch copy of the working tree with a test-only `.env`, a throwaway MariaDB 10.4 with its own data dir, and `php -S`; all removed afterwards). Results:
  - logged out → 302 `/auth/login`
  - logged-in non-developer → 302 `/403`
  - logged-in developer → Adminer auto-logs in (302 to `?server=…&username=…&db=…`, no password) and lists the DB's tables. A SQL query run through Adminer's form (CSRF token) returns rows.
  - `adminer.css` link rendered
  - a POSTed login as `root` → "Only the configured database can be opened here.", no other DB shown
  - the admin's own DB-backed session row stays intact after using Adminer
  - the test DB password appeared in **no** response body or header
- Like the old link (`server=<db_host>`), Adminer connects to `db_host` on the default port (`db_port` isn't passed), so behaviour is unchanged.
- Repo-wide search: nothing else requests `adminer/` over HTTP (only docs, CODEOWNERS and gate exclusions), and no route starts with `adminer`.
- `php -l` on `db_admin.php` and `includes/core_functions.php`: clean.
- `scripts/gates.sh` (XAMPP PHP 8.2): platform, php-lint, ai-credit-writes pass. auth-gates fails with or without this change (26 existing failures from `git ls-files 'modules/*.php'` quoting on Windows; it only scans `modules/`). composer/phpstan/phpcs aren't installed here.

## Ops follow-up (not code)
- Rotate the tenants DB credential (it was in page HTML and possibly in logs) and update every consumer: `sanchiconnect-saas-tenants` `.env`, tenants-admin `.env`, sc-saas-admin's main-DB connection, crons.
- Deploy to `main`.

## Commit
`c724e9f` on sanchiconnect-saas-tenants-admin `ai_native_setup_vishali` (pushed 2026-10-14). SAN-1913 moved to Done; credential rotation and deploy still open.
