---
id: SAN-939
title: meetings/notes 403 Forbidden unhandled in meeting.component
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-939
sentry:
  - SC-SAAS-FRONTEND-74
repos: [frontend]
commit: sc-saas-frontend@fff67813 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-939 — meeting.component.ts unhandled 403 on notes fetch/save

## Root cause
`fetchMeetingNotes()`/`saveMeetingNotes()` in `meeting.component.ts` both called `.subscribe()` with
no error callback. A 403 (no permission on this meeting's notes; 1 user, 2 events) had nowhere to go
but Sentry as an unhandled HTTP failure.

## Fix
Added no-op `error` callbacks to both subscribes, matching the existing SAN-504/471 pattern used
elsewhere for the same class of defect. `fetchMeetingNotes()` now leaves notes empty on failure
instead of crashing.

## Blast radius
None — purely additive error handling, no change to success-path behavior.

## Verification
Committed separately from the unrelated SAN-937 fix that also touches this file (see that ticket's
doc) — split into two commits so each is independently reviewable. No automated test added — step 6
(tests-first) is blocked workspace-wide (no `guardian` skill); substituted a direct code read.
