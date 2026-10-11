---
id: SAN-963
title: Remove External Meeting URL option from 1:1 reschedule modal
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-963
repos: [admin]
created: 2026-09-23
updated: 2026-09-23
---

# SAN-963 — In-built Meeting Tool only in the reschedule modal's Meeting Settings

## Request (revised mid-implementation — see below)

Events → an event's Attending tab → per-attendee "Reschedule event booking" modal, for a 1:1 Meeting
event with Delivery Mode = Online.

**First version of the ask:** hide the whole "Meeting Settings" card (In-built/External radios +
Meeting URL) from this modal entirely, even for Online events. Implemented and put in review.

**Revised ask, after seeing the live modal again:** don't hide the card — keep "Meeting Settings" and
"In-built Meeting Tool" visible, but remove only the "External Meeting URL" option (and the Meeting URL
input tied to it). In-built Meeting Tool becomes the sole, default-checked option. Explicit instruction:
"existing flow broke nhi karna hai" (don't break the existing flow).

## Investigation finding

The card is gated on `event_type == "one_to_one"` AND `delivery_mode == "online"` — unchanged by this
revision. It's still not shown at all for a 1:1 Offline event, same as before either version of this
fix.

## Root cause / context

Not a bug — a deliberate UX narrowing. Each 1:1 slot has its own `meeting_tool_type`/
`meeting_external_url` on `events_attendees`, settable at original booking (`add_attendee.php`, which
still offers both In-built and External) and, until now, re-settable at reschedule too.

## Fix (final)

`themes/default/html/events/reschedule_booking.php`:
- Restored the `delivery_mode == "online"` gate around the "Meeting Settings" card (undoing the
  first version's full removal).
- Removed only the "External Meeting URL" radio and the "Meeting URL" text input. The "In-built
  Meeting Tool" radio is now the only option, rendered `checked` unconditionally rather than
  conditionally on the attendee's stored value — there's nothing else to select, so any reschedule
  through this modal for an online 1:1 attendee forces `meeting_tool_type` to `"inbuilt"`, even for an
  attendee originally booked with an external link.
- Restored the submit handler's `meeting_tool_type` read (`input[name="meeting_tool_type"]:checked`)
  and re-added it to the AJAX payload, guarded by `if (meetingToolType)` so nothing is sent for a 1:1
  Offline event (where the radio doesn't exist) — mirrors the controller's own `isset()` guard.
- Left `meeting_external_url` out of the submit payload entirely — with External gone, there's no
  input to read it from; the controller already only reads it when `meeting_tool_type == "external"`,
  which can no longer happen from this form.

`modules/events/reschedule_booking.php` (controller) — **unchanged from the first version's fix**: the
`isset($_POST['meeting_tool_type'])` guard around the `events_attendees` update still applies and is
still necessary, now for the 1:1 Offline case specifically (where the field is genuinely never sent).
The removed `$postData['meeting_tool_type']`/`['meeting_external_url']` forward to the backend (dead
code — `RescheduleAttendeeDTO` never declared these fields, `whitelist: true` was already stripping
them) also stays removed; unaffected by this revision.

## Design decisions taken (not asked, judgment calls)

- **Kept a checked radio input rather than dropping to a plain label + hidden field.** "Existing flow
  broke nhi karna hai" was explicit; reusing the exact same
  `input[name="meeting_tool_type"]:checked` read in the submit handler is the smallest change that
  keeps the surrounding JS/controller contract identical to before, just with one fewer selectable
  value.
- **Forces a previously-external attendee to in-built on their next reschedule**, rather than, say,
  leaving their `meeting_tool_type` untouched if it was already "external". Not explicitly asked, but
  the alternative (silently keeping a now-unrepresentable "external" value while the UI shows nothing
  but a checked "In-built" radio) would be a confusing, inconsistent state — what the UI shows should
  match what gets saved.

## Verified

- `php -l` clean on both changed PHP files.
- `git status --short` — `modules/events/reschedule_booking.php`,
  `themes/default/html/events/reschedule_booking.php`, `themes/default/html/events/details.php` (fix),
  `modules/events/module.spec.md` (docs).
- Confirmed `add_attendee.php` untouched — still offers both meeting-tool options at original booking,
  per agreed scope.

## Follow-up: blank space below Save (same issue, UI consequence of the fix above)

Removing the External Meeting URL option (and, for a 1:1 Offline event, the whole card) shortened this
form's real content, but the parent page's iframe wrapping it had a fixed
`min-height: 600px` (`themes/default/html/events/details.php`,
`#loadRescheduleEventBookingIframeBox`) — sized for the old, taller content. Left blank space below
Save.

**First attempt (reverted):** dynamically measure the iframe's same-origin `contentWindow.document.body.scrollHeight`
on the iframe's `load` event and set the iframe's height to match, instead of a fixed number. **This
broke the modal** — the `load` event fired before the iframe content's own JS (chosen-select,
datetimepicker) finished laying itself out, so the measured height came out too small and visibly cut
off the Agenda field, Meeting Settings, and the Save button entirely. Caught immediately from a
screenshot and reverted.

**Fix (shipped):** lowered the iframe's inline `min-height` from `600px` to `480px` — sized for the
old, taller two-radio + Meeting URL card; the new content is shorter (one radio, or no Meeting Settings
card at all for 1:1 Offline). Kept `scrolling="yes"` (unchanged) as a safety net, so a longer Agenda or
any future content addition scrolls inside the modal instead of silently clipping, rather than betting
on a second attempt at exact dynamic sizing.

## Not verified — genuinely outstanding

No live end-to-end test: this environment has no admin-panel login. Needs a real check — open the
reschedule modal for a 1:1 Online event's attendee (including one originally booked as External),
confirm only "In-built Meeting Tool" shows and is checked, submit, and confirm
`events_attendees.meeting_tool_type` is `"inbuilt"` / `meeting_external_url` is `null` afterward. Also
confirm a 1:1 Offline event's reschedule modal still shows no Meeting Settings card at all.

## Rollout

Not committed. Awaiting review and a real test from the user.

## Open questions

None blocking.
