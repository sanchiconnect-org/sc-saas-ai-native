# SAN-852 — Adminer "DB Administration" link carried the tenant DB password

**Repo:** sc-saas-admin · **Parent:** SAN-1562 (secret rotation) · **Class:** CODE_ERROR

## Problem
The Developer-zone "DB Administration" menu link put the tenant's MySQL password (`db_pass`) in the URL query string. The URL was in the page HTML for every admin instance (shared code, not just demo2), and it also ended up in browser history and server access logs.

## Root cause
`getDeveloperMenus()` in `includes/core_functions.php` built the link with `&password=` . `constant("db_pass")`. The bundled Adminer 5.4.2 only logs in through a POSTed `auth[...]` form and ignores a `password` URL parameter, so the parameter did nothing except expose the password.

## Fix (revised: one-click login kept, per Nirmal)
Developers do use this link to log in, so it still logs in with one click. The credentials are now supplied server-side instead of in the URL.
- New `db_admin.php` wrapper at the app root. It is not under `adminer/` because local stacks such as MAMP PRO alias `/adminer` to their own bundled Adminer, which shadowed it and returned a 500 in local testing:
  - Boots the admin app far enough to read the admin session, then requires a logged-in user with the `is_dev` role (roles are re-read from the DB). Otherwise it redirects to login or 403.
  - Closes the admin session and gives Adminer its own `adminer_sid` session on PHP's default file handler. It can't share the admin session: both use `$_SESSION["token"]`, and Adminer XORs it as an integer, which throws a TypeError on the app's md5 token.
  - On the first visit, logs Adminer in automatically. `adminer_object()` overrides `credentials()` to return `db_host`/`db_user`/`db_pass` server-side, and `login()` accepts only this tenant's own DB user. Adminer's session stores only a `-` placeholder as the "password".
- `includes/core_functions.php`: the menu link is now `../db_admin.php`.

## Verification
- `php -l` clean on both files.
- Tested under `php -S` with a fake app session in front (no local MySQL):
  - The first request logs in and 302s to `?server=…&username=…&db=…`.
  - The follow-up request calls `credentials()` and attempts the connection.
  - The real password is absent from all HTML responses and session files.
- Not yet tested against a real database: check on dev (thub.sanchidev.in) after deploy. Clicking DB Administration as an is_dev admin should land straight in the tenant DB; a non-dev admin should get a 403.

## Not shipped (deploy-side)
`.htaccess` files are gitignored here, so direct requests to `adminer/adminer.php` and `adminer/adminer_backup.php` can't be blocked from the repo. Those requests still reach the plain Adminer login form, which needs the password; this is unchanged from before. Recommend a deploy-side rule: `RewriteRule ^adminer/adminer(_backup)?\.php$ - [F,L]`.

## Follow-up (not code)
- Rotate the RDS credentials for every tenant whose admin served the old link (tracked under SAN-1562).

**Commit:** sc-saas-admin@b29a7bf1 (ai_native_setup)
