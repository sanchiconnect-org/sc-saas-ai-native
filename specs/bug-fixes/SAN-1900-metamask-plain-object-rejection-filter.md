---
id: SAN-1900
title: "MetaMask -32603 plain-object rejection bypasses beforeSend filter"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1900
sentry: [SC-SAAS-FRONTEND-90]
repos: [frontend]
commit: sc-saas-frontend@609e3df48 (branch ai_native_setup_vishali, pushed)
created: 2026-10-14
updated: 2026-10-14
---

## Root cause
The SAN-376 filter in `src/main.ts` tests the exception *value* for `-32603` + `JSON-RPC`. For a plain-object rejection, the SDK's value is the synthetic `Object captured as promise rejection with keys: code, message`, so the filter never matched. The latest event's release `218edca78` already includes SAN-376/SAN-1668, so this is a live gap, not deploy lag.

## Fix
`beforeSend` also drops the event when `hint.originalException` is a non-Error object with `code === -32603` and a message containing `JSON-RPC`.

## Blast radius
Sentry ingestion only. The app has no wallet/`window.ethereum` code, so no first-party error can match. The SAN-1144 diagnostic tagging for other plain-object rejections is unchanged.

## Verification
`tsc` + eslint clean. No automated test added. Confirmed via a new prod release when events stop.

## Related
SAN-376, SAN-1668, SAN-1144
