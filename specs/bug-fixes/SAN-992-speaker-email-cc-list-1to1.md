---
id: SAN-992
title: CC the event's CC list on the event-speaker-registration email (1:1)
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-992
repos: [backend]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-992 — speaker-chosen email is CC'd to the 1:1 event's CC list

## Request

For a One-on-One event, the admin-set CC list (`events.cc_emails`, Event Details step) must be copied on
every email the event sends "from start to end", starting with the email the speaker gets when an admin
chooses them in the Speakers step.

## Investigation finding

- Admin Step 2 (`sc-saas-admin/modules/events/edit/speakers.php`, `submitAction=updateSpeaker`) calls
  `GET v1/admin-actions/speaker-event-registration/:eventUUID/:adminToken` (SAN-906) after every save.
- `AdminActionsService.sendEventSpeakerRegistrationEmail()` loads the full `events` row (so `ccEmails` is
  available) but `SESEmailService.sendEventSpeakerRegistrationEmail()` had **no CC parameter at all**. The
  CC list was never copied here.
- For a 1:1 event the speaker is `events.user_id` (a registered user, or the user row speakers.php creates
  for a non-registered speaker). The meeting booked on approve is between that user and the applicant.

## Fix

- `ses-email.service.ts`: `sendEventSpeakerRegistrationEmail(toEmail, data, icalEvent, ccEmails?)`, an
  additive optional param set on the `SESEmailDataDto` as a true `cc` (visible, not BCC). It stays unset when
  empty, so every other caller is unchanged.
- `admin-actions.service.ts`: passes `event.ccEmails` only when `eventType === one_to_one` and the list is
  non-empty.

## Recipient rule agreed with the user (applies to SAN-992–997)

The speaker is emailed **only** when chosen, when an applicant is accepted by admin, and on reschedule.
By explicit decision, the speaker also keeps the meeting-cancelled email on an admin reversal and on event
cancellation. The CC list gets everything.

## Verified

- `npx tsc --noEmit` clean. Lint: no new errors, only pre-existing CRLF/prettier noise in these files.
- Not exercised against a live tenant/SMTP yet. The `sc-saas-3rdparty-webservices` gateway is not
  cloned in this workspace, so forwarding of `cc` to the provider is assumed from existing callers (the
  desk-CC feature and `contactEmail` CCs already rely on it).

## Open questions

None.
