---
id: SAN-925
title: FeedbackComponent crashes reading 'meetingTitle' off undefined meetingDetails
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-925
sentry:
  - SC-SAAS-FRONTEND-FV
repos: [frontend]
commit: sc-saas-frontend@4893b34e (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-925 — feedback template reads meetingDetails before it resolves

## Root cause
`feedback.component.html:19` read `meetingDetails.meetingTitle` in the template before the
(asynchronously loaded) `meetingDetails` had resolved, crashing with "Cannot read properties of
undefined (reading 'meetingTitle')" (1 user, 16 events).

## Fix
Added `*ngIf="meetingDetails"` on the containing block so the template simply doesn't render until
the data is available.

## Blast radius
None — the block was unusable without `meetingDetails` anyway (every field inside reads from it);
this only delays render instead of crashing.

## Verification
Re-read the template after editing. No automated test added — step 6 (tests-first) is blocked
workspace-wide (no `guardian` skill); substituted a direct code read.
