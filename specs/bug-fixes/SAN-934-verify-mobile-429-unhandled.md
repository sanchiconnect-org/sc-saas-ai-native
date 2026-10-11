---
id: SAN-934
title: verify/mobile 429 surfaces as unhandled HTTP failure
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-934
sentry:
  - SC-SAAS-FRONTEND-72
repos: [frontend]
commit: sc-saas-frontend@f675d4c3 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-934 — account-information.component.ts unhandled verifyMobile 429

## Root cause
`account-information.component.ts:264`'s `verifyMobileNumber()` pipe already stops the loader on
error via its own `tap` error handler and a `finalize()`, but the outer `.subscribe()` had no error
callback — a 429 (2 users, 4 events) re-surfaced as an unhandled HTTP failure after those handlers
already ran.

## Fix
Added a no-op `error` callback to the outer `.subscribe()` — the toast/loader-stop is already handled
upstream, this just stops the duplicate unhandled-error report.

## Blast radius
None — purely additive error handling, no change to success-path behavior.

## Verification
Re-read the surrounding `verifyMobileNumber()` method to confirm the existing `tap` error handler and
`finalize()` already cover user feedback. No automated test added — step 6 (tests-first) is blocked
workspace-wide (no `guardian` skill); substituted a direct code read.
