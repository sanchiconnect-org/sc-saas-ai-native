---
id: SAN-995
title: CC the event's CC list on every remaining 1:1 email + stop sending admin alerts to the speaker
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-995
repos: [backend]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-995 — close the remaining CC gaps in the 1:1 event email flow

## Investigation finding: recipient audit of every 1:1 email (before this fix)

| Action | Template | To | CC list |
|---|---|---|---|
| Speaker chosen | event-speaker-registration | speaker | ❌ (SAN-992) |
| Apply, Manual mode | meeting-requested (reused) | applicant | ❌ (SAN-993) |
| New application / cap reached / withdrawn | plain text | **speaker** (`event.userId`) | ❌ |
| Apply, Automatic mode / admin approve | meeting-scheduled-to-receiver/-sender | applicant + speaker | ✅ |
| Reject / auto-reject | meeting-request-rejected | applicant | ✅ |
| Reversal | meeting-cancelled ×2 | applicant + speaker | ✅ |
| Reschedule: old slot cancelled | meeting-cancelled | applicant + speaker | ❌ |
| Cancel whole event | meeting-cancelled | each booked pair | ❌ |

The rejection email also always said "this slot has been booked by another applicant", even for a direct
admin rejection.

## Fix (`events.service.ts`)

- Reschedule and cancel-event: pass `event.ccEmails` (1:1 only) into `sendCancelledMeetingEmail`.
- The new-application / cap-reached / withdrawal alerts go to the CC list and no longer to the speaker.
  They were templated in SAN-997, which also removed the old `notifyEventOwner()` wrapper; the send
  methods are called directly at the three call sites.
- `performOrdinaryReject()`: the reason line varies by `rejectionCause`. It stays "booked by another
  applicant" for `AUTO_REJECTED_ON_APPROVAL` and becomes "your application for this slot was not approved"
  for `MANUAL`. Same template, so FR-1.2 AC3 still holds.

## Decision (user, 2026-09-25)

The speaker keeps the meeting-cancelled email on an admin reversal and on event cancellation ("stay same").

## Verified

- `npx tsc --noEmit` clean.

## Open questions

None.
