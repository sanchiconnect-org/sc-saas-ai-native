---
id: SAN-677
title: "loginFault( One time password you entered is expired ) — expected OTP-expiry"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-677
sentry:
  - SC-SAAS-FRONTEND-4A
repos: [frontend]
commit: "none — expected business rule"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-677 — expected OTP-expiry business rule

## Root cause
`auth.service.ts:98-99` (`verifyOtp()`) — expected OTP-expiry business logic, guarded handler.

## Fix
No fix needed.

## Verification
Confirmed the message originates from a guarded, intentional business-rule response.
