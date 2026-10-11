---
id: SAN-685
title: "verifyOTPFault( rate limit reached ) — expected rate-limiting business rule"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-685
sentry:
  - SC-SAAS-FRONTEND-84
repos: [frontend]
commit: "none — expected rate-limiting business rule"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-685 — expected OTP rate-limit rejection

## Root cause
`sign-up.service.ts:56` (`verifyOTP()`), guarded handler surfacing the backend's OTP rate-limit
business rule as intended (backend rate-limits OTP endpoints to 3 requests/60s per `@RateLimit` in
`sc-saas-backend/src/modules/auth/auth.controller.ts`).

## Fix
No fix needed. If legitimate users are hitting this often, consider raising the backend rate-limit
threshold (`sc-saas-backend` — out of scope for this repo).

## Verification
Confirmed the backend rate-limit configuration and that the frontend handler is already guarded.
