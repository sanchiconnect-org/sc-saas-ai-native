---
id: SAN-970
title: Speaker email omits External Meeting Link section entirely (Venue-only)
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-970
repos: [backend]
created: 2026-09-24
updated: 2026-09-24
---

# SAN-970 — don't show a dead External Meeting Link for a 1:1 Online event's speaker email

## Request

For an Event Type = "1:1 Meeting" + Delivery Mode = "Online" event, the SAN-906 speaker-registration
email showed an "External Meeting Link" section with an "Open Link" button pointing nowhere. In Person
(offline) events should keep showing Venue as before — not reported as broken.

## Investigation finding

Confirmed by code, not assumption: `events.event_registration_url` is genuinely `null` for every
one_to_one event, by design (SAN-788) — `themes/default/html/events/edit/info.php` hides the
`#eventRegistrationUrl` field entirely whenever `event_type == "one_to_one"`, and
`modules/events/edit/info.php` explicitly skips server-side validation of that field for the same event
type, because a 1:1 event has no single shared meeting URL — each attendee gets their own per-slot link
on `events_attendees.meetingToolType`/`meetingExternalUrl` instead.

## Root cause

`sendEventSpeakerRegistrationEmail()` (`admin-actions.service.ts`) branched purely on
`event.deliveryMode`, with no check on `event.eventType` and no null-check on `eventRegistrationUrl` —
so for a 1:1 + Online event it unconditionally set `event_location_type = 'External Meeting Link'` and
`event_link = event.eventRegistrationUrl` (always `null` for this event type), producing a dead "Open
Link" button in the sent email.

## Fix

Guarded the ONLINE branch with `event.eventType !== EventTypes.ONE_TO_ONE`. For a 1:1 Online event,
`event_location_type`/`event_location`/`event_link` all stay at their declared empty-string defaults —
the location section of the email gets nothing to render. The OFFLINE (Venue) branch is now reached via
`else if (event.deliveryMode != EventSpeakerDeliveryMode.ONLINE)`, unconditional on event type exactly
as before — Delivery Mode = In Person still shows Venue regardless of event type, unaffected by this
change.

## Design decisions taken (not asked, judgment calls)

- **Left the OFFLINE/Venue branch's condition unchanged in spirit** (still fires whenever delivery mode
  isn't online), just restructured as an `else if` rather than a bare `else`, so the new one_to_one
  exclusion on the ONLINE side doesn't accidentally fall through into the Venue branch for a 1:1 Online
  event — it should render neither section, not silently become "Venue" instead.
- **Did not touch the DB-stored email template itself.** The actual Handlebars markup
  (`EmailTemplateCode.EVENT_SPEAKER_REGISTRATION`) lives in a per-tenant DB row, not this repo, so its
  exact behavior for an empty `event_location_type` couldn't be inspected from code. Flagged as a
  genuinely open question in the Linear issue rather than assumed away.

## Verified

- `npx tsc --noEmit` clean, `npx eslint` clean (0 new errors — pre-existing unrelated unused-import
  warnings only) on the changed file.
- Confirmed `EventTypes.ONE_TO_ONE` and the `eventType` column name against `events.entity.ts` and
  `core/constants/enum.ts` directly rather than guessing the identifier.
- `git status --short` — only `admin-actions.service.ts` (fix) + `module.spec.md` (docs) touched.

## Follow-up: the template itself also needed a fix

A live test on the real tenant (screenshot-confirmed) showed the "Open Link" button still rendering
for a 1:1 Online event even with `event_location_type`/`event_link` left empty by the backend fix
above. Root cause: the email template (`event-speaker-registration`) never checked `event_link` at
all — its location cell was `{{#if event_location}} {{event_location}} {{else}} <Open Link button
href="{{event_link}}"> {{/if}}`, so whenever `event_location` was falsy it unconditionally rendered the
Open Link button, regardless of whether `event_link` actually had a value. The backend leaving
`event_link` empty was necessary but not sufficient — the template's own logic was the other half of
the bug.

Found the template's actual source: `sc-saas-backend/src/modules/global/admin/spa_email_templates.repository.ts`'s
`installDefaultEmailTemplates()` seed data (not, as initially assumed, entirely absent from the repo —
an earlier investigation in this session missed this 568KB file). Three iterations, in order:

1. **`<tr>`-wrap attempt.** `{{#if event_location}}<tr>...</tr>{{else}}{{#if event_link}}<tr>...</tr>{{/if}}{{/if}}`,
   so the whole row would disappear for a 1:1 Online event while a genuine webinar's Open Link kept
   working. **Live-tested on the real tenant and confirmed broken**: the admin's WYSIWYG email-template
   editor visibly stripped the `{{#if}}`/`{{else}}`/`{{/if}}` markers on save (they sat as raw text
   directly between `</tr>` and `<tr>`, outside any `<td>` — invalid table content), leaving both
   `<tr>`s rendering unconditionally: an empty Venue row *and* an always-shown, still-dead Open Link
   button — worse than the original bug. Reverted.
2. **Cell-only attempt.** `{{#if event_location}} {{event_location}} {{else}} {{#if event_link}}
   <Open Link> {{/if}} {{/if}}`, kept entirely inside the existing value `<td>` (editor-safe — no raw
   text outside a cell). Technically correct and would have worked, but superseded by:
