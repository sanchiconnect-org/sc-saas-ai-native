---
id: SAN-997
title: Templated 1:1 alert emails (new application / slot full / withdrawn) to the CC list + fix slot time in 1:1 emails
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-997
repos: [backend, admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-997 — replace the plain-text 1:1 alerts with the existing template format; fix slot times

## Request

QA screenshot: an email "New application: final" arrived with only one bare sentence ("Sandeep Kumar applied
for a slot on "final" (Sep 25th, 2026, 09:15).") and no logo or layout. The user asked why it was sent, who
receives it, and wanted it in the old format that admin mails use, going to the CC list. Clarified
afterwards: **"copy the old design, new text"**. Each email keeps its own template, but its HTML is an exact
copy of an already-running template, with only the wording changing.

## Investigation finding

- **Why and to whom:** the email is the SAN-784 "new application" alert (`notifyEventOwner()`). It was sent
  with the generic `sendEmail()` as `<p>${message}</p>` (no template) to `event.userId`, which for a 1:1
  event is the **chosen speaker**. The server that sent it runs the deployed code, without SAN-995.
- **Slot time bug:** `convertTimeToTimezone()` (`core/utils/date.ts`) parses its input as UTC and converts it
  to IST. `events_attendees.time_from` is already IST wall-clock (EVENT_SCHEDULE_TIMEZONE), so the
  rejection email showed a 09:15 slot as `02:45 pm (IST)`. Confirmed by a render test for both `09:15` and
  `09:15:00`.

## Fix

- Three new templates, module `events`, added the standard way (enum codes, seeds, admin `emails.php`
  mapping):
  - `event-one-to-one-new-application`: heading "New Application"; "**{applicant}** has applied for a
    One-on-One slot in **{event}**". Details Event / Applicant / Date / Time / Status.
  - `event-one-to-one-slot-full`: heading "Slot Full"; "A One-on-One slot in **{event}** has reached its
    application cap…". Details Event / Date / Time / Application Cap.
  - `event-one-to-one-application-withdrawn`: heading "Application Withdrawn"; names the applicant (the old
    text said "an applicant"). Details Event / Applicant / Date / Time.
- **Template format (user, final):** all five 1:1 templates (these three plus SAN-993/994) use the
  **meeting** template design (`[Meeting] Meeting Created (CC to Admin)`: grey page, white bordered card,
  logo row, greeting, intro line, grey-label details table, closing line, Cheers row and the "This email was
  emailed to…" footer). They're **written in the code as readable, indented HTML**, not one minified line.
  Only the wording differs. They're rendered with `handlebars.compile()` like the meeting sender
  (`{{{ brand_logo }}}`). There's no button and no Handlebars blocks. (Earlier iterations used a shared
  layout helper and then the facility design; both were superseded at the user's request.)
- **Time = the slot the user chose**, from–to (`09:15 am - 09:30 am`, built from
  `events_attendees.time_from`/`time_to`). This applies in the rejection, application-received and all
  three alert emails.
- **No new helper functions (user, 2026-09-25: "already code uses that format, apply that, nothing new
  create").** Following the existing patterns exactly:
  - each template's HTML is an inline `templateContent` literal, like every other seed entry;
  - one send method per template, in the existing `(toEmail, data, ccEmails?)` style:
    `sendEventOneToOneNewApplicationEmail`, `sendEventOneToOneSlotFullEmail`,
    `sendEventOneToOneApplicationWithdrawnEmail` (and SAN-993/994's two);
  - `events.service.ts` calls them directly at the three alert sites (To = first CC address, the rest
    CC'd, skipped when there's no CC list). The old `notifyEventOwner()` wrapper is removed;
  - slot times are formatted inline with `moment(date + ' ' + time).format('hh:mm a')` for both start
    and end, the same way the speaker email formats its times. `convertTimeToTimezone()` is no longer
    imported in events.service.

## Verified

- `npx tsc --noEmit` clean. `php -l` clean on `emails.php`.
- Render test (scratchpad `render-test.ts`): the real seed method against a fake repo, with all five
  templates rendered through `handlebars.compile()` exactly as the senders do. No unresolved tokens, the logo
  `<img>` and subjects render, and the time shows as `09:15 am - 09:30 am` (the old formatter gave
  `02:45 pm (IST)` for a 09:15 start).

## Open questions

None.
