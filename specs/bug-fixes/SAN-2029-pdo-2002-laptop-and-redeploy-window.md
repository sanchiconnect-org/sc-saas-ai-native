---
id: SAN-2029
title: "PDO 2002 timed out / connection refused: developer laptop and one redeploy-window refusal"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2029
sentry: [SC-SAAS-ADMIN-F, SC-SAAS-TENANTS-ADMIN-4]
repos: [admin, tenants-admin]
related: [SAN-1016, SAN-1736, SAN-1757, SAN-1932, SAN-1973, SAN-1974]
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2029: no code defect behind either 2002

## Investigation
**ADMIN-F (`2002 Operation timed out`)**
* All 36 events since 2026-08-14 are `environment: local`, from developer laptops: `macs-MacBook-Pro-2.local` (Nirmal's local vhost), `AmanK` and `192.168.1.8`.
* The event that regressed it was at 2026-10-26 02:19:18Z: Nirmal's laptop, PHP 8.1 CGI, on `/application_management/submission-application-management/7/tech-transformer`. Stack `index.php:45` → `config/config.php:91` → `core/db.php:278`, which is current code.
* Same conclusion as SAN-1016. The SAN-1736 retry deliberately skips 2002 (`config/config.php:50-58`).

**TENANTS-ADMIN-4 (title now `2002 Connection refused`)**

| Date (UTC) | Error | Events | Environment | Container |
|---|---|---|---|---|
| 2026-09-29 | 1040 | 58 | production | `df8b2ba2697f` |
| 2026-10-10 | 1040 | 7 | local | `aeba05ccafd9` |
| 2026-10-21 | 1040 | 134 | local | `9fb4005fe495` |
| 2026-10-22 07:58 | 2002 | **1** | local | `e5c367c7d760` |

* The single 2002 came from `SentryUptimeBot` on `adm.tenants.sanchidev.in`, on a new container ID right after that morning's deploy. That points to a restart window.
* The stack shows the SAN-1757 retry is deployed and correctly doesn't retry 2002.

## Root cause
Infra/environment, not code:
* laptops that can't reach the remote dev DB;
* one transient refusal during a container restart.

## Fix
None in code.

## Blast radius / existing-flow impact
None.

## Verification
Read-only.

## Ops follow-ups
* On developer laptops, unset `SENTRY_DSN` or set `SENTRY_ENVIRONMENT=development-laptop` in the local `.env`.
* On dev hosts, set `SENTRY_ENVIRONMENT=development`.
* Deploy tenants-admin `55fa313` (SAN-1932) and `b7483af` (SAN-1973). They are still only on `ai_native_setup_vishali`.
* If several 2002s appear outside deploy windows, check the dev MySQL uptime logs.
* Still pending with the dev lead (from SAN-1973/1974): turn a final bootstrap connect failure into a 503 page.