3. Drop the Open Link branch entirely, for every event, not just one_to_one —
   `{{#if event_location}} {{event_location}} {{/if}}`. External Meeting Link no longer renders in
   this email at all; only Venue does, when set. Deliberate scope reduction agreed with the user, not
   just a targeted bug fix — a genuinely working non-1:1 online event's speaker email also loses its
   meeting link now, same as the 1:1 case.
4. **Live-tested, confirmed working for the cell content** — but an empty row (empty label + empty
   value cell) still rendered below "Time" for an event with no Venue, since step 3 only emptied the
   cell contents, not the `<tr>` itself.
5. **Attribute-injection attempt, live-tested, confirmed BROKEN — worse than a cosmetic issue.**
   Tried conditionally injecting `display: none` into the `<tr>`'s own `style` attribute via
   `{{#unless event_location}} display: none;{{/unless}}`, reasoning that Handlebars markers inside an
   attribute value (a plain string to any parser) would survive where a freestanding text node between
   `<tr>`s did not. **This stopped the email from sending at all** — most likely the editor runs the
   `style` attribute through a CSS validator that doesn't recognize Handlebars syntax as valid CSS and
   corrupts the surrounding markup when it tries to sanitize it, breaking Handlebars compilation
   entirely. Reverted immediately back to step 4's known-working version.

**Final decision:** stop attempting to hide the row. Three attempts to remove/hide it (a `<tr>`-wrap,
and an attribute-injection) both caused real, live regressions on the user's actual tenant — one
silently broke email sending outright. Accepted the cosmetic empty-row trade-off from step 4 as the
final, shipped state. If the row genuinely needs to disappear, that requires either a different email
template engine/editor that doesn't mangle raw Handlebars, or a direct database edit of the template
row bypassing the WYSIWYG editor's sanitization — both out of scope for this fix and out of reach from
this sandbox (no direct access to the live tenant's DB).

Backend (`admin-actions.service.ts`) simplified to match step 3: removed the `event.eventType` branch
entirely (the `EventTypes` import along with it, now unused), removed the `event_link` variable and its
entry in the email-data object — the ONLINE branch does nothing at all now; only the
`deliveryMode != ONLINE` (Venue) branch remains. Left dead code would have misrepresented what the
email actually does.

**Important caveat, explained to the user:** `installDefaultEmailTemplates()` only *inserts* a row for
a `templateCode` that doesn't already exist in a tenant's `spa_email_templates` table — it never
updates `templateContent` on an existing row (it only backfills the separate `defaultTemplateContent`
column when that happens to be null, and nothing in this codebase reads that column back to re-apply
it). So this seed-file fix only reaches **brand-new tenants** provisioned after this change lands.
Every already-provisioned tenant (including the one used for live testing) keeps its stale template
content until someone manually re-applies the corrected HTML via Developer → Email Management in the
admin panel — which the user was walked through directly, with the exact HTML to paste, since this
sandbox has no way to reach that tenant's DB directly.

## Verified

- `npx tsc --noEmit` clean on the changed repository file.
- `npx eslint` — 2 pre-existing prettier errors elsewhere in this 568KB file (lines 391, 3712), confirmed via `git diff --stat` (1 line changed) to be unrelated to this edit, not introduced by it.
- The pasted-back HTML given to the user for manual application was built directly from the exact raw
  HTML they copied from the live Admin UI's source-code view, not reconstructed from a guess — same
  attributes, styling, and `data-offset-key`s preserved verbatim in both branches.

## Verified (live, on the real tenant)

- Venue set → email correctly shows "Venue: Delhi" (screenshot-confirmed).
- No Venue, no Open Link → email sends correctly, location row renders empty (screenshot-confirmed) —
  the accepted final cosmetic trade-off.
- Confirmed the failed attribute-injection attempt (step 5 above) by observing email delivery stop
  entirely, then confirmed delivery resumed immediately after reverting.

## Rollout

Not committed by me. The user has been applying each iteration directly to their live test tenant via
Developer → Email Management, confirming behavior as we went (see Verified above) — the code-repo side
(`spa_email_templates.repository.ts`, for future tenants) matches the final, live-confirmed version.

## Follow-up (2026-09-24): missing cell padding, in the repo seed

Separate from the Open Link work above: this same template's Date/Time/Venue table `<td>` cells had no
padding at all in the repo seed — only `background-color`/`height`, no `padding` of any kind (worse
than `meeting-scheduled-to-sender`'s cells, which at least had some padding before its own SAN-977 fix,
just missing `padding-left`). Text sat flush against every cell edge on all sides.

Fixed by adding `padding: 10px;` to all 6 `<td>` cells (3 rows × label+value), matching the convention
every other template in this seed file uses. Verified via `tsc --noEmit` (clean) and `git diff` (2 lines
changed, confirmed to contain only the intended `padding: 10px;` additions).

Same caveat as every other seed-file fix: reaches new tenants only, not any already-provisioned one.

## Open questions

None blocking. Fully hiding the empty row (rather than accepting it) is a known, explicitly deferred
follow-up — would need a different template-editing path than the current WYSIWYG editor.
