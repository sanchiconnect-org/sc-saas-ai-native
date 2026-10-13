---
id: SAN-1016
title: "PDOException [2002] Operation timed out on DB connect (SC-SAAS-ADMIN-F) — local dev machines only"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1016
sentry: [SC-SAAS-ADMIN-F]
repos: [admin]
related: [SAN-140, SAN-1736, SAN-446]
commit: none. No production occurrence, so no code defect to fix
created: 2026-10-13
updated: 2026-10-13
---

# SAN-1016: the 2002 timeouts come only from developer laptops

## Investigation
* **SC-SAAS-ADMIN-F: 36 events, all `environment: local`, zero production.** Sentry already marks the group resolved, and it was last seen 2026-09-15.

  | server_name | events | window |
  | -- | -- | -- |
  | `macs-MacBook-Pro-2.local` | 26 | 2026-08-14 → 2026-09-15 |
  | `AmanK` | 7 | 2026-08-17 |
  | `192.168.1.8` | 3 | 2026-08-30 → 08-31 |

* The latest event's URL is `https://sc-saas-admin-local-nirmal/operation_cost/claims`, running PHP 8.1 CGI on macOS. These are developers' local admin vhosts. They connect to the **remote** dev MySQL, because local admin setups use the remote DB with no local database. A `[2002] Operation timed out` there means the laptop's network couldn't reach the DB host (home Wi-Fi, VPN, firewall). It does not mean connection exhaustion on the server.
* This is therefore **not** the same root cause as SAN-140 / SC-SAAS-ADMIN-5. Error 1040 is "Too many connections" on the server. Error 2002 is the client failing to reach the server at all.
* The SAN-446 environment-mis-tagging concern does not apply. None of these hosts is a deployed server: the hostnames are laptops and the URL is a `-local-` vhost.

## Existing flow (unchanged)
* `config/config.php` → `connectWithRetryOnTooManyConnections()` (SAN-1736) retries **only** error 1040. It deliberately rethrows a 2002 timeout unchanged, because the connect has already blocked for a long time and retrying would multiply the delay.

## Why no code change
The ticket proposed an explicit PDO connect timeout and a clean error page. Neither is justified by evidence:
* **Connect timeout:** production has never hit a 2002. A shorter timeout than the current default could turn today's slow-but-successful production connects into new failures. That would break existing flow for no observed benefit.
* **Clean error page:** this changes the admin's fatal-on-DB-down behaviour on every page, including how the error is captured, to fix a condition seen only on dev laptops.

If a 2002 ever appears with `environment: production` (or from a deployed host), reopen this ticket. A timeout plus error-page change can then be designed against real data.

## Verification
* Sentry aggregate by `environment` and `server_name` over 90 days, shown above. The group is resolved in Sentry with no recurrence in about 4 weeks.
* Read `core/sentry.php` (environment comes from `SENTRY_ENVIRONMENT`) and the bootstrap connect path in `config/config.php`. Nothing was modified.
* Contract checks do not apply: there is no flag, API/DTO, auth or tenant-scoping change.
