# SAN-1662 — `verifyWhatsappOTP` logs `verifyOTPFault( undefined )` on empty-body failures

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1662 (same class as SC-SAAS-FRONTEND-9Y / B4 / BC)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (diagnostic message)

## Problem
`AuthService.verifyWhatsappOTP()` (`src/app/core/service/auth.service.ts`) logged `console.warn(`verifyOTPFault( ${fault.error?.message} )`)`. A failure with no JSON
body (a 504 or a network drop) has no `error.message`, so the message was `verifyOTPFault( undefined )`, which `captureConsoleIntegration` forwards to Sentry as an
uninformative event.

## Context
SAN-673 / SAN-688 / SAN-692 (commit `145e86991`, 2026-09-07) fixed the same defect in `sign-up.service.ts` for SC-SAAS-FRONTEND-9Y / B4 / BC. The program-apply OTP flow, which
is the real source of 9Y, calls `SignUpService.verifyOTP` (program-public-apply-modal, program-check-status-modal), already hardened, so 9Y itself was covered by SAN-673. This
method was missed because it belongs to a different service.

## Fix
Use the existing `httpFaultMessage(fault, `HTTP ${fault?.status}`)` helper (already used for `sendOTPFault` in the same file) so the warning always carries a validation message,
the backend message, or the HTTP status. The toast and the rethrow are unchanged.

## Contract impact
None. Frontend logging only; no API, flag, tenancy or auth change.

## Verification
- `tsc --noEmit -p tsconfig.app.json` and `ngc -p tsconfig.app.json --noEmit` both exit 0.
- No automated test added (none exists for this service's `catchError` path). Not exercised against a real 504.

## Commit
sc-saas-frontend `14bbd4e51` on `ai_native_setup_aman`. Not deployed.
Note: the commit message body lost one inline expression to shell expansion and reads `verifyOTPFault( \ )` where it meant `verifyOTPFault( ${fault.error?.message} )`; the pushed
history was not rewritten for that. The code change is correct.
