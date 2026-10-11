---
id: SAN-1009
title: Send the "Application withdrawn" email to the user who withdrew (1:1)
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1009
repos: [backend]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1009 — the user who withdraws also gets the "Application withdrawn" email

## Request

QA: when a user withdraws their pending 1:1 application, only the CC list and admins receive "Application
withdrawn". The user receives nothing.

## Finding

`withdrawEventAttendeeApplication()` (`sc-saas-backend/src/modules/events/events.service.ts`) built its
recipients from `event.ccEmails` (which includes the creator admin, SAN-1007) plus the desk-CC admins
(SAN-998), and sent no other email.

## Decision (user)

"Same alert, add the user": no new template. The user is added to the existing
`event-one-to-one-application-withdrawn` email and sees its wording ("Hi, <name> has withdrawn their
application for a One-on-One slot in: <event> … The slot is open again for new applications.").

## Fix

The recipient list is now `[user, ...CC list, ...desk-CC admins]` (de-duplicated). The user is the **To**,
and everyone else is CC'd. Because the user always exists, the email now always sends. The speaker is still
not a recipient. No template, sender method or data change.

## Verified

- `npx tsc --noEmit` clean.
- Not exercised against a live send.

## Open questions

None.
