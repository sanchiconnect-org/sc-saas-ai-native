---
id: SAN-1974
title: "PDO 1040 \"Too many connections\" recurred after SAN-1736 / SAN-1876 (SC-SAAS-ADMIN-5)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1974
sentry: [SC-SAAS-ADMIN-5]
repos: [admin]
related: [SAN-1736, SAN-1876, SAN-1973, SAN-1932, SAN-1922]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1974: the ADMIN-5 recurrence is scanner traffic on a stale dev build, not production

## Investigation
* **Sentry, 14-day window (75 events):** every event is `environment: local`, on the dev hosts (`*.sanchidev.in`, Docker containers `d77225ea76e3` and `d3cbd07aa224`, geo Noida). **None is production.**

  | Burst (UTC) | Events | Hosts | URLs |
  |---|---|---|---|
  | 2026-10-10 20:43:26-29 (3 s) | 62 | `adm.nasscom`, `adm.sanchiconnect`, `adm.thub` `.sanchidev.in` | `/@fs/proc/self/environ`, `/key.pem`, `/terraform.tfstate`, `/secrets.yml`, `/firebase-*.json`, `/__vite_rsc_findSourceMapURL`, `/api/graphql`, `/backoffice`, ... |
  | 2026-10-21 19:13:39 (1 s) | 13 | `adm.nasscom`, `adm.sinemumbai` `.sanchidev.in` | `/users`, `/studio`, `/checkout`, `/analytics`, `/chat`, `/swagger`, `/api-docs`, `/admin/settings`, ... |

  * Both bursts have an empty user agent and dozens of distinct guessed paths per second, which is a vulnerability scanner.
  * **Correlation with SC-SAAS-TENANTS-ADMIN-4 (SAN-1973):** tenants-admin had 7 events at 2026-10-10 20:43:27-29 (the same second) and 134 events at 2026-10-21 19:10:14-22, 3 minutes before this app's 19:13:39 burst. The same scanner swept every vhost on the shared dev MySQL each time. **It is one DB-server event per burst, not two independent bugs.**
* **The dev host runs a build older than SAN-1736.**
  * The latest event's stack is `index.php:38` → `config/config.php:50` (`$mainDatabase = new Medoo(array(...` with no retry wrapper) → `core/db.php:278`.
  * In every branch since SAN-1736 (`c9de651c`, 2026-10-06), that connect is `$mainDatabase = connectWithRetryOnTooManyConnections($connectMainDatabase);` at `config.php:91`, and `index.php` includes `config.php` at line 40-41.
  * So container `d77225ea76e3` serves code from before 2026-10-06. `origin/development` (`27f3aaa2`, 2026-10-12) already has the retry.
  * The SAN-1876 `.htaccess` probe rules (`a834a578`) would have answered most of the 10-10 burst (`@fs/`, `__vite`, `*.json|yml|tfstate|...`) with a 404 from Apache. They are **not** on `origin/development` or `origin/main`, only on `ai_native_setup` / `ai_native_setup_vishali`.
* **Does the app leak connections?** No.
  * No `PDO::ATTR_PERSISTENT` or `pconnect` anywhere outside `vendor/`.
  * Each web request opens the tenants (main) DB connection plus the tenant DB connection, holds both for the request and releases them at script end. During a failed tenant lookup it reconnects up to 2 more times, each replacing the previous one.
  * Other `new Medoo` / `new PDO` sites are the `cli/` workers (own process, one pair), `health.php` (one short connection) and `includes/startup_recognition_id_functions.php`. None loops opening connections per request.
  * The cost is per request, not a leak: every non-existent URL reaches `index.php` through the `.htaccess` catch-all and opens 2 connections before routing can 404. That is what a scanner burst multiplies.
  * The 10-21 URLs (`/users`, `/chat`, ...) look like real routes, so `.htaccess` cannot filter them without risk.

## Fix
None for this issue. Current code has no defect.
* The current branch has the SAN-1736 retry (`config/config.php:60-91`) and the SAN-1876 `.htaccess` probe rules.
* A 1040 that survives all 3 retries is still rethrown on purpose, per the SAN-1736 decision ("the last 1040 is rethrown unchanged"). For the main tenants-DB connect at `config.php:91`, that means a PHP fatal error instead of the 503 page SAN-1922 gives the tenant-DB connect.
  * **[DESIGN DECISION PENDING — dev lead]** Should the main connect also catch → 503 + one Sentry event? It is a failure-path-only change, but it does not reduce connection pressure or Sentry volume.

## Blast radius / existing-flow impact
* No change.

## Verification
* Sentry Discover, `message:"Too many connections"`, 14 days, grouped by project / environment / server: 4 rows, all `local`. The admin rows are 71 events on `d77225ea76e3` (10-10 20:43:26 to 10-21 19:13:39) and 4 on `d3cbd07aa224` (10-10 20:43:27-29).
* `git show c9de651c^:config/config.php` has `new Medoo(` at line 50, which matches the event frame. `origin/development` has the retry at `:91`.
* `git merge-base --is-ancestor a834a578 origin/development` and `… origin/main`: both no.
* No code changed, so no gates or tests were run for this issue.

## Ops follow-ups
1. **Redeploy the dev admin containers** (`d77225ea76e3`, `d3cbd07aa224`) from the current branch. They serve code from before 2026-10-06.
2. **Promote SAN-1736 + SAN-1876 + SAN-1922** (`c9de651c`, `a834a578`, `f7020899`) through `development` → `stagingdemo` → `main`. SAN-1876's `.htaccess` is on neither `development` nor `main`.
3. Set `SENTRY_ENVIRONMENT=development` in the dev hosts' `.env` (already raised in SAN-1932), so dev scanner noise can be filtered out of production triage.
4. Rate-limit or WAF-block scanner bursts at the dev load balancer / nginx in front of `*.sanchidev.in` (for example `limit_req` per IP, or blocking empty user agents). This is the only lever for route-shaped probes like `/users` and `/chat`.
5. Capacity on the shared dev MySQL (`max_connections`, `wait_timeout`, `PROCESSLIST` by user/host) stays as recommended in SAN-1932.
6. Recommended: resolve SC-SAAS-ADMIN-5 in Sentry after step 1. A recurrence after that with a `connectWithRetryOnTooManyConnections` frame would be real exhaustion.

## Related
* SAN-1736: bootstrap 1040 retry.
* SAN-1876: `.htaccess` bot secret-probe rules.
* SAN-1973: the same bursts in tenants-admin.
* SAN-1932: tenants-admin infra recommendations.
* SAN-1922: 503 pattern for the tenant-DB connect.
