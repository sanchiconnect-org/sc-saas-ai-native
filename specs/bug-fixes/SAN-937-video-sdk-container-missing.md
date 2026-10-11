---
id: SAN-937
title: "'No Container found with id video-sdk-container' joining a meeting"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-937
sentry:
  - SC-SAAS-FRONTEND-FJ
repos: [frontend]
commit: sc-saas-frontend@d7adcdd9 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-937 — meeting.component.ts VideoSDKMeeting.init() DOM race

## Root cause
`VideoSDKMeeting.init()` throws synchronously ("No Container found with id video-sdk-container") when
the view hasn't rendered the `#video-sdk-container` element yet — a routing/`*ngIf` race (2 users,
1 event).

## Fix
Added a DOM-existence check (`document.getElementById('video-sdk-container')`) before calling
`meeting.init(config)`; on failure, show a "please try again" toast and return instead of letting the
third-party SDK throw.

## Blast radius
None on the success path (container present in the normal flow). Failure path changes from an
uncaught crash to a controlled toast + early return.

## Verification
Re-read the file after editing to confirm placement immediately before `new VideoSDKMeeting()` /
`meeting.init(config)`. No automated test added — step 6 (tests-first) is blocked workspace-wide (no
`guardian` skill); substituted a direct code read. No live meeting-join test performed in this
environment — genuinely outstanding.
