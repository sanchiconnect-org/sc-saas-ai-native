---
id: SAN-680
title: "loginFault( Your profile has been rejected ) — expected business state"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-680
sentry:
  - SC-SAAS-FRONTEND-2K
repos: [frontend]
commit: "none — expected business state"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-680 — expected profile-rejection business state

## Root cause
`auth.service.ts:47-67` (`login()`), guarded handler surfacing a genuine backend business state
("profile has been rejected").

## Fix
No fix needed — working as intended.

## Verification
Confirmed the message originates from a guarded, intentional backend business-rule response.
