---
id: SAN-906
title: Send speaker-registration email on Speaker Details submit
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-906
repos: [admin]
created: 2026-09-22
updated: 2026-09-22
---

# SAN-906 — wire up the unused event-speaker-registration email

## Request

Events → Edit → Speakers → Speaker Details form (`adm.thub.sanchidev.in/events/edit/speakers/<uuid>`):
when **Speaker Type** is set to either **Registered** or **Non-Registered** and the form is submitted,
an email must be sent to the speaker, using the existing `event-speaker-registration` template.

## Investigation finding

The backend already had a complete, ready-to-use sender for this exact template —
`GET v1/admin-actions/speaker-event-registration/{eventUUID}/{adminToken}`
(`sc-saas-backend/src/modules/global/admin-actions/admin-actions.service.ts:4144-4213`), including the
`event-speaker-registration` template render, an ICS calendar attachment, and venue/online-link
derivation from `event.deliveryMode`. It had never been called from anywhere in either repo — this was
a "wire it up" task, not a "build it" task.

## Root cause

The endpoint requires `events.speaker_email` to be non-null (throws `EVENT_SPEAKER_NOT_EXISTS`
otherwise) and reads `receiver_name` from `events.speaker_name`. But
`sc-saas-admin/modules/events/edit/speakers.php`'s `updateSpeaker` handler had both fields **commented
out** of the array it persists to `events` — so those columns were always `null`, and the endpoint
could never have succeeded even if something had called it.

## Fix

`modules/events/edit/speakers.php`, inside the `updateSpeaker` action:

1. Capture `$_POST['speaker_type']` into `$originalSpeakerType` before the handler overwrites it to
   `"registered"` later in the same branch (once a non-registered speaker's `users` row is created) —
   needed to know which of the two ways to resolve the speaker's email/name.
2. Resolve `$speakerEmail`/`$speakerName`: non-registered → read straight from `$_POST` (already used
   above to create the new user); registered → look up `users` by the submitted `user_id`, since the
   "Choose a Speaker" dropdown only submits an id, not name/email.
3. Persist both onto the `events` row (un-commented, populated from the resolved values instead of raw
   `$_POST`).
4. On a successful save, call the backend endpoint via `generatePartnerRandomStringForBackdoor()` +
   cURL — the same admin-token pattern this same module already uses for `approveAttendee()` in
   `add_attendee.php`. Fire-and-forget: a failed send does not fail the "speaker updated" response.

## Design decisions taken (not asked, judgment calls)

- **Fires on every successful save, not just the first time a speaker is added.** The request said
  "submit karne par email jaani chahiye" (email should go out on submit) without qualifying "only the
  first time" — implemented literally. No dedupe/one-time-only guard exists. Flagged in the module spec
  as a real, deliberate trade-off rather than an oversight; easy to add a guard later if re-sending on
  every edit turns out to be unwanted.
- **`speaker_bio`/`speaker_linkedin_url` left commented out**, untouched — unrelated to sending this
  email and outside what was asked; not fixed alongside this while touching the same array.

## Verified

Statically, by cross-checking directly against source rather than assuming:
- `events.speaker_name`/`events.speaker_email` column names match the TypeORM entity exactly
  (`sc-saas-backend/src/modules/events/entities/events.entity.ts:147-151`).
- Route path and param order (`eventUUID` then `adminMd5`) match the controller exactly.
- `api_server_url` constant format (`<api_url>api/`) combines correctly with the route.
- No per-route `@Features` flag gate on this endpoint (consistent with its sibling methods in the same
  controller).
- `php -l` clean. `git status --short` — only `speakers.php` (this fix) and `module.spec.md`
  (documentation) touched in `sc-saas-admin`.

## Not verified — genuinely outstanding

No live end-to-end test: this environment has no admin-panel login, so the Speaker Details form has not
actually been submitted and no email has been confirmed to land in an inbox, for either Speaker Type
value. Needs a real test on a real event before this is trustworthy as "done."

## Rollout

Not committed. Awaiting review and a real send-test from the user.

## Open questions

None blocking. If re-sending the email on every re-save (not just the first) turns out to be unwanted,
that's a follow-up, not resolved here.
