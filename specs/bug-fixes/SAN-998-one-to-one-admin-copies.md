---
id: SAN-998
title: Admin copies on 1:1 event emails — acting admin on admin actions, desk-CC admins on applicant alerts
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-998
repos: [backend, admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-998 — admins get copies of the 1:1 event emails

## Request

"The admin also [should be] sent those mails as previously sent to admin, for every action done on the admin
side." Also: who received the one-line "…applied for a slot on…" email?

## Investigation finding

- **Who got the one-line alert:** `events.user_id`. In sc-saas-admin that column is only ever written by the
  Speakers step (`modules/events/edit/speakers.php`: null for multi-speaker, the chosen or created user
  otherwise). So the old plain-text alerts always went to the **speaker**, never an admin. The `events`
  table has no creator/owner-admin column (the `list.php` insert writes only uuid/title/status/dates).
- **Admin emails that existed before:** only on **approve**, including manual add and the approve that ends
  a reschedule. `MeetingsService.sendScheduledMeetingEmail(…, admin)` → `sendMeetingEmailToAdmin()` emails
  the admin who clicked, with `meeting-created-cc-admin`. Every other admin action (reject, reversal,
  cancel event, reschedule's old-slot cancellation, speaker chosen, publish) sent the admin nothing. The
  admin appeared only as the ICS organizer.
- **Existing admin-CC rule for user-driven emails:** `Feature.CC_DESK_COMMUNICATION`. It CCs admin users
  whose role code matches the users' desks (`getUsersDesks`) and who have `ccCommunicationEmails = true`.
  This is used by meetings (`sendScheduledMeetingEmail`) and connections.

## Decisions (user)

- **Admin actions → the admin who did the action** is CC'd on every email that action sends, using the
  existing templates. Approve keeps its existing `meeting-created-cc-admin` email. There are no new
  templates.
- **Applicant-driven alerts** (new application, slot full, withdrawn) have no acting admin → the event's
  CC list **plus the desk-CC admins** ("admin also send, add in that cc, as previously sent").

## Fix

| Email | Trigger | CC added |
|---|---|---|
| Speaker chosen (`event-speaker-registration`) | admin, Speakers step | acting admin |
| Event is live (`event-one-to-one-live`) | admin, publish | acting admin (so it now also sends without a CC list) |
| Rejection (`meeting-request-rejected`) | admin reject / auto-reject on approve / remove pending | acting admin |
| Reversal (`meeting-cancelled` ×2) | admin remove approved | acting admin |
| Reschedule old-slot cancellation (`meeting-cancelled`) | admin reschedule | acting admin |
| Cancel event (`meeting-cancelled`) | admin cancel | acting admin |
| Approve (`meeting-scheduled-*`) | admin approve | unchanged; the admin already gets `meeting-created-cc-admin` |
| New application / slot full / withdrawn | applicant | desk-CC admins (when the feature is on) |

- `events.service.ts`: `performOrdinaryReject()` now takes the acting `AdminUsersEntity` instead of
  `rejectedByAdminId` (same three callers). The desk-CC lookup is written inline at the two alert sites, in
  the same shape as `meetings.service.ts`. The alerts send whenever the combined list (CC list + desk
  admins) is non-empty.
- `admin-actions.service.ts`: `checkIsValidAdmin()`'s returned admin is now kept in both
  `sendEventSpeakerRegistrationEmail()` and `sendEventOneToOneLiveEmail()`.
- All CC lists are de-duplicated, with empty values dropped. Scope: One-on-One events only.

## Verified

- `npx tsc --noEmit` clean.
- Not exercised against a live tenant or SMTP.

## Open questions

None.
