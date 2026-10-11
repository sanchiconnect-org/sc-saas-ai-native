# SAN-567 / SAN-569 / SAN-615 — console.warn on transient or expected faults floods Sentry

- **Linear:** SAN-567 (SC-SAAS-FRONTEND-49), SAN-569 (SC-SAAS-FRONTEND-3M), SAN-615 (SC-SAAS-FRONTEND-C6)
- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra (taken over from vishali kashyap) · **Classification:** NOISE / expected-condition logging

## Problem
`captureConsoleIntegration` forwards every `console.warn` to Sentry. Three service `catchError` blocks warn on every fault,
including faults that are not application bugs:
- SAN-567: `startupDashboard( ... profile_completeness: 0 Unknown Error )` — network drop on thub.sanchidev.in.
- SAN-569: `startupinfoFault( ... startup-information: 0 Unknown Error )` — same cause.
- SAN-615: `update PitchFile Info( Uploaded file content does not match its extension )` — an expected 400 the backend
  returns (`pitch-deck.controller.ts`) and the user is already toasted.

## Root cause
No distinction between a transient infrastructure fault (status 0 / 5xx), which is not actionable from the client, and a real client fault.

## Fix
Skip the `console.warn` when `!fault?.status || fault.status >= 500` in `startup-dashboard.service.ts` (`getStartUpCompleteness`,
`getStartUpDashboard`) and `startup.service.ts` (`getStartUpInfo`). In `pitch-deck.service.ts` and `pitch-deck-record.service.ts`
(`uploadPitchFile`) also skip it for a 400 whose message matches `does not match its extension`. Toasts and the rethrow are unchanged;
other 4xx faults still warn.

## Contract impact
None. Frontend-only logging change. No API, flag, tenancy or auth change.

## Verification
- `tsc --noEmit -p tsconfig.app.json` and `ngc -p tsconfig.app.json --noEmit` clean.
- No automated test added (none exists for these services' catchError paths).
- Not checked in a browser.

## Commits
sc-saas-frontend `3cf4994d8` (SAN-567), `cac790292` (SAN-569), `8678ca9f7` (SAN-615), on `ai_native_setup_aman`. Not deployed.
