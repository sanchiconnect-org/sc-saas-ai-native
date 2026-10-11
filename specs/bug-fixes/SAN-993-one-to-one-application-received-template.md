---
id: SAN-993
title: New "application received" email template for 1:1 applicants, CC'd to the event's CC list
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-993
repos: [backend, admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-993 — dedicated applicant acknowledgment for a Manual-mode 1:1 application

## Request

When a startup applies for a slot from the frontend, the applicant gets an email, and so does the CC list.
If no suitable template exists, create one following the existing template structure. The user explicitly
approved creating a new template for this.

## Investigation finding

- The frontend `POST v2/events/attend/:eventUUID` goes to `EventsService.attendEvent()`. In Manual mode the
  applicant got the reused **meeting** template `meeting-requested` (SAN-784 picked it as "closest fit"), with
  no CC. In Automatic mode the applicant is booked straight away and already gets meeting-scheduled with CC,
  so that path is unchanged.
- The slot time was formatted with `convertTimeToTimezone()`, which is wrong for slot times. See SAN-997.

## Fix

- New template `event-one-to-one-application-received` ("[Event] One-on-One application received"),
  module `events`, added the standard way:
  - `EmailTemplateCode.EVENT_ONE_TO_ONE_APPLICATION_RECEIVED` (`core/constants/enum.ts`)
  - seed entry in `spa_email_templates.repository.ts` → `installDefaultEmailTemplates()`
  - `EventOneToOneApplicationReceivedEmailData` (`core/types/ses-email.type.ts`)
  - `SESEmailService.sendEventOneToOneApplicationReceivedEmail(toEmail, data, ccEmails?)`
  - admin `config/default-settings/emails.php` → `"event-one-to-one-application-received" => "events"`
- **Design, per the user (final):** the **meeting** template design (`[Meeting] Meeting Created (CC to
  Admin)`): grey page, white bordered card, logo row, "Hi …" greeting, intro line, grey-label details
  table, closing line, "Cheers {brand}" row and the "This email was emailed to…" footer. In the code it's
  written as **readable, indented HTML** (one element per line, like the facility templates' source) instead
  of a single minified line, with the editor-only `data-offset-key` wrapper spans left out. Only the wording
  differs. It's an inline `templateContent` literal like every other template in the file: no shared helper
  (per the user: "nothing new created") and no Handlebars blocks.
- The send method follows the meeting sender (`sendMeetingEmailToAdminEmail`) exactly:
  `(toEmail, data, ccEmails?)`, rendered with `handlebars.compile()`, so the template uses
  `{{{ brand_logo }}}` for the logo `<img>`.
- Content: "Your application for a One-on-One slot has been received for: **{event}**". Details:
  Speaker / Date / Time / Status (Applied). The closing says they'll get another email once approved or
  rejected. **Time is the slot the applicant chose**, from–to (e.g. `09:15 am - 09:30 am`).
- `attendEvent()` Manual branch uses the new method with `event.ccEmails`. The speaker is not a recipient.

## Verified

- `npx tsc --noEmit` clean.
- Render test (scratchpad): ran the real `installDefaultEmailTemplates()` against a fake repo, captured the
  seed and rendered it with `handlebars.compile()` exactly as the sender does. No unresolved `{{ }}` tokens,
  the logo `<img>` renders, and the time shows as `09:15 am - 09:30 am`.
- `php -l` clean on `emails.php`.

## Rollout

Backend first. `installDefaultEmailTemplates()` inserts any template code a tenant doesn't have yet, so
this new code reaches **every** tenant on the next backend restart (unlike edits to an existing template,
which only reach new tenants).

## Open questions

None.
