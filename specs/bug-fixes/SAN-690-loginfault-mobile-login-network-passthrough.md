---
id: SAN-690
title: "loginFault( ... 0 Unknown Error, mobile login ) — network-level passthrough"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-690
sentry:
  - SC-SAAS-FRONTEND-9A
repos: [frontend]
commit: "none — infra/network-scoped, not a code defect"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-690 — network-level failure passthrough on mobile login

## Root cause
`auth.service.ts:47-67` (`login()`), guarded fallback chain, "0 Unknown Error" on
`public/auth/mobile/login` — same network-level-failure passthrough class as SC-SAAS-FRONTEND-3M/49
(SAN-604/605), just a different endpoint (mobile login).

## Fix
No fix needed/possible in frontend — consistent with prior conclusion that this failure mode is
infra/network-scoped, not a code defect.

## Related
SC-SAAS-FRONTEND-3M (SAN-674), SC-SAAS-FRONTEND-49 (SAN-675).

## Verification
Cross-referenced against the SAN-604/605 conclusion for the same failure class.
