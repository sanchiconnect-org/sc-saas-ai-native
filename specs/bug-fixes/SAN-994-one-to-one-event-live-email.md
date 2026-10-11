---
id: SAN-994
title: New "event is live" email template + admin-actions endpoint, sent to the 1:1 event's CC list on publish
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-994
repos: [backend]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-994 — tell the CC list when a 1:1 event goes live

## Request

"Send the mail to ccmail when event live": the CC list should hear about the event from the start. The user
explicitly approved creating a new template for this.

## Investigation finding

- No email of any kind was sent on publish. Publishing is a direct Medoo write in PHP, in two places:
  `sc-saas-admin/modules/events/details.php` (`submitAction=publishEvent`) and
  `modules/events/edit/publish.php` (`submitAction=makeEventLive`). There was no backend call.

## Fix

- New template `event-one-to-one-live` ("[Event] One-on-One event is live"), module `events`, added the
  standard way (enum code, seed, `EventOneToOneLiveEmailData`, `SESEmailService.sendEventOneToOneLiveEmail()`,
  admin `emails.php` mapping). Uses the meeting template design, written as readable indented HTML and rendered with `handlebars.compile()`, like SAN-993.
  Rows: Speaker / Schedule (one line per day from `events.dates`, 12-hour) / Approval / Mode-or-Venue.
- New endpoint `GET api/v1/admin-actions/event-live/:eventUUID/:adminMd5`:
  - **Auth model (stated explicitly):** the `adminMd5` backdoor token checked by `checkIsValidAdmin()`,
    identical to every sibling admin-action. Not a public route.
  - Returns a no-op success (not an error) for a non-one_to_one event, an event that isn't published, or an
    empty CC list, so admin can call it unconditionally.
  - To = first CC address, the rest CC'd. The speaker is not a recipient.
- The admin call site is SAN-996.

## Verified

- `npx tsc --noEmit` clean. Render test: no unresolved tokens.
- Contract check: the only consumer is sc-saas-admin (SAN-996), and it calls exactly this path. No existing
  controller or DTO changed.

## Open questions

None.
