---
id: SAN-1989
title: "explode(): Argument #2 must be of type string, array given in index.php (SC-SAAS-ADMIN-15)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1989
sentry: [SC-SAAS-ADMIN-15]
repos: [admin]
related: [SAN-979]
commit: admin@0fc5e3bf (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1989: an array `action` query parameter crashes the admin front controller

## Root cause
* **Sentry:** `TypeError: explode(): Argument #2 ($string) must be of type string, array given`.
  * 2 events at 2026-10-20 18:49:45 UTC, production, server `ip-10-0-21-179`.
  * Request: `GET http://adm.trise.tripura.gov.in/t/index.php`. The frame's local `string` is `["aaaa"]`, so the query string was `?action[]=aaaa`.
  * The client was spoofed as Edge 12 and sent no session. This is a scanner probe, not an admin.
* **Where:** `sc-saas-admin/index.php:62` in the deployed build (`:63` on the branch before this fix): `enforceJuryNdaGate($database, (isset($_GET['action']) && $_GET['action']) ? explode("/", $_GET['action']) : array());`.
  * PHP turns `action[]=x` into an array. The checks are `isset() && truthy`, and a non-empty array passes both, so `explode()` gets an array.
  * Two more sites have the same problem: `index.php:74` (`juryNdaProtectedRoute(explode(...))`) and `index.php:80-82` (routing). `modules/common.php:10` explodes the same value as well.
* **Same class as SAN-979.** That bug was an `explode()` on a value that is sometimes already an array, fixed with an `is_array()` guard at the call site. Here the value comes straight from the query string, and a real route is always a string. So the guard goes once at the top of the front controller, not at each `explode()`.

## Fix (`sc-saas-admin/index.php`, +7 lines)
This block goes right before the FA-010 jury NDA gate, after bootstrap and before any `explode()` of `action`:

```php
if (isset($_GET['action']) && !is_string($_GET['action'])) {
    include "modules/404.php";
    exit;
}
```

* `modules/404.php` is the page the router already uses for an unknown route (`index.php:75` and the routing fallback). It does its own `checkLoggedIn()` / `checkPartnerLoggedIn()`, so a visitor with no session goes to the login page, as for any other unknown URL.
* `/* */` comments, following the repo convention.

## Blast radius / existing-flow impact
* **Happy path is identical.** Every route `.htaccess` produces (`index.php?action=$1`) and every link in the app passes a string, so `is_string()` is true and nothing changes.
* No `action` at all (the dashboard) is unaffected, because `isset()` is false.
* Only a non-string `action` (an array, from `action[]=` / `action[k]=`) is affected. It used to be a PHP fatal error (blank 500 in production) plus a Sentry event. It is now the normal 404 page.
* No flag, API contract, auth model or tenant DB selection is touched. The guard runs after `config/config.php` has already picked the tenant by `admin_domain`.

## Verification
* `php -l index.php` (XAMPP PHP 8.2.12): no syntax errors.
* An isolated XAMPP Apache 2.4 ran on `127.0.0.1:8099` (scratchpad, torn down afterwards). It served the exact `index.php` from the guard onwards, with the jury NDA functions stubbed and stub `modules/404.php`, `modules/index.php` and `modules/users/list.php`:
  * **before** (HEAD `index.php`): `?action[]=aaaa` → `Fatal error: Uncaught TypeError: explode(): Argument #2 ($string) must be of type string, array given`. This reproduces the Sentry error.
  * **after:** `?action[]=aaaa` → 404 page; `?action[x]=1` → 404 page; `?action[]=users&action[]=list` → 404 page.
  * **unchanged:** `?action=users/list` → the module; `?action=nope` → 404 page; no query string → dashboard module.
* `composer gates` cannot run here (composer is not installed). `bash scripts/gates.sh` was run with XAMPP PHP on `PATH`, using `GATES_DIFF_RANGE=HEAD`:

  ```
  0    platform
  127  composer
  0    php-lint
  0    auth-gates      (980 assertions passed, 0 unreviewed)
  0    ai-credit-writes
  127  phpstan         (not installed locally)
  127  phpcs           (not installed locally)
  ```
* No automated test was added. The repo has no harness that boots `index.php` with a crafted `$_GET`. The Apache run above is the verification.
* Contract checks: no flag, controller/DTO or tenant-scoped query is touched, so `/trace-flag`, `/audit-contract` and `/check-isolation` don't apply.

## Ops follow-ups
* None needed. The Sentry issue should stop after this deploys.

## Related / follow-ups
* SAN-979: the same `explode()`-on-an-array class, in the visibility field.
* `sanchiconnect-saas-tenants-admin/index.php:43-45` has the same latent pattern (`explode("/", $_GET['action'])` with only an `isset() && truthy` check). It has no Sentry event yet, and that repo is outside this issue's `Repo: Admin` label. A separate tenants-admin issue should port the same guard.
