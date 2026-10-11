---
id: SAN-1005
title: "Meeting Cancelled" email greets the recipient by email address instead of name
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1005
repos: [backend]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1005 — "Hi <email>," in the Meeting Cancelled email

## Request

QA: cancelling a 1:1 event sends the "Meeting Cancelled" email to the speaker and the CC list, but the
greeting shows the email address ("Hi aman@example.com,") instead of the person's name.

## Root cause

`MeetingsService.sendCancelledMeetingEmail()` (`src/modules/meetings/meetings.service.ts`) passed
`receiver_name: user.email` / `receiver_name: otherUser.email` into the `meeting-cancelled` template, whose
greeting is `Hi {{ receiver_name }},`. This has been there since the method was added (`dcc63090`, Dec 2024,
"Add cancel event meeting email"). It isn't a regression from SAN-992–998.

The method is the only place this email is built. It has exactly three callers, all in
`events.service.ts`: reschedule's old-slot cancellation (~L440), cancel event (~L1760) and admin reversal of
an approved booking (~L1828). All three had the wrong greeting. The meetings module does not call it.
`users.name` is NOT NULL (`user.entity.ts`), so every recipient has a name to show, for all account types.

Same bug class elsewhere (not fixed here, out of scope): `requestVideoPitch()` in
`admin-actions.service.ts` (~L3503) passes `receiver_name: startupUser.email` to the video-pitch-requested
email.

## Fix

`receiver_name: user.name` / `otherUser.name`, the same as `sendScheduledMeetingEmail()`. The subject
(`meeting_custom_title` ← `meeting_title`), `sender_name`, recipients and CC list are unchanged.

## Verified

- `npx tsc --noEmit` clean. The diff is 2 lines, plus a comment on each.
- Not exercised against a live send.

## Open questions

None.
