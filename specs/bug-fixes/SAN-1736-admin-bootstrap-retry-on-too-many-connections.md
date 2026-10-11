# SAN-1736 — admin bootstrap connects once; a transient "Too many connections" is fatal

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1736 (Sentry SC-SAAS-ADMIN-5; reopens SAN-140, which I had closed too early)
- **Repo:** sc-saas-admin · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (client resilience) over an infrastructure capacity limit

## Evidence
SC-SAAS-ADMIN-5 `PDOException: SQLSTATE[HY000] [1040] Too many connections`: 3,539 events since 2026-07-29, newest on 2026-10-06 morning. In the last 7 days all events are `environment: production`:
164 from `ip-10-0-21-214` (from 2026-10-05 04:52 UTC to 2026-10-06 06:47 UTC), 22 from `ip-10-0-21-211` (1 Oct), 13 from `ip-10-0-21-245` (3 Oct), 3 from `ip-10-0-21-212`.
The newest event is a real request, `POST http://adm.hub.startupsingam.com/application_management/edit_program_round_jury` (Chrome 152 on Windows, php 8.3.35 on apache2handler), failing in `config/config.php:50` while
connecting to `sc_pc_tenants_prod`. So this is not the dotfile-probe traffic that SAN-140's `.htaccess` fix (`b537b2eb`) addressed; that earlier closure was wrong for this issue and SAN-140 is back In Review.

## Root cause (two layers)
1. **Capacity (infra):** every admin request opens a connection to the shared tenants DB (`$mainDatabase`) and one to the tenant's own DB. Every tenant's admin panel (and the backends and the tenants API) shares that MySQL
   server, so peaks exceed `max_connections`. The remedy is MySQL `max_connections`, pooling or RDS Proxy. Code cannot make that decision.
2. **Client side (this issue):** `config/config.php` attempted each connection exactly once. MySQL refuses 1040 immediately during a spike and accepts again moments later, but one refusal made the whole request fatal
   (an uncaught `PDOException`, a fatal Sentry event, an error page).

## Fix
`config/config.php`: `connectWithRetryOnTooManyConnections(callable $connect, int $attempts = 3, int $baseDelayMs = 200)`, used for both bootstrap connections (`$mainDatabase` and `$database`, the second via a closure
over the tenant row). Retries ONLY 1040 (matched on the message, because `core/db.php` rethrows a bare `PDOException` without `errorInfo`), waiting `baseDelayMs * attempt` plus up to 100 ms jitter: at most
200 + 400 ms plus 2 x 100 ms = about 0.8 s. Every other error, including a 2002 timeout, and the last 1040, is rethrown unchanged. Comments use `/* */` per the repo's convention.

## Considered and rejected
- Persistent connections (`PDO::ATTR_PERSISTENT`): would hold one connection per Apache worker permanently, can increase the baseline, and tenant credentials differ per domain.
- Closing `$mainDatabase` after the bootstrap reads: it is used later in the request by the AI-credits modules (`includes/ai_credits_functions.php`, `modules/ai_credits/*`) and `includes/core_functions.php`
  (lines 811 to 877), so it cannot be closed early.
- Retrying 2002 (timeout): the connect already blocks for a long time, so retries would multiply the delay.

## Not fixed
Capacity. `sanchiconnect-saas-tenants-admin` has the same bootstrap pattern (SAN-414, SC-SAAS-TENANTS-ADMIN-4) and was not changed.

## Contract impact
None. The tenant row is still selected by `admin_domain` / `admin_custom_domain` exactly as before (tenant scoping invariant #5 unchanged); no API, flag or auth change. Module spec updated: `sc-saas-admin/module.spec.md`
(core bootstrap).

## Verification
- `php -l config/config.php`: no syntax errors (PHP 8.2 locally; production runs 8.3.35).
- A PHP CLI script extracted the real helper from `config.php` and ran it against fake connectors, 12 checks, all pass: success is not retried; 1040 then success returns the connection after 2 calls; two 1040s then success
  after 3; backoff measured at 107 ms and 93 ms for a 40 ms base (jitter included); exhaustion after 3 attempts rethrows the 1040 unchanged; 2002, 1045, 1049 and 2006 are not retried; a message with the text but without the
  `[1040]` code is retried; a 1040 followed by another error stops at 2 calls; the default worst case measured 669 ms (under 0.85 s).
- No automated test added: this repo has no test suite. Not run against a real MySQL or in a browser.

## Commit
sc-saas-admin `c9de651c` on `ai_native_setup_aman`. Not deployed.

## Sentry
SC-SAAS-ADMIN-5 is left **unresolved on purpose**: this reduces how many requests die in a short spike, but the cause is server capacity. Resolve it after a deploy and a quiet period, or after the capacity change.
