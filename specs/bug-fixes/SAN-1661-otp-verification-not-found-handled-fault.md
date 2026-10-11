# SAN-1661 — "No such verification request found" re-logged to Sentry

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1661 (Sentry SC-SAAS-FRONTEND-40, 19 users / 19 events)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** NOISE (expected-condition logging)

## Problem
`verifyOTPFault( No such verification request found in the system. Please try again. )` on program apply. The OTP-verify `catchError` blocks toast the message
and also `console.warn` it, and `captureConsoleIntegration` forwards that warning to Sentry as a second report of an expected user error.

## Root cause
The backend returns `VERIFICATION_NOT_FOUND` (`sc-saas-backend/src/core/constants/api-error-message.ts:320`) when the OTP request is gone or was replaced. The sibling
messages (invalid OTP, expired OTP, request expired or completed) are already in the `HANDLED_HTTP_FAULT` filter in `src/main.ts` (SAN-599/601/608); this one is not.

## Fix
Add the exact message to `HANDLED_HTTP_FAULT`. The filter stays narrow (warning level only, no exception, message must end in `Label( <message> )`), so a real
exception mentioning the same text still reports. The user is still toasted.

## Contract impact
None. The backend message is unchanged; this only filters the client-side Sentry report. No flag, tenancy or auth change.

## Verification
- `tsc --noEmit -p tsconfig.app.json` exits 0.
- A one-off node check extracted the real `HANDLED_HTTP_FAULT` regex from `main.ts` and ran 9 cases: it matches the new message under `verifyOTPFault(...)` and
  `loginFault(...)`, still matches the existing sibling messages, and does not match an unrelated message, a message with trailing text, or the bare message with no
  `Label( ... )` wrapper (9/9 as expected).
- No automated test added (none exists for main.ts).

## Commit
sc-saas-frontend `5a470e9bc` on `ai_native_setup_aman`. Not deployed.
