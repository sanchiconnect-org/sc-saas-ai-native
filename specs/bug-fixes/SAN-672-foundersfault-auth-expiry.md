---
id: SAN-672
title: "foundersFault( Invalid access token ) — expected auth-expiry rejection"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-672
sentry:
  - SC-SAAS-FRONTEND-96
repos: [frontend]
commit: "none — expected auth-expiry rejection"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-672 — expected auth-expiry rejection

## Root cause
`founders.service.ts:32-35` (`getFounders()`) — already guarded. "Invalid access token" on
`/auth/login` culprit means an expired/invalid JWT reached this call — standard auth-expiry rejection,
handled by the existing 401/auth-interceptor flow.

## Fix
No fix needed.

## Verification
Confirmed the handler is already guarded and the message matches the standard auth-expiry flow.
