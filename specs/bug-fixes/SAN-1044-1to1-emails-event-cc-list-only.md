---
id: SAN-1044
title: 1:1 event emails go only to the event's CC list + the admin who created the event (no desk/super-admin copies)
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1044
repos: [backend]
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1044 — event CC list only

## Request

QA: a 1:1 "Meeting scheduled" email was CC'd to 11 `@sanchiconnect.com` admins plus the event's own CC
address (`cccmailevent@…`, the only address in that event's "CC Emails on Notification Emails" field).
Decision (user): 1:1 event emails go **only** to the addresses added to the event's CC list and to **the
admin who created the event**. No super admins, desk admins or other admins.

## Root cause

- `MeetingsService.sendScheduledMeetingEmail()` applies the platform-wide `Feature.CC_DESK_COMMUNICATION`
  rule on every call: it CCs every admin whose role code is the user's desk (`startup_desk` …),
  `super_admin` or `program_manager` and who has `cc_communication = 1`. It also sends the acting admin a
  separate `meeting-created-cc-admin` email. This is pre-existing and shared with non-event meetings.
- SAN-998 applied the same desk rule to the 1:1 alerts (new application / slot full / withdrawn), and
  SAN-998/1006 CC'd the acting admin on speaker-chosen, event-live, reject, reversal, reschedule and
  cancel-event emails.

## Fix (sc-saas-backend)

- `sendScheduledMeetingEmail()`: new optional last parameter `eventCcOnly` (default `false`). When `true`
  it skips the desk-CC lookups, the separate admin email and the ICS admin attendee. Only
  `events.service.ts`'s 1:1 booking passes `true`; every other caller is unchanged.
- `events.service.ts`: the alerts no longer add desk-CC admins. Reject / reversal / reschedule / cancel
  event CC only `event.ccEmails`. The now-unused imports were removed.
- `admin-actions.service.ts`: speaker-chosen and event-live CC only `event.ccEmails`. Event-live is a no-op
  again when there are no recipients.
- Kept: `event.ccEmails` still includes the creator admin (SAN-1007). The user and the speaker are still
  direct recipients where they were. `actingAdminId` (SAN-1006) is still used for
  `approvedBy` / `rejectedBy` / `reversedBy`, but no longer receives email.

## Resulting CC on every 1:1 event email

The event's CC list + the admin who created the event. Nobody else.

## Verified

- `npx tsc --noEmit` clean; existing ses-email + admin-actions suites pass (5 suites, 40 tests).
- Not exercised against a live send.

## Open questions

None.
