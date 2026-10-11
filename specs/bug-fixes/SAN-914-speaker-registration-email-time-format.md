---
id: SAN-914
title: event-speaker-registration email shows raw HH:MM:SS instead of 12-hour time
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-914
repos: [backend]
created: 2026-09-22
updated: 2026-09-22
---

# SAN-914 — format time_from/time_to before they reach the email template

## Request

Follow-up to SAN-906/SAN-913: admin sets an event's Schedule as Time From `12:00 am` / Time To
`01:30 am` (shown that way in the admin Info tab). The `event-speaker-registration` email the speaker
receives instead shows `Time: 00:00:00 - 01:30:00` — fix it so the email's time matches what the admin
actually set.

## Investigation finding

The two values are not actually different data — `12:00 am` and `00:00:00` are the same instant, just
in different formats (12-hour am/pm vs. raw 24-hour `HH:MM:SS`). Confirmed there is no staleness or
timezone-shift bug here: `sendEventSpeakerRegistrationEmail()` in
`sc-saas-backend/src/modules/global/admin-actions/admin-actions.service.ts` reads `event.timeFrom`/
`event.timeTo` fresh from the DB at send time (no cached/stale copy involved) — it simply never
formatted them before handing them to the Handlebars template.

## Root cause

`sendEventSpeakerRegistrationEmail()` passed `event.timeFrom`/`event.timeTo` straight through as the
raw DB `"HH:MM:SS"` strings. The sibling method `events.service.ts`'s public event-registration email
(`sendEventRegistrationPublicEmail`) already solves this exact problem for the same data shape —
`moment(event.date + ' ' + event.timeFrom).format('hh:mm a')` — but `sendEventSpeakerRegistrationEmail`
had never been updated to match; it predates that fix and was never touched by it.

## Fix

`admin-actions.service.ts`, `sendEventSpeakerRegistrationEmail()`: format `time_from`/`time_to` with
the same `moment(event.date + ' ' + event.time*).format('hh:mm a')` call before adding them to the
attributes object passed to `sesEmailService.sendEventSpeakerRegistrationEmail()`. `moment` was already
imported in this file. `date` left untouched — not reported as wrong, out of scope.

## Design decisions taken (not asked, judgment calls)

- **Reused the existing convention exactly rather than introducing a new date-formatting helper.**
  `events.service.ts` already solves this identical problem for a near-identical email; matching it
  keeps the two speaker/attendee-facing event emails visually consistent and avoids a second way of
  doing the same thing in the codebase.
- **Did not touch `date` field formatting** (`event.date.toString()`), even though the sibling method
  also wraps date in `getFormattedEventDate()` — the user only reported the time as wrong, and the date
  reads correctly as-is (e.g. `2026-09-23`); changing untouched, uncomplained-about output is scope
  creep for a narrow bug fix.

## Verified

- `npx tsc --noEmit` clean.
- `npx eslint` clean (0 errors) on the changed file after `--fix` for a prettier line-length nit.
- Confirmed by reading `events.service.ts:1330-1331` that this is the codebase's own established
  pattern for the same `time_from`/`time_to` → email-attribute mapping, not an invented one.

## Not verified — genuinely outstanding

No live send test (no admin login in this environment) — needs a real resend to confirm the email now
renders e.g. "12:00 am - 01:30 am" instead of "00:00:00 - 01:30:00".

## Rollout

Not committed. Awaiting review and a real send-test from the user.

## Open questions

None blocking.
