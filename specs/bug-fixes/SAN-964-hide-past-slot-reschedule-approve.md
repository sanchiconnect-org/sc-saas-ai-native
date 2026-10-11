---
id: SAN-964
title: Hide Reschedule/Approve/Reject for past-slot attendees on the Attending tab
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-964
repos: [admin]
created: 2026-09-23
updated: 2026-09-23
---

# SAN-964 — gate Reschedule/Approve/Reject on a per-slot past-date check

## Request

Events → a 1:1 Meeting event → Attending tab: once an attendee's booked slot (date already gone, e.g.
"18 Sep, 2026" with today past that) is in the past, the Reschedule and Approve actions should no
longer show for that row. **Revised mid-implementation:** same treatment for Reject too — all three
(Approve, Reject, Reschedule) gated identically. Only Delete and View Details stay available for a
past slot.

## Investigation finding

- Every attendee row already carries `date`/`time_from`/`time_to` (`modules/events/details.php:280-282`
  query) — no new query needed.
- Existing codebase precedent for an "expired" comparison: `modules/finance_management/proforma_invoices/list.php`
  computes "now" once in the controller and hands it to the template, rather than calling
  `time()`/`date()` inline in the view. Followed here.
- **Timezone caveat, confirmed before writing any code:** `events_attendees.date`/`time_from`/`time_to`
  are wall-clock values in **Asia/Kolkata** (same as `events`, per the backend's
  `EVENT_SCHEDULE_TIMEZONE` constant and the SAN-710 fix history) — not necessarily this admin server's
  own timezone. A naive `strtotime()`/`time()` comparison would silently misread the stored value.

## Fix

`modules/events/details.php` (controller): added `$istNow = new DateTime('now', new
DateTimeZone('Asia/Kolkata'))`, computed once before the attendee loop. Inside the loop, for each row,
`$slotEndIst = DateTime::createFromFormat('Y-m-d H:i:s', $v['date'] . ' ' . $v['time_to'], new
DateTimeZone('Asia/Kolkata'))`, and `is_past_slot = $slotEndIst !== false && $slotEndIst < $istNow`
added to `$arrayObject` alongside the existing `date`/`time_from`/`time_to` fields — carries through
`$newArray` into `$oneToOneEvent[$date][$response]` with no further plumbing needed.

`themes/default/html/events/details.php` (template): the existing `if ($value['approval_status'] ==
"pending_moderation")` block wrapping both Approve and Reject now also requires `&&
!$value['is_past_slot']` — both hidden together for a past slot, not just Approve. Reschedule wrapped
in its own `if (!$value['is_past_slot'])`.

## Design decisions taken (not asked, judgment calls)

- **Delete and View Details stay available for a past slot; Reject does not (revised).** First pass
  kept Reject available as a "still-legitimate cleanup action" judgment call — the user then explicitly
  asked for the same treatment on Reject, so it's now gated identically to Approve. Delete/View Details
  were never asked to change and still work regardless of `is_past_slot`.
- **Compared against `time_to` (slot end), not just `date`.** The user's example was a whole day already
  past, but the more precise and still-correct check is the slot's own end time — a same-day slot whose
  end time has already passed is exactly as "past" as one from a fully bygone date, and this
  automatically covers the whole-day case too (an earlier date's `time_to` is always before "now").
- **Computed `is_past_slot` in the controller, not the template**, matching the one existing
  "expired" precedent in this codebase (`proforma_invoices/list.php`) rather than introducing a second,
  inconsistent way of doing the same kind of check.
- **Left the backend gap (no server-side past-slot validation) untouched**, per explicit scope
  agreement with the user — flagged in the Linear issue as a known, separate follow-up if wanted later.

## Verified

- `php -l` clean on both changed files.
- `git status --short` — `modules/events/details.php`, `themes/default/html/events/details.php` (fix),
  `modules/events/module.spec.md` (docs).
- Verified the `DateTime`/`DateTimeZone('Asia/Kolkata')` comparison logic directly (`php -r`, a
  standalone snippet, not touching the app): a slot dated 2026-09-18 correctly evaluates as past
  relative to "now" (2026-09-23 in this sandbox), and a slot dated 2027-01-01 correctly evaluates as
  not past.

## Not verified — genuinely outstanding

No live end-to-end test: this environment has no admin-panel login. Needs a real check — an event with
at least one attendee slot in the past and one in the future, confirming Reschedule/Approve/Reject are
hidden only for the past one, and Delete/View Details still show for both.

## Rollout

Not committed. Awaiting review and a real test from the user.

## Open questions

None blocking. If the backend past-slot guard (noted as out of scope above) is ever wanted, that's a
separate follow-up issue, not resolved here.
