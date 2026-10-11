---
id: SAN-941
title: "/api/v2/events/ endpoint: 0 Unknown Error (network-level) unhandled"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-941
sentry:
  - SC-SAAS-FRONTEND-F6
repos: [frontend]
commit: sc-saas-frontend@fa5b5e31 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-941 — events-calender.component.ts unhandled network-level failure

## Root cause
`events-calender.component.ts`'s `getMeetings()` called
`this.globalService.getAllPlatformEvents().subscribe(response => {...})` — a plain arrow-function
subscribe with no error callback. A network-level failure (status 0; 1 user, 3 events) crashed the
subscribe instead of leaving the calendar view empty.

## Fix
Converted to `.subscribe({ next: response => {...}, error: () => {} })`.

## Blast radius
None on the success path. On failure, the calendar view now stays empty instead of throwing an
unhandled exception.

## Verification
Committed separately from the unrelated SAN-938 fix that also touches this same function (see that
ticket's doc) — split into two commits so each is independently reviewable. No automated test added —
step 6 (tests-first) is blocked workspace-wide (no `guardian` skill); substituted a direct code read.
