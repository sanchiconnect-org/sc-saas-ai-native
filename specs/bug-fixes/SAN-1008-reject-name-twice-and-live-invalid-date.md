---
id: SAN-1008
title: 1:1 reject email shows "X from X"; event-live email shows "01 Jan 2026, Invalid date - Invalid date"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1008
repos: [backend]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1008 — duplicate speaker name in the reject email; broken schedule in the event-live email

## Request (QA screenshots)

1. The rejection email that reaches the user, the CC list and the admin read "**ritu raj** from **ritu raj** has
   rejected the meeting request". The same name appeared in both places.
2. The "Event is live" email (CC list and admin) showed Schedule "01 Jan 2026, Invalid date - Invalid date".

## Root cause

1. `performOrdinaryReject()` (`events.service.ts`) set **both** `sender_name` and `organization_name` to
   `getOrganizationName(eventOwner)`. For a mentor or non-registered speaker, that "organization" is the
   person's own name, and the `meeting-request-rejected` template is
   `{{ sender_name }}{{{ organization_name }}} has rejected…`. This is pre-existing (SAN-769). The meeting
   emails already avoid it with `user.name` + `getOrganizationNameWithMentorNull()`.
2. `sendEventOneToOneLiveEmail()` (`admin-actions.service.ts`, added in SAN-994) normalised each day with
   `formatDateToYYYYMMDD()`, which returns `'YYYY:MM:DD'` (**colons**, meant for ICS arrays). `moment('2026:09:25')`
   reads only the year (→ 01 Jan) and `moment('2026:09:25 15:45')` is invalid. The admin panel's
   `events.dates` (`{date: 'YYYY-MM-DD', time_from: 'HH:mm', time_to: 'HH:mm'}`) was fine.

## Fix

1. Rejection email: `sender_name = eventOwner.name`, and `organization_name = " from <b>org</b>"` only when
   `getOrganizationNameWithMentorNull(eventOwner)` is set and differs from the name. The Speaker row in the
   application-received email and the event-live email now show the speaker's own name too
   (`eventOwner.name` / `speaker.name`), not their organization's.
2. Event-live schedule: `moment(day.date).format('YYYY-MM-DD')` instead of `formatDateToYYYYMMDD()`.

## Verified

- `npx tsc --noEmit` clean.
- Reproduced and verified with moment directly: the old code gives `01 Jan 2026, Invalid date`, the fix gives
  `25 Sep 2026, 03:45 pm - 06:00 pm | 26 Sep 2026, 10:00 am - 12:30 pm`.
- Not exercised against a live send.

## Open questions

None.
