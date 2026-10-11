---
id: SAN-687
title: "startupinfoFault( ... 502 Bad Gateway, localhost ) — local dev-proxy down"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-687
sentry:
  - SC-SAAS-FRONTEND-A1
repos: [frontend]
commit: "none — local dev-environment issue"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-687 — local dev-proxy down, not a code defect

## Root cause
`startup.service.ts:96-113`, local dev environment, 502 Bad Gateway — same local
dev-server-proxy-down pattern as SC-SAAS-FRONTEND-9Z.

## Fix
No frontend fix — local dev-environment issue.

## Related
SC-SAAS-FRONTEND-9Z (SAN-681, same pattern).

## Verification
Confirmed `environment: local` tag and 502 status match a dev-proxy-down signature.
