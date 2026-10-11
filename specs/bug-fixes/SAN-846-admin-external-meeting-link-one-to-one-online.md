---
id: SAN-846
title: "Admin: External Meeting Link hidden for 1:1 Meeting events when Delivery Mode is Online"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-846
repos: [admin]
commit: sc-saas-admin@76ec020a (branch ai_native_setup_vishali, pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-846 — Admin External Meeting Link visibility for 1:1 online events

## Problem
On the Event Edit → Details page in `sc-saas-admin` (`themes/default/html/events/edit/info.php`), the "External Meeting Link" field (`#eventRegistrationUrl`) never appeared for Event Type = "1:1 Meeting" (`one_to_one`), even with Delivery Mode = Online. Every other online event type shows this field.

Reported against `adm.thub.sanchidev.in/events/edit/info/<uuid>/gfhgf` — a 1:1 Meeting event set to Online showed no External Meeting Link field on Step 1.

## Root cause
`SPEC_ERROR`, not a code defect. Git blame traced the exclusion to commit `035414173` ("event meeting link issue fixed", Nov 28 2024) — before that, 1:1 + Online did show the field. Three gates in `themes/default/html/events/edit/info.php` explicitly excluded `one_to_one`:
- initial page load (~line 2252)
- `#event_type` change handler (~line 2309)
- `#delivery_mode` change handler (~line 2328)

Investigated whether the 2024 exclusion was compensating for an automatic video-link mechanism before touching anything: confirmed `event_registration_url` is functionally dead for `one_to_one` bookings — the real join link for a 1:1 online meeting is generated per-booking via VideoSDK in `sc-saas-backend`'s `bookOneToOneMeetingAndSendConfirmation()` and stored as `meetingCode` on the `meetings` table, unrelated to this admin field. Confirmed with the requester (Vishali) that this is a UI-visibility-only ask — restore the field to match every other online event type, no booking-flow wiring in scope.

## Fix
Removed the `$this->event['event_type'] != "one_to_one"` / `event_type != "one_to_one"` condition from all three gates, so `#eventRegistrationUrl` shows whenever Delivery Mode = Online regardless of Event Type. Three one-line changes, no other logic touched.

No API/DTO/flag/tenant-scoping impact — pure client-side visibility toggle in one admin theme file.

## Blast radius
`sc-saas-admin` only, Event Edit → Details page. Does not touch the booking/meeting-link generation flow in `sc-saas-backend` or `sc-saas-frontend` — the value entered here is still not read anywhere downstream for `one_to_one` events; it is purely a form field the admin can now see and fill in.

## Verification
`php -l` unavailable in this environment (PHP not installed on the dev machine used) — noting the gap rather than skipping it silently. Manually diffed the change: only the boolean sub-condition was removed from three `if` statements, brace/structure unchanged, confirmed via `git diff`. No test framework exists for `sc-saas-admin` (per workspace convention) — manual repro in the admin UI is the substitute verification.

Vishali had this committed and pushed as `sc-saas-admin@76ec020a` on `ai_native_setup_vishali` (repo's active per-developer branch, confirmed via `git branch -vv` — `ai_native_setup` itself is 89 commits behind and stale for this repo). Linear moved to Done.

## Related
None.
