---
id: SAN-1972
title: "aktu tenant DB PDO 1045 \"Access denied\" still unresolved in Sentry after SAN-1922 (SC-SAAS-ADMIN-14)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1972
sentry: [SC-SAAS-ADMIN-14]
repos: [admin]
related: [SAN-1922, SAN-1736]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1972: ADMIN-14 is the same 158 events SAN-1922 already handled

## Investigation
* **Sentry:** `PDOException: SQLSTATE[HY000] [1045] Access denied for user 'aktu'@'10.0.21.242' (using password: YES)`.
  * 158 events, **first seen 2026-10-14 16:08:48 UTC and last seen 2026-10-14 16:24:24 UTC**. That is one 16-minute window, with nothing in the 8 days since.
  * Production, server `ip-10-0-21-242`, `GET http://adm.aktu.sanchiapp.com/`. The latest event's user agent is `Slackbot-LinkExpanding`: a link to the panel was pasted in Slack and unfurled.
  * The issue is "unresolved / ongoing" only because nobody resolved it in Sentry. It has not fired again.
* **The events came before the SAN-1922 code existed.**
  * The stack is `index.php:41` → `config/config.php:155` (`$database = connectWithRetryOnTooManyConnections(...)`) → `core/db.php:278`, with `handled: no`.
  * `config.php:155` is the tenant-DB connect line in `origin/main` and `origin/development`, which have no `try`.
  * In the current branch that line is `:161`, inside the SAN-1922 `try { … } catch (PDOException $tenantConnectException)`. The catch would have answered with a 503 page and a `captureException` (with tag `alert=admin-tenant-db-connect-failed`).
  * SAN-1922 commit `f7020899` is dated 2026-10-15 14:29 IST (08:59 UTC), about 16.5 hours after the last event.
* **Deploy-lag check (fetched 2026-10-22):**
  * `f7020899` **is** on `origin/ai_native_setup` and on the working branch `ai_native_setup_vishali`.
  * It is **not** on `origin/development`, `origin/stagingdemo` or `origin/main`.
  * So production still runs code where a tenant-DB connect failure is a PHP fatal error. The 503 handling exists only on the integration branch.
* **Was the credential fixed?** Probably yes, but this is not confirmed.
  * Production has none of the 503 code, so if the password were still wrong, every request to `adm.aktu.sanchiapp.com` would still raise this same unhandled event.
  * Zero events in 8 days means one of two things: the `aktu` credential / `tenant_users` row was corrected around 16:24 UTC on 2026-10-14, or nobody has opened the panel since. The first is much more likely, but nobody has confirmed it in a ticket.

## Fix
None. Current code has no defect.
* The tenant-DB connect on `ai_native_setup_vishali` (`config/config.php:160-188`) already catches the exception and returns 503 + `Retry-After: 30` + one Sentry event.
* The outage cause was an ops credential mismatch, handled under SAN-1922.

## Blast radius / existing-flow impact
* No change.

## Verification
* Read `config/config.php` on the working branch, and on `origin/main` / `origin/development` via `git show`. The line numbers match the Sentry frame, as described above.
* `git merge-base --is-ancestor f7020899 <branch>`: yes for `origin/ai_native_setup`; no for `origin/development`, `origin/stagingdemo` and `origin/main`.
* Sentry issue metadata: last seen 2026-10-14T16:24:24Z, 158 occurrences in total, the same count SAN-1922 analysed.
* No code changed, so no gates or tests were run for this issue.

## Ops follow-ups
1. Confirm in the SAN-1922 thread that the `aktu` `tenant_users.database_password` matches MySQL. SAN-1922 ops steps 1-6 apply. A plain load of `adm.aktu.sanchiapp.com` that reaches the login page is enough.
2. Promote `f7020899` (together with the rest of `ai_native_setup`) through `development` → `stagingdemo` → `main`. Until then, a future credential rotation will again show admins a fatal error instead of the 503 page.
3. Then **resolve SC-SAAS-ADMIN-14 in Sentry** (for example "resolved in next release"). It stays "unresolved" only because it was never resolved.
4. Recommended close: as a duplicate of SAN-1922 once step 1 is confirmed.

## Related
* SAN-1922: original investigation, ops runbook and the 503 hardening.
* SAN-1736: the 1040 retry wrapper the tenant connect runs inside.
