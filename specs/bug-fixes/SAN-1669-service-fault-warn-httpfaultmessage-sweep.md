# SAN-1669 — 94 service fault warnings logged `fault.error.message` with no fallback

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1669 (Sentry SC-SAAS-FRONTEND-43, 98, 7E, 76, GG, 80, 82 and the same class)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (diagnostic message, and a throw on an empty body)

## Problem
`updateFounderInfo( undefined )`, `savefounderInfo( undefined )`, `foundersFault( undefined )`, `searchInvestor Fault( undefined )`, `searchMentor Fault( undefined )`,
`getIndividualInvestorCompleteness( undefined )`, `getMentorDashboard( undefined )`. Same defect SAN-673/688/692 fixed only in `sign-up.service`, and SAN-1662 in `auth.service`.

## Root cause
94 `console.warn` sites in 22 files under `src/app/core/service/` logged `` `Label( ${fault.error.message} )` `` or `${fault?.error?.message}`. A failure with no JSON body (504, network
drop, empty 502) has no `error.message`, so the warn is `( undefined )`, which `captureConsoleIntegration` forwards to Sentry. The unguarded `fault.error.message` form (about 30 sites) also throws
a TypeError inside the `catchError` callback when `fault.error` is null, replacing the original failure with a crash.

## Fix
Every such warn line now uses `httpFaultMessage(fault, `HTTP ${fault?.status}`)` from `src/app/shared/utils/http-fault.util.ts`, a pure helper that never throws and returns the validation or backend
message, else the fallback. Done by script (one-off node, not committed): live `console.warn` lines only, commented-out lines untouched, import added in 20 files, line endings preserved.
Files: advisoryBoard, challenge, commitments, corporate, founders, individual-profile, investor-compare, investors, job-details, jobs, mentors, mentorship, metrics, partners, pitch-deck-record, pitch-deck,
profile, program-office, search, service-provider, startup-compare, startup (all `.service.ts`).

## What did not change
Toasts, rethrows and call sites are unchanged. A normal backend message (for example `Invalid access token`) logs the same text, so the `HANDLED_HTTP_FAULT` filter in `main.ts` still matches it. An empty-body
failure now logs `Label( HTTP 504 )` instead of `Label( undefined )`.

## Contract impact
None. Logging only; no API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` and `ngc` exit 0; the diff (165 added / 111 removed lines) was reviewed and holds only these warn-line and import changes. No automated test added (none exists for these services'
`catchError` paths).

## Commit
sc-saas-frontend `55a7a6697` on `ai_native_setup_aman`. Not deployed.
