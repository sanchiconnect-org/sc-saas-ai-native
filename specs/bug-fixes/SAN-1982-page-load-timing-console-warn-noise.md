---
id: SAN-1982
title: "Page-load timing JSON reported to Sentry as an issue — browser-injected console.warn (SC-SAAS-FRONTEND-HK)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1982
sentry: [SC-SAAS-FRONTEND-HK]
repos: [frontend]
commit: frontend@8584477bf (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1982: page-load timing JSON reaching Sentry

## Investigation
* **Sentry:** a message event (not an exception) `{"dnsLookup":0,"tcpConnect":0,"requestTime":39,...,"totalLoadTime":756,"readyState":"complete","success":true}`.
  * 5 events, 1 user, 2026-10-16, connect.trise.tripura.gov.in `/startups/dashboard`.
  * Tags `logger: console`, `level: warning`, browser **HiBrowser 3.00.09** on an Infinix X6870 (Android 16), release `218edca78`.
  * `extra.arguments` is the single JSON string.
* **How it reaches Sentry:** `logger: console` + `warning` is the `captureConsoleIntegration({ levels: ['warn'] })` hook in `src/main.ts`, so something called `console.warn` with that JSON string.
* **The caller is not in this app:**
  * `grep -rl "dnsLookup\|totalLoadTime"` over the whole of `sc-saas-frontend` (src, scripts, index.html, assets) → no match;
  * the same grep over `node_modules --include=*.js` → no match;
  * so neither the app nor any dependency produces this payload.
* It was seen only on HiBrowser, the bundled browser on Transsion (Infinix/Tecno/itel) phones, which injects its own page-performance script. It is a successful timing, not a fault.
* This is the same class as the other foreign-script noise `beforeSend` already drops (SAN-1668 extensions, SAN-1143 beacon.min.js).

## Fix
A narrow drop in `beforeSend` in `src/main.ts`, next to the Popper filter. It needs all of:
* no exception;
* `level === 'warning'`;
* the message matches `^\{"dnsLookup":\d+,"tcpConnect":\d+,.*"totalLoadTime":\d+.*\}$`.

## Blast radius / existing-flow impact
* No app functionality is lost: the app never logged this, and the browser's own console output is untouched (`beforeSend` only decides what is sent to Sentry).
* Every other `console.warn` is still forwarded, including the service-level `Label( message )` warnings and any JSON warning of another shape.
* Exceptions are never matched.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → exit 0.
* The regex checked with node:
  * HK message matches: `true`;
  * ordinary warn (`SomeService( Http failure )`) matches: `false`;
  * other JSON (`{"status":500,"message":"x"}`) matches: `false`.
* No automated test was added: `beforeSend` is inline in `main.ts` and has no spec harness (none of the existing filters are unit-tested).
* Lint: none configured.

## Related
SAN-1668, SAN-1143, SAN-1573 (other `beforeSend` noise filters). Same sweep: SAN-1986, SAN-1991, SAN-1993, SAN-1994.
