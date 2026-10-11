---
id: SAN-926
title: FINANCIALS save error (Internal Server Error) on ecosystem.firstwingsconnect.com
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-926
sentry:
  - SC-SAAS-FRONTEND-D5
repos: [frontend]
commit: sc-saas-frontend@e11ea2c7 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-926 — financials-details.component.ts unhandled save error

## Root cause
`financials-details.component.ts:420`'s `saveFinancials().subscribe()` had no error callback.
`saveFinancials()`'s own `catchError` already shows a toast and `console.warn`s before re-throwing
(8 users, 36 events) — without a callback here, `subscribe()` re-threw the already-handled fault as a
second, unhandled exception on top of the toast.

## Fix
Added an error callback that resets `this.loader`/`this.savingFinancials` (redundant with the
existing `finalize()` on the same pipe, but harmless) and otherwise does nothing — user feedback is
already handled upstream in the service.

## Blast radius
None — purely additive error handling, no change to success-path behavior or user-facing messaging.

## Verification
Confirmed via grep that `this.loader`/`this.savingFinancials` are used identically elsewhere in the
same file (e.g. the existing `finalize()` block). No automated test added — step 6 (tests-first) is
blocked workspace-wide (no `guardian` skill); substituted a direct code read.
