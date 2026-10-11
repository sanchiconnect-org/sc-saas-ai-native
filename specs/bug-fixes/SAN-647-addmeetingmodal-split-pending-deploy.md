---
id: SAN-647
title: "TypeError: Cannot read properties of null (reading 'split') in add-meeting-modal — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-647
sentry:
  - SC-SAAS-FRONTEND-47
repos: [frontend]
commit: "sc-saas-frontend@2fd51acd (SAN-485), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-647 — null duration-time crash, already fixed

## Root cause
`AddMeetingModalComponent.handleDurationChange()` called `fromTime.split(':')` when `timeFrom` was
null (duration picked before a start time).

## Fix
Already fixed in commit `2fd51acd` (SAN-485, 2026-08-24) — added `if (!fromTime) { return; }` guard at
`add-meeting-modal.component.ts:565-568`. Fix predates this issue's window by over a week — consistent
with prod deploy lag, not a fresh regression.

## Verification
Confirmed the guard precedes the `.split()` call.
