---
id: SAN-1017
title: "fetchSaaSSettingsFromSanchiConnect connect ETIMEDOUT 122.176.150.231:443 at bootstrap (SC-SAAS-BACKEND-1H) — infra, no longer recurring"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1017
sentry: [SC-SAAS-BACKEND-1H]
repos: [backend]
related: [SAN-895, SAN-896, SAN-897]
commit: none. Infra/network issue, not recurring; the proposed "fail soft" would break functionality
created: 2026-10-13
updated: 2026-10-13
---

# SAN-1017: startup settings fetch timing out

## Investigation
* **Path:** `main.ts` → `app.listen()` → `GlobalService.onApplicationBootstrap()` → `getSAASSettings()` → `SanchiConnectAPIService.fetchSaaSSettingsFromSanchiConnect()`. That last call is `GET ${SANCHICONNECT_API_BASE_URL}/v1/public/global/tenant-settings/<APP_DOMAIN>`, and it throws `InternalServerErrorException` on any error. The bootstrap promise rejects (`mechanism: onunhandledrejection`), so that container never starts serving.
* **SC-SAAS-BACKEND-1H: 90 events.**
  * **About 26 are production**, across about 18 ECS hosts, in deploy-wave clusters: 08-10/11, 08-17 17:13, 08-18 08:02–10:45, and 08-31 16:04 → 09-01 00:54. When the tenants API host (`122.176.150.231:443`) timed out, the starting container failed and ECS replaced it.
  * **The rest are `environment: local`**: Docker containers on developer machines, 08-24 → 09-07.
* **No longer recurring.**
  * The last production event was 2026-09-01. There have been none since, through at least two fleet-wide redeploys (10-03 and 10-11).
  * There are no production errors mentioning that host or path in the last 30 days.
  * Sentry marks the group resolved.
  * Most likely the network path to that host was fixed or changed on the infra side. The env value could not be confirmed from here, because `.env` read access was not granted.
* **Invariant #5 holds.** The request is for this deployment's own `APP_DOMAIN`, with its own `x-hostname`. There is no cross-tenant reference.

## Why the proposed "fail soft" was not applied
`getSAASSettings()` fills the global `saasSettings` (via `segregateSAASData`) and schedules the cron jobs (`cronService.setCronJobs()`). `saasSettings` includes `THIRD_PARTY_SERVICE_BASE_URL` (SMS, email, video, chat) and `IMAGEKIT_URL`. A fresh container has no last-known settings to keep, so failing soft would start the backend with empty settings. SMS, email, image URLs and crons would then fail silently. Refusing to start, the current behaviour, is safer, because ECS retries the container.

## Decision
No code change (user decision, 2026-10-13). Reopen if a production event reappears.

Optional hardening, considered and not applied: retry the startup fetch 2–3 times with a short backoff, only on network errors (`ETIMEDOUT`/`ECONNREFUSED`/`ECONNRESET`/`EHOSTUNREACH`). Behaviour on success and on final failure would be unchanged.

## Verification
* Sentry aggregate by `environment` and `server_name` over 90 days, plus a 30-day production search for the host and path (none found).
* Code read: `sanchiconnect.service.ts` and `global.service.ts` (`onApplicationBootstrap` and `getSAASSettings`). Nothing was modified.
* Contract checks: no change to the tenant-settings contract, flags, API or auth.
