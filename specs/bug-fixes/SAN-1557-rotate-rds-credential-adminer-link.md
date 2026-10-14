# SAN-1557 — Rotate the production RDS credential exposed in SAN-852 and check every tenant's admin panel for the same link

- Linear: https://linear.app/sanchiconnect/issue/SAN-1557 (Urgent, due 2026-10-13; assignee Nirmal Singh; label Bug + Repo: Admin). Related: SAN-852 (link fix, Done), PRA-1.
- Repo: sc-saas-admin. Classification: mostly ENV_ERROR / operations (credential rotation and consumer updates are infra work), plus one CODE_ERROR left open by SAN-852.

## Evidence (checked in code, 2026-10-14)
1. **SAN-852's fix isn't in production.** `b29a7bf1` (2026-10-13, new `db_admin.php` that logs in to Adminer server-side, and the link becomes `../db_admin.php`) is only on the `ai_native_setup*` branches. `origin/main` `includes/core_functions.php:165` still builds `../adminer/adminer.php?server=…&username=…&db=…&password=<db_pass>`.
2. **Every tenant is exposed, not only demo2.** `db_host/db_user/db_name/db_pass` come from each tenant's own `tenant_users` row (`config/config.php:172-181`), and the menu template is shared. Every tenant's admin panel on the `main` code renders that tenant's own DB password.
3. **Adminer was reachable directly, with no admin session (still open on SAN-852's branch).** `adminer/adminer.php` and an older copy `adminer/adminer_backup.php` are real files, so the root `.htaccess` routing rule (`!-f`) never touches them. Locally both returned **200** (the Adminer login page) with no session. Anyone with a leaked credential could log in from the internet. `db_admin.php`'s comment "this wrapper is now the only way into Adminer" wasn't true.
4. **tenants-admin has the same leak, not covered by SAN-852.** `sanchiconnect-saas-tenants-admin/includes/core_functions.php:104` puts the **tenants (cockpit) DB** password in the same Adminer link, and `adminer/adminer.php` is public there too. That's a different repo, so it needs its own issue.

## Fix (code part, sc-saas-admin)
Root `.htaccess`: `RewriteRule "^adminer/(?!adminer\.css$)" - [NC,F,L]` blocks every HTTP request under `adminer/` except the theme CSS. `db_admin.php` still works because it `include()`s `adminer/adminer.php` from PHP, which rewrite rules don't affect.
Files: `sc-saas-admin/.htaccess` (+7 lines).

## Verification (local XAMPP, admin.localhost)
- Before: `adminer/adminer.php` 200, `adminer/adminer_backup.php` 200.
- After: 403 for `adminer/adminer.php`, `ADMINER.PHP`, `adminer_backup.php`, `adminer.php/x` (path-info), `adminer//adminer.php`, `adminer%2ephp`, `adminer.php?server=…`, `adminer/`. `adminer/adminer.css` 200. `db_admin.php` 302 to login without a session (unchanged). `auth/login` 200 (routing unchanged).
- Not verified: the logged-in `db_admin.php` → Adminer flow with an is_dev session (it doesn't go through `.htaccess` for the PHP include; only `adminer.css` is fetched by the browser, and that's allowed).
- `scripts/gates.sh` (XAMPP PHP 8.2): platform, php-lint, ai-credit-writes pass. auth-gates fails with or without this change (its "file no longer exists" errors look like a Windows path issue). composer/phpstan/phpcs aren't installed here. No automated test: sc-saas-admin has no HTTP test harness.

## Ops follow-up (not code)
- Deploy `b29a7bf1` + this change to `main` for every tenant panel.
- Rotate the DB password of **every tenant** whose panel showed the developer menu on the old code (scope is wider than `saasdemo2`), and update each `tenant_users.database_password` plus any backend `.env`/cron that holds it.
- tenants-admin: **SAN-1913** (filed 2026-10-14) to port SAN-852 + this `.htaccess` rule, and rotate the tenants DB credential.
- Record the rotation date in the rotation log. A second person confirms the link no longer renders a secret.

## Commit
`b67d4f4a` on sc-saas-admin `ai_native_setup_vishali` (pushed 2026-10-14). SAN-1557 is In Review; rotation is still open.
