---
id: SAN-2118
title: "401 on meetings/pending-acceptance and connections still reaching Sentry from prod — trise serving a September bundle"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2118
sentry: [SC-SAAS-FRONTEND-2J]
repos: [frontend]
related: [SAN-1673, SAN-1925, SAN-1971, SAN-2030, SAN-1140]
commit: none — deploy lag / stale PWA
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2118: 2J is still a stale build

## Investigation
* 2J: 126 events / 51 users in 14 days. The newest event (`meetings/pending-acceptance` 401 on connect.trise.tripura.gov.in) is on release `dab63831` (2026-09-03).
* The SAN-1673 `beforeSend` 401 filter (`bd95b012c`, 10-06) is in `218edca78` (2026-10-11, the tip of origin/main) and **not** in `dab63831`.
* There were zero 2J 401 events in 14 days from releases that contain the filter (`218edca78`, `3fe291506`).

## Fix
None in code; the interceptor is untouched. Redeploy trise from current main or force a service-worker refresh (SAN-1140).
