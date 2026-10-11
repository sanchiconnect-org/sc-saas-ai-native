---
id: SAN-684
title: "loginFault( Internal Server Error ) — backend 500 passthrough, correctly guarded"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-684
sentry:
  - SC-SAAS-FRONTEND-AW
repos: [frontend]
commit: "none — correctly guarded, backend-origin"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-684 — genuine backend 500, correctly handled

## Root cause
`auth.service.ts:62-65` (`login()`), guarded fallback chain
(`fault?.error?.message || fault?.message || fault?.status`) — "Internal Server Error" is a genuine
backend 500 passed through correctly.

## Fix
No frontend fix — investigate `sc-saas-backend` login endpoint for the 500 cause if it recurs at
volume.

## Verification
Confirmed the error handler already guards against null/undefined fault shapes.
