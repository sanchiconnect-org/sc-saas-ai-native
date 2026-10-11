---
id: SAN-1010
title: Show Reschedule only for approved 1:1 attendees (not pending or rejected)
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1010
repos: [admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1010 — Reschedule only after approval

## Request

Admin → event → Attending tab: Reschedule should be available **only after an attendee is approved**. It
shouldn't appear for a pending (applied) or a rejected attendee.

## Investigation finding

- `themes/default/html/events/details.php` rendered Reschedule for every `approval_status`, gated only on
  `!is_past_slot` (SAN-964).
- This was more than cosmetic. `sc-saas-backend`'s `recheduleEventAttendeeRequest()` ends by calling
  `approveEventAttendeeRequest()`. So rescheduling a **pending** attendee silently approved them (in Manual
  mode also auto-rejecting the other applicants on that slot), and rescheduling a **rejected** attendee
  revived them as approved.

## Fix (sc-saas-admin)

- `themes/default/html/events/details.php`: the Reschedule button renders only when
  `approval_status == "approved"` and the slot isn't past. Approve/Reject (pending only) and Delete/View
  Details are unchanged.
- `modules/events/reschedule_booking.php`: loads `approval_status`, and the `rescheduleBooking` POST returns
  `{error: true, errorMessage: "Only an approved booking can be rescheduled."}` for a non-approved attendee
  without calling the backend. This covers a stale Attending tab or a crafted request. The modal's existing
  error popup shows the message.

## Resulting Attending-tab actions

| Status | Approve / Reject | Reschedule | Delete / View Details |
|---|---|---|---|
| Pending (applied), future slot | ✅ | ❌ | ✅ |
| Approved, future slot | ❌ | ✅ | ✅ |
| Rejected | ❌ | ❌ | ✅ |
| Any status, past slot | ❌ | ❌ | ✅ |

## Verified

- `php -l` clean on both files.
- Not exercised in a browser.

## Not changed

The backend reschedule endpoint itself still accepts any status (sc-saas-admin is its only caller, now
guarded). A backend-side guard would be defence-in-depth, tracked as an optional follow-up if wanted.

## Open questions

None.
