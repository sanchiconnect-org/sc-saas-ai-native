---
id: SAN-1931
title: "fetchSaaSSettingsFromSanchiConnect throws on a transient cockpit 502 (SC-SAAS-BACKEND-1H)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1931
sentry: [SC-SAAS-BACKEND-1H]
repos: [backend]
related: [SAN-407, SAN-1017]
commit: sc-saas-backend@4843fd2c (branch ai_native_setup_vishali, pushed) — src/modules/global/global.controller.ts
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1931: cache-clear refresh turns a cockpit 502 into a 500

## Root cause
* **Sentry:** `InternalServerErrorException: Request failed with status code 502` in `SanchiConnectAPIService.fetchSaaSSettingsFromSanchiConnect`, 2 events on 2026-10-14.
* `sanchiconnect.service.ts:31-48` turns any axios error into `InternalServerErrorException`.
* `GlobalService.getSAASSettings()` (`global.service.ts:180`) fetches live, with no fallback. Its callers:
  1. **`onApplicationBootstrap`** (`global.service.ts:176`): no cache exists yet, so it's left as is.
  2. **`PATCH public/global/saas/settings`**: an explicit refresh triggered by tenants-admin (`resetAPISaaSSettings`). Left as is, because reporting success after a failure would be false.
  3. **`GET public/global/clear/cache/all`** (`global.controller.ts` ~300):
     * sc-saas-admin calls it after every settings save, from `clearSettingsAPICache()` (`includes/core_functions.php:4613`) and the maintenance page, and ignores the response;
     * it is the most frequent live caller and the likely source of the events (not confirmed against Sentry).
  4. **`getAdminConsoleUrl`**: already handled by SAN-407.

## Fix
`global.controller.ts`:
* Added a `Logger`.
* In `clearCacheForKey('all')`, the `getSAASSettings()` call is wrapped in try/catch.
* On failure it logs a warning and still returns `{ message: 'Cleared Cache' }`. That is true, because the cache was cleared.

## Blast radius
* The fetch throws before `segregateSAASData` runs, so the in-memory `saasSettings`/`saasFeatures` keep their last good values. This is the same fallback idea as SAN-407.
* The `saas-platform-settings` cache key is written but never read in `src`.
* Cron jobs are not re-registered on failure, so the existing ones keep running.
* The 200 response shape is unchanged and `contracts/openapi.json` is unchanged.

## Verification
* `npm run gates` (sc-saas-backend): exit 0 (lint, test 1329 ≥ floor 1319, openapi-floors, build).

## Open
* Replace the `console.log('errrr', error)` in `sanchiconnect.service.ts` with a sanitised warning.
* Both `public/global` endpoints are unauthenticated. This predates the change; noted per the unauthenticated-endpoint guardrail.
