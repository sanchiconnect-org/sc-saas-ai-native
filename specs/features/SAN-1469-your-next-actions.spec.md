---
id: SAN-1469
title: "Notifications Phase 2 — EX-02 Your next actions (dashboard card, up to five ranked actions)"
type: feature
status: done                    # approved 2026-10-08 (OQs resolved by Mahima); implemented 2026-10-08; browser check on a dev tenant pending
linear: https://linear.app/sanchiconnect/issue/SAN-1469/notifications-p2-ex-02-your-next-actions   # project "Enhancement"
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-02 (W-01 annotation 4), Phase 2"
repos: [backend, frontend]      # dependency order
contracts:
  api:
    - "GET api/v1/notifications/counters (EXISTING) — two ADDITIVE fields: `connectionsWaitingLong` (number) and `eventsToday` ([{uuid, title, timeFrom}])"
    - "No new routes"
  flags:
    - notification_centre_enabled   # EXISTING — gate
  events: []
tenant_scoped: true
depends_on: [SAN-1381]
created: 2026-10-08
---

# Notifications Phase 2 — EX-02 Your next actions

## Reference
- **BRD:** EX-02 (W-01 annotation 4). The only source text is Linear SAN-1469:
  > A ranked list of up to five actions, each with a single button: people waiting more than 3 days (D3), deadlines within 72 hours not yet applied to, unopened job applicants, events today, profile gaps. Ranking favours people waiting and deadlines over general content.
- **Builds on:** the SAN-1381 counters (`closingSoon`, `jobs.perJob`), the dashboard-v2 catch-up card (SAN-1439), and the SAN-1472 event-attendance rules.

## Current state (checked 2026-10-08)

| Action | Data today | Gap |
|---|---|---|
| People waiting > 3 days | `counters.connections` = all pending Received [EV `notification-counters.service.ts`, `countReceivedRequests`] | No age split. **Add** `connectionsWaitingLong`, using the same Received-list query (`getConnectionsRequestByType`) with a created-before cut-off, so it can't drift (NFR-03). |
| Deadlines ≤ 72 h, not applied | `counters.opportunities.closingSoon[]` {type, uuid, title, closesAt} [EV] | none |
| Unopened job applicants | `counters.jobs.perJob[]` {jobUuid, jobTitle, count} [EV] | none |
| Events today | The dashboard's `upcomingEvents` is the **platform** event list, not the user's registrations [EV `dashboard.service.ts:71-86`] | **Add** `eventsToday`: events the user is attending, on today's IST date, with the same attendance rules as SAN-1472 |
| Profile gaps | `ProfileService.profileCompleteness$` {percentage, forms} [EV `dashboard-v2.component.ts:272`] | none |

- `dashboard-pending-tasks` is an empty stub (title only) [EV], so there is no overlap.

## Proposed design (recommended defaults; every [DDP] needs a decision)
- **P-1 Placement [DDP OQ-1]:** a "Your next actions" card in **dashboard-v2**, directly under the catch-up card. It is shown only with `notification_centre_enabled`, and hidden when it would be empty. The legacy role dashboards are unchanged, the same as SAN-1439.
- **P-2 Items and ranking [DDP OQ-2]:** fixed priority, at most 5 items in total:
  1. **People waiting:** "N connection requests waiting over 3 days" → **Review**, which opens `/connections/pending-requests`. One aggregated item.
  2. **Deadlines:** one item per `closingSoon` entry, soonest first: "{title} closes in N days" → **Apply** (challenge or program route).
  3. **Job applicants:** "N new applicants for {job}" → **Review** (job details). One item per job, most applicants first.
  4. **Events today [DDP OQ-3]:** "{title} today at {time}" → **View**, which opens the events calendar.
  5. **Profile gaps [DDP OQ-4]:** "Complete your profile ({p}%)" → **Complete** (profile edit), shown when completeness is below 100 %.
- **P-3 Muting:** in-app muted categories (SAN-1478 `inAppMuted`) hide the matching items: connection requests, deadlines, job applications and event reminders.
- **P-4 Backend:**
  - `connectionsWaitingLong` reuses `ConnectionsRepository.getConnectionsRequestByType(…, RECEIVED, …)` with a new optional `createdBefore` filter (now − 3 days), taking only the total.
  - `eventsToday` is a new counter-repository query: `events_attendees` attending and not rejected, joined to live events whose IST date is today. One-on-One events use the attendee's own slot date and time. At most 5 rows.

## Acceptance criteria
- [ ] With the flag on, the card lists at most 5 items in the P-2 order, each with exactly one button that opens the right page.
- [ ] Requests pending 4 days and 1 day → "1 connection request waiting over 3 days".
- [ ] A challenge closing in 2 days and not applied to → an Apply item. Once applied to, it disappears (it's no longer in `closingSoon`).
- [ ] An event the user is attending today → a "today" item. An event they aren't attending → none.
- [ ] Profile at 100 % → no profile item.
- [ ] Nothing to show → no card. Flag off → no card, and the counters response has no new fields read.
- [ ] Muted categories don't appear.

## Open questions

None. All four were resolved by Mahima on 2026-10-08, by accepting the recommended defaults (OQ-1 dashboard-v2 under the catch-up card; OQ-2 fixed priority with a cap of 5; OQ-3 events I'm attending today; OQ-4 completeness below 100 %).

## Implementation notes (2026-10-08)

Uncommitted, on `ai_native_setup_mahima`.

- **Backend:**
  - `ConnectionsRepository.getConnectionsRequestByType` gains an optional 5th parameter `createdBefore`. Existing callers are unchanged.
  - `connectionsWaitingLong` uses the Received list's own query and user set, with a cut-off of now − 3 days.
  - `NotificationCountersRepository.getEventsToday(userId)` uses the SAN-1472 attendance rules. Its IST date is the attendee's slot for 1:1 events and the event date for every other type. It returns at most 5 rows, earliest first.
  - Both fields are additive on `GET notifications/counters`, and both are gated by their module flags.
- **Frontend:**
  - `core/state/notifications/next-actions.util.ts` (`buildNextActions`) builds the ranked list.
  - `modules/dashboard-v2/components/dashboard-next-actions` is the card. It is flag-gated and hidden when empty.
  - Profile → the dashboard's `handleEditProfile()`.
  - Deadlines → the challenges or programs list pages, the same as the catch-up card.
  - Events → `/calender/events?eventId=`.
  - Jobs → `/jobs/{uuid}/details`.
- **Verification:**
  - Backend jest 220 pass; the real-MySQL integration suite passes 14/14 (`eventsToday` rules, the 3-day cut-off).
  - Frontend Karma 22/22, and the AOT build passes.
  - Not run: a browser check on a dev tenant.
- **Gates:** additive optional fields only; user- or team-scoped queries on the tenant's own DB; no new flags.
