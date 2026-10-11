---
id: SAN-659
title: "TypeError: Cannot read properties of undefined (reading 'toString') in SignUpService.verifyOTP — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-659
sentry:
  - SC-SAAS-FRONTEND-AR
repos: [frontend]
commit: "sc-saas-frontend@943385c9 (SAN-528), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-659 — undefined OTP code crash, already fixed

## Root cause
`SignUpService.verifyOTP()` called `signupCredentials.code.toString()` with `code` undefined.

## Fix
Already fixed in commit `943385c9` (SAN-528, 2026-08-26) — added
`if (!signupCredentials.code) { return throwError(...) }` guard at `sign-up.service.ts:40-42`, before
the `.toString()` call. Fix commit is same-day as this issue's last-seen — likely pending deploy given
prod lag.

## Verification
Confirmed the guard precedes the `.toString()` call.
