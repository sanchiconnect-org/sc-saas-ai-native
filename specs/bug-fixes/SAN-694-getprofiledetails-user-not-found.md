---
id: SAN-694
title: "getProfileDetails Fault( User not found ) — already-fixed handler, genuine backend response worth watching"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-694
sentry:
  - SC-SAAS-FRONTEND-44
repos: [frontend]
commit: "sc-saas-frontend@9d186afc (SAN-582)"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-694 — genuine backend response, already-guarded handler

## Root cause
`profile.service.ts:87-107` (`getProfileDetails()`) — already fixed per SAN-582
(`sc-saas-frontend@9d186afc`), now using `httpFaultMessage(fault)` (guarded). "User not found" here is
a genuine backend response, not a null-crash. A logged-in user's own profile self-lookup failing is
unusual (possible deleted/disabled account with a still-valid session token), but the code already
handles the 404 case gracefully (`fault.status === 404` → `authService.logout()` + "Session expired"
toast).

## Fix
No fix needed; if this recurs at volume, would indicate an account-deletion/session-invalidation
ordering issue worth a backend look.

## Verification
Confirmed the 404 handler already logs the user out with an appropriate toast.
