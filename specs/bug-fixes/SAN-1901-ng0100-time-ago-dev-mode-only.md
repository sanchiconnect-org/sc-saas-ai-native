---
id: SAN-1901
title: "NG0100 time-ago ExpressionChanged in feed + chat — dev-mode only"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1901
sentry: [SC-SAAS-FRONTEND-BV, SC-SAAS-FRONTEND-B2]
repos: [frontend]
commit: none — no code defect, see Investigation
created: 2026-10-14
updated: 2026-10-14
---

## Investigation
BV (`CommunityFeedSinglePostComponent`, `daysPassed(post.createdAt)`) and B2 (chat `SentMessageComponent`) both show a relative-time label crossing a second/minute boundary between change detection and the dev-mode `checkNoChanges` pass. All events are `environment: local` (thub.sanchidev.in dev build per SAN-158, and localhost:4200), from one internal IP. Production mode never runs `checkNoChanges`, so there is no user impact.

## Fix
None. Rewriting the time-ago rendering would touch chat + feed for no user-facing gain. Goes away with SAN-158.
