---
id: SAN-996
title: Call event-live endpoint on 1:1 publish + register the new event email templates
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-996
repos: [admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-996 — admin side of the 1:1 CC-list emails

## Fix

- `modules/events/details.php` (`publishEvent`) and `modules/events/edit/publish.php` (`makeEventLive`),
  which are both publish paths: read `uuid`/`event_type`/`publish_status` **before** the update. Then, only for
  a `one_to_one` event that was **not already published**, call
  `GET {api_server_url}v1/admin-actions/event-live/{uuid}/{adminToken}` (SAN-994).
  - Fire-and-forget, the same pattern as the SAN-906 speaker call in `edit/speakers.php`. A failed call never
    fails the publish response.
  - The "not already published" guard stops the email being re-sent when publish is clicked again.
- `config/default-settings/emails.php`: all five new codes mapped to `events`:
  `event-one-to-one-application-received`, `event-one-to-one-live`, `event-one-to-one-new-application`,
  `event-one-to-one-slot-full`, `event-one-to-one-application-withdrawn`.
- `/* */` comments only (admin comment style). The one `//Admin Logs` comment next to the edit was converted.

## Verified

- `php -l` clean on all three files.

## Rollout

Deploy after the backend (SAN-992–995, SAN-997). If admin ships first, the event-live call just gets a 404
and is ignored, and publishing still works.

## Open questions

None.
