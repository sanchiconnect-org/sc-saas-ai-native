---
id: SAN-857
title: "\"View Details\" broken in Meeting Requested email for event-slot applications"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-857
repos: [backend]
commit: sc-saas-backend@2dd0e1cd
created: 2026-09-18
updated: 2026-09-18
---

# SAN-857 — dead "View Details" link on the event-application acknowledgment email

## Request

Reported via Gmail screenshot: the "[Meeting] Meeting requested" email sent when a startup applies for a 1:1
event slot (Manual approval mode) has a "View Details" button that does nothing.

## Root cause (SPEC_ERROR — called out in the code's own comment)

`sc-saas-backend/src/modules/events/events.service.ts`'s manual-approval branch (~line 1187) reuses the
`meeting-requested` email template for this notification, per a comment referencing [[SAN-784|SAN-784]]:
"reuses the existing 'meeting requested' template as the closest fit... since no dedicated template exists for
this new notification." That template's content hardcodes its CTA button as `href="{{ meeting_link }}"`
(`sc-saas-backend/src/modules/global/admin/spa_email_templates.repository.ts`, `meeting-requested` entry —
confirmed by grepping the template's actual content, not just its declared `shortCodes` list), but this call
site passed `meeting_link: ''` — there's genuinely no meeting/join link at this stage (nothing is booked until
an admin approves the application), so the field was left blank, leaving the button's `href` literally empty.

**Note:** an earlier pass at this fix incorrectly targeted `reschedule_link` instead, based on a misreading of
the template's large one-line HTML content. `reschedule_link` is passed into `mapAttribute()` for this template
too (matches the other, non-event `sendMeetingRequestedEmail()` callers in `meetings.service.ts`, which do use
it) but is never actually referenced anywhere in `meeting-requested`'s own content — only `meeting_link` is.

## Design decision (resolved with the user, not invented)

Three options were presented: point the link at the event's own page, remove the Link/CTA row entirely (new
template variant), or something else. **Resolved: point it at the event's page.**

## Fix

`events.service.ts` — imported `frontEndUrl` from `core/utils/app.utils.ts` (already used elsewhere for
building frontend links, e.g. `getUserTypeRegistrationUrl()`), and changed:

```ts
meeting_link: '',
```
to
```ts
meeting_link: `${frontEndUrl}/events/register/${event.uuid}`,
```
(`reschedule_link` stays `''` — genuinely unused by this template.)

Confirmed `events/register/:eventId` (mounted from `PublicEventsModule` in `sc-saas-frontend`'s
`app-routing.module.ts`) is the only event-detail-capable route in the frontend, and that its component
(`PublicEventsComponent`) calls `GlobalService.getPlatformEventById(uuid)` — i.e. the route param is a UUID,
matching `EventsEntity`'s (via `AbstractEntity`) generated `uuid` column, not the numeric `id`.

## Not addressed (flagged, not fixed)

The underlying gap SAN-784's own comment already named — this notification still borrows a template meant for
an actual meeting request with a real join/reschedule link, not an "application submitted, pending review"
acknowledgment. A dedicated template without an implied-actionable Link/CTA row would be the cleaner long-term
fix. Out of scope here per the resolved decision to just give the button a real destination.

## Verification

`npx tsc --noEmit -p tsconfig.json` clean. No regression test proposed — this is a one-line data-value fix (the
string passed into an existing, already-tested email-sending call), not new logic.

## Rollout

Committed and pushed to `ai_native_setup`: `2dd0e1cd`.

## Open questions

None blocking for this narrow fix. The "dedicated template" gap noted above is a real follow-up but not
requested here.
