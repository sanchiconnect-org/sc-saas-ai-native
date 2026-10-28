---
id: SAN-1973
title: "PDO 1040 \"Too many connections\" recurred after SAN-1757 / SAN-1932 (SC-SAAS-TENANTS-ADMIN-4)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1973
sentry: [SC-SAAS-TENANTS-ADMIN-4]
repos: [tenants-admin]
related: [SAN-1757, SAN-1932, SAN-1974, SAN-1736, SAN-1876]
commit: tenants-admin@b7483af (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1973: a second scanner burst on the dev tenants-admin, and probes the SAN-1932 rules don't cover

## Investigation
* **Sentry, 14-day window (141 events):** all are `environment: local` (dev). None is production.

  | Burst (UTC) | Events | Host / container | URLs |
  |---|---|---|---|
  | 2026-10-10 20:43:27-29 | 7 | `adm.tenants.sanchidev.in` / `aeba05ccafd9` | `/@fs/...` (already analysed in SAN-1932) |
  | 2026-10-21 19:10:14-22 (8 s) | 134 | `http://122.176.150.231/` (raw IP) / `9fb4005fe495` | `/.git/*`, `/<dir>/.git/*`, `/.svn/*`, `/.hg/*`, `/.bzr/*`, `/source.tar.gz`, `/repo.zip`, `/database.sql`, `/dump.sql`, `/app.js.map`, `/angular.json`, `/variables.tf`, `/webpack.config.js`, `/CVS/Root`, `/git/HEAD`, `/code/config`, ... |

  * **Correlation with SC-SAAS-ADMIN-5 (SAN-1974):** sc-saas-admin had 62 events in the same second on 10-10, and 13 events at 2026-10-21 19:13:39, 3 minutes after this burst. The same scanner hit both apps on the shared dev MySQL. It is one DB-server event per burst.
  * The raw-IP host means the dev Apache answers a bare-IP request with the tenants-admin vhost (default vhost), so internet-wide scanners reach it without knowing a hostname.
* **The SAN-1757 retry is deployed and ran out.** The stack is `index.php:23` → `config/config.php:80` (`connectWithRetryOnTooManyConnections`) → `:67` → `core/db.php:289`. All 3 attempts hit 1040, as in SAN-1932.
* **The SAN-1932 `.htaccess` rules are not deployed.**
  * Commit `55fa313` is on `ai_native_setup_vishali` only. It is not on `origin/ai_native_setup`, `origin/development` or `origin/main`.
  * Its dot-segment rule alone would have answered every `/.git`, `/.svn`, `/.hg`, `/.bzr`, `/.env.*` and `/.github` probe with a 404, with no PHP involved.
* **Not covered even after `55fa313`:** source/backup downloads and source maps (`.zip`, `.tar.gz`, `.sql`, `.map`, `.json`, `.tf`). Each fell through the catch-all to `index.php` and opened a tenants-DB connection.
* **Does the app leak connections?** No.
  * No `PDO::ATTR_PERSISTENT` or `pconnect` outside `vendor/`.
  * A web request opens exactly one bootstrap connection and releases it at script end. `core/db.php` reconnects once on 2006/2013, replacing the handle.
  * The per-tenant connection loops (`client_stats/list.php`, `cors_domain_management/backfill.php`) and the single connections in `sql_script_execute.php` / `_data_export_generate.php` are operator-only pages behind login and `is_dev` / super admin. A scanner can't reach them.
  * `health.php` opens one short connection.
  * The pressure comes from every junk URL costing one connection before routing can 404.

## Fix (`sanchiconnect-saas-tenants-admin/.htaccess`, +8 lines)
This rule goes after the SAN-1932 rules and before the `index.php` catch-all, in the same style as sc-saas-admin's SAN-1876 rule:

```apache
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule "\.(json|ya?ml|env|tfstate|tf|hcl|ini|sql|bak|zip|tar|gz|tgz|rar|7z|map)$" - [NC,R=404,L]
```

* Module routes are extensionless. There is no `modules/**` file whose route would end in these extensions, and no link built from `main_url` or in templates ends in one, so these requests can only be probes.
* `!-f` keeps every real file served as before (`composer.json`, `contracts/ai-credits.schema.json`, theme assets).
* In the 100 sampled events of the 10-21 burst, the SAN-1932 dot-segment rule plus this rule answer about 75 from Apache.
* The remaining extensionless or `.js` / `.py` / `.php` probes (`/CVS/Root`, `/git/HEAD`, `/webpack.config.js`, `/settings.py`, `/wp-config.php`) still reach PHP. They were left alone on purpose: they look like routes or like real asset types, and filtering them would risk real requests. Rate-limiting at the edge (ops item 3) is the lever for those.

## Blast radius / existing-flow impact
* **Happy path is identical.** All module routes (`/`, `/auth/login?…`, `/client_stats/list`, `/ai_credits/packages`, `/tenants/edit/12`) still go to `index.php`.
* Real files are still served, and the existing SAN-1913 adminer and SAN-1932 rules behave the same.
* Only a request for a **non-existent** file with one of the listed extensions changes: it used to get PHP + a DB connection + the 404/login redirect, and now gets an Apache 404.
* No PHP changed. No flag, API, auth or shared-DB schema is touched.

## Verification
* An isolated XAMPP Apache 2.4 + PHP 8.2 ran on `127.0.0.1:8099` (scratchpad, `httpd -t` Syntax OK, torn down afterwards). It used this exact `.htaccess` with a stub `index.php` that echoes `action`, with no `.env` and no DB:
  * **404 from Apache (index.php not reached):** `/source.tar.gz`, `/repo.zip`, `/release.zip`, `/SRC.ZIP`, `/database.sql`, `/dump.sql`, `/app.js.map`, `/static/js/app.js.map`, `/angular.json`, `/codemeta.json`, `/variables.tf`. The existing rules still give 404 for `/.git/config`, `/.env.old` and `/@fs/proc/self/environ`.
  * **Unchanged, 200 via index.php with the right `action`:** `/`, `/auth/login?x=1`, `/client_stats/list`, `/ai_credits/packages`, `/tenants/edit/12`, `/some/file.csv`, `/.well-known/acme-challenge/x`.
  * **Unchanged, 200 as real files:** `/composer.json`, `/contracts/ai-credits.schema.json`, `/themes/default/assets/a.css`, `/adminer/adminer.css`.
  * **Unchanged, 403:** `/phpinfo.php`, `/adminer/adminer.php`.
* `composer gates` cannot run here (composer is not on `PATH`). `bash scripts/gates.sh` was run with XAMPP PHP on `PATH`, using `GATES_DIFF_RANGE=HEAD`:

  ```
  0    platform
  127  composer
  0    php-lint
  0    auth-gates
  0    ai-credit-writes
  127  phpstan   (not installed locally)
  127  phpcs     (not installed locally)
  ```
* No automated test was added. The repo has no `.htaccess` test harness, so the Apache run above is the verification.
* Contract checks: none apply (no flag, API/DTO or tenant-scoped query).

## Ops follow-ups
1. **Deploy `55fa313` (SAN-1932) together with this change** to the dev tenants-admin. Container `9fb4005fe495` doesn't have the dot-segment rules yet.
2. **Stop serving tenants-admin on the bare IP** (`122.176.150.231`). Give the dev Apache a default vhost that returns 404/444 for unknown `Host` headers, so IP-range scanners never reach PHP.
3. Rate-limit scanner bursts at the dev edge (`limit_req` per IP, or blocking empty user agents). This covers route-shaped probes as well.
4. Set `SENTRY_ENVIRONMENT=development` on the dev hosts (open since SAN-1932).
5. The SAN-1932 infra items (`max_connections`, `wait_timeout`, `PROCESSLIST` by user/host on the shared dev MySQL) still apply.
6. **[DESIGN DECISION PENDING — dev lead]** Should the bootstrap connect catch the final 1040 and return 503 + one Sentry event, like sc-saas-admin's SAN-1922 tenant-DB catch (a SAN-1932 code follow-up)?
   * `modules/database-connectivity-error.php` in this repo currently shows the "Direct access is not allowed" text, so it would need its own 503 copy first.
   * It doesn't reduce connection pressure.

## Related
* SAN-1757: bootstrap retry.
* SAN-1932: first burst, dot-segment `.htaccess` rules, infra recommendations.
* SAN-1974: the same bursts in sc-saas-admin.
* SAN-1876: sc-saas-admin's equivalent extension rule.
