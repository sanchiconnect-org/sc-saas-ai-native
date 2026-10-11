---
id: SAN-676
title: "verifyOTPFault( No such verification request found ) — expected OTP-expiry business rule"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-676
sentry:
  - SC-SAAS-FRONTEND-40
repos: [frontend]
commit: "none — expected business rule"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-676 — expected OTP session-expiry/supersession

## Root cause
`sign-up.service.ts:56` — real backend business-rule response (OTP session expired/consumed/
superseded by a resend). Guarded handler, working as intended.

## Fix
No fix needed. Optional UX polish: auto-trigger "resend OTP" when this specific message is seen.

## Verification
Confirmed the handler is already guarded and the message matches an intentional backend business rule.
