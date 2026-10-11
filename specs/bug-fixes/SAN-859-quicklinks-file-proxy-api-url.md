---
id: SAN-859
title: "Quicklinks file-proxy URL uses tenant's configured API URL, not request Host"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-859
repos: [backend]
commit: sc-saas-backend@9d765642
created: 2026-09-20
updated: 2026-09-20
---

# SAN-859 — quicklinks file-proxy origin sourced from the tenant's own API URL

## Request

For the `public_portal_quicklinks_file_proxy_enabled` flag (already fully built and wired end-to-end: cockpit
`tenant_users` column → backend `Feature` enum → `QuicklinksService.getQuicklinks()`), use the tenant's own
configured API URL as the file-proxy URL's origin, instead of deriving it from the incoming request's Host
header.

## Before

`PublicPortalController.getQuicklinks()` computed `requestOrigin = https://${req.hostname}` per request, passed
it into `QuicklinksService.getQuicklinks(category, requestOrigin)`, which used it (only when the flag is on) via
`buildQuicklinksFileProxyUrl(key, requestOrigin)`.

## After

The origin is now `saasSettings[SaaSSettingKey.API_URL]` — a new `SaaSSettingKey.API_URL = 'apiUrl'` enum entry
exposing the tenant's `tenant_users.api_url` column (already present in the tenant-settings bootstrap payload
this backend loads at startup, via the generic string-valued `settings` map — see
`global.service.ts`/`segregateSAASData()`). This is a single, cockpit-verified value instead of trusting
whatever hostname a given request happened to arrive on.

## Changes

- `src/core/constants/enum.ts` — new `SaaSSettingKey.API_URL = 'apiUrl'`.
- `src/modules/public-portal/utils/quicklinks-file-proxy-url.util.ts` — `buildQuicklinksFileProxyUrl(key, apiUrl)`
  strips a trailing slash from `apiUrl` before concatenating (`tenant_users.api_url` is stored WITH a trailing
  slash upstream — confirmed via `sc-saas-admin/config/config.php`'s own `api_url . "api/"` concatenation, which
  relies on that trailing slash already being there).
- `src/modules/public-portal/services/quicklinks.service.ts` — reads the setting directly; `getQuicklinks()` no
  longer takes a `requestOrigin` parameter.
- `src/modules/public-portal/controllers/public-portal.controller.ts` — `getQuicklinks()` no longer needs
  `@Req()`; removed the now-unused `Req`/`Request` imports (nothing else in this controller used them).

`quicklinks-file-proxy.controller.ts` (the endpoint that actually *serves* the proxied file) is unaffected — it
builds its own real-CDN-fetch URL via `AppConfigService.getAppDomain`, unrelated to this change.

## Verification

`npx tsc --noEmit -p tsconfig.json` clean. `npx eslint` on all four touched files showed only pre-existing
tooling-quirk warnings (confirmed by linting an untouched sibling file in isolation — same spurious "unused
import" warnings appear there too, since single-file eslint invocation here doesn't resolve decorator usage
across the whole class). No test framework covers this module's request-shape end-to-end; no regression test
proposed for a plain value-source swap.

## Rollout

Committed and pushed to `ai_native_setup`: `9d765642`.

## Open questions

None blocking.
