---
id: SAN-1011
title: "Empty verify/mobile call on register + unhandled 401 on applied-programs list"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1011
sentry: [SC-SAAS-FRONTEND-2J]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1011

## Problem
Sentry group 2J (980+ users) carries two variants: `GET public/auth/verify/mobile/` with no number → 404 on /auth/register, and `programs-management/applied/list: 401` unhandled.

## Root cause (CODE_ERROR)
1. `account-information.component.ts`: mobileNumber is optional when mobile-OTP is off, so a cleared field is "valid" and `verifyMobileNumber()` calls the API with an empty segment (backend route is `verify/mobile/:mobileNumber`).
2. Applied-programs subscribers had no error callback; the interceptor already handles 401 (SAN-471) but the error still surfaced.

## Fix
- account-information: skip check when value is blank; clear stale duplicate error and re-emit form validity.
- Error callbacks (reset loader) in applied-programs, programs, program-code-details, program-public-apply, call-for-applications-applied, vs-applied-programs, vs-programs, vs-program-code-details.

## Existing-flow check
Other verifyMobile callers (register-modal, claim-listing-modal) have a required mobile field — unaffected. Success paths untouched; on error data stays unset as before.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
