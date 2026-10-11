---
id: SAN-1472
title: "Notifications Phase 2 — EX-05 Event reminders (24 h and 1 h before a registered event)"
type: feature
status: done                    # approved 2026-10-08; implemented 2026-10-08; SAN-1829/1830 + SAN-1472 Done; manual dev-tenant run + EXPLAIN still pending
linear: https://linear.app/sanchiconnect/issue/SAN-1472/notifications-p2-ex-05-event-reminders-24-h-and-1-h   # parent issue (project "Enhancement"); sub-issues SAN-1829 (backend), SAN-1830 (frontend)
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-05, Phase 2 (not wireframed)"
repos: [backend, frontend]      # dependency order. tenants/admin only if OQ-5, OQ-6 or OQ-8 are decided against the recommended default
contracts:
  api:
    - "GET   api/v1/notifications           (backend, EXISTING — one new `type` value `event_reminder` in the list; shape UNCHANGED)"
    - "GET   api/v1/notifications/counters  (backend, EXISTING — UNCHANGED under the recommended default; additive `eventReminders` + `bell` term ONLY if OQ-4 is decided 'count in bell')"
    - "No NEW routes. No new cron-trigger route (see OQ-12)"
  flags:
    - notification_centre_enabled   # EXISTING (SAN-1401) — recommended gate (OQ-5)
    - events                        # EXISTING module flag (Feature.EVENTS) — recommended second gate
    - cron_enabled                  # EXISTING master cron switch — consumed, unchanged
    - events_notifications          # EXISTING, tenants-only today — NOT touched under the recommended default (OQ-5)
  events:
    - "notifications.type — ONE new enum value `event_reminder` (backend NotificationType + frontend NotificationTypes)"
    - "cron_jobs — ONE new CronJobName `EVENT_REMINDER` (seeded INACTIVE, like every non-core job)"
    - "socket 'fetch-count' (EXISTING, payload-free) — emitted to each reminded user"
tenant_scoped: true
depends_on: [SAN-1381, SAN-1478]   # Phase 1 bell/centre code merged; SAN-1478 in-app preference key `eventReminders` merged
created: 2026-10-08
---

# Notifications Phase 2 — EX-05 Event reminders

## Reference and evidence tags

- **BRD:** EX-05, Phase 2, not wireframed. The BRD itself is not in the workspace. The only source text is Linear SAN-1472 (no comments):
  > Reminders 24 hours and 1 hour before a registered event, with the joining link or venue.
  > Note: check the existing backend `modules/cron/meeting-reminder.service.ts` and the `events_notifications` tenant flag before designing anything new.
- **Builds on:** `specs/features/SAN-1381-notifications-action-driven-dashboard.spec.md` (Phase 1), `specs/features/SAN-1471-application-status-updates.spec.md` (EX-04, writer pattern), `specs/features/SAN-1478-notification-preferences-in-app.spec.md` (EX-19, `eventReminders` key).
- **Tags** (per `specs/spec-authoring-practices.md`): **[EV]** evidenced with `file:line`; **[INFERRED]** drawn from code, not stated; **[NOT SPECIFIED]** the code/BRD says nothing; **[DESIGN DECISION PENDING]** needs a human decision (see Open questions).
- Paths without a repo prefix are in `sc-saas-backend/src/`.

## Problem

A user who registers for an event gets one confirmation email at registration (webinars only) and nothing afterwards. There is no reminder before the event starts, in-app or otherwise. EX-05 asks for two reminders, 24 h and 1 h before a registered event, carrying the joining link (online) or the venue (in person).

## Current state (checked against code, 2026-10-08)

### 1. `meeting-reminder.service.ts` — what exists, and why it is not reused as-is

- `MeetingReminderCronService.sendMeetingReminderEmail()` [EV `modules/cron/meeting-reminder.service.ts:59–217`] reminds the two parties of a **meeting** (`meetings` table), by **email + WhatsApp only** — no in-app row.
- Selection [EV `modules/meetings/repositories/meetings.repository.ts:1199–1226`]: accepted, not rejected, `NOT_STARTED`, `meetingType = FUNDRAISING`, `date = UTC today`, and `timeFrom = exactly (UTC now + saasSettings.meeting_reminder_in_mins)` to the minute (`getUTCTimeAheadMins()`, `core/utils/app.utils.ts:125–131`).
- **Idempotency is "the cron fires exactly once per matching minute"** (job seeded `*/1 * * * *`, `modules/cron/repository/cron-job.repository.ts:61–64`). There is no "sent" marker: a missed minute (restart, slow run) loses the reminder; a second process or an overlapping run would send it twice. [INFERRED from the code above]
- Single window (one configurable lead time), not two.
- **Overlap with events:** One-on-One event bookings create a `meetings` row via `createMeeting(..., MeetingModuleType.EVENT)` [EV `modules/events/events.service.ts:221–229`], and `createMeeting()` always sets `meetingType = FUNDRAISING` [EV `meetings.repository.ts:669`] with `defaultAccepted = true`. So **approved 1:1 event bookings already receive the meeting reminder email/WhatsApp** whenever the tenant's `MEETING_REMINDER` cron row is active. [INFERRED from the two citations]
- Side observation (out of scope, not fixed here): `meetings.date` holds the IST slot date while `timeFrom` is UTC [EV `events.service.ts:182–219`], and the selector compares against the UTC date — an IST slot before 05:30 may never match. [INFERRED]

**Conclusion:** the precedent to reuse is the **cron registration pattern** (CronJobName + seed + `CronService.setCronJobs()` switch), not the exact-minute selection or the missing sent-marker. EX-05 needs a window query plus an atomic per-(attendee, window, start) claim.

### 2. `events_notifications` tenant flag — traced

| Repo | Where | What it does |
|---|---|---|
| tenants | [EV `sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-users.entity.ts:1553–1559`] | boolean column, default `false` |
| tenants-admin | [EV `sanchiconnect-saas-tenants-admin/modules/tenant_management/_switch_sections.php:151`] | toggle in the Events switch section |
| admin | [EV `sc-saas-admin/themes/default/html/events/edit/publish.php:270`] | shows the "Broadcast Notification to Community" form (an invitation email to the community) on the event Publish step |
| backend | **absent** — no `Feature` enum member, no read [EV grep: no match in `sc-saas-backend/src`] | — |
| frontend | **absent** — not in `IFeatures` [EV grep: no match in `sc-saas-frontend/src`; `core/domain/brand.model.ts`] | — |

So today `events_notifications` means "allow the admin to broadcast an event invitation email". It does not gate any user-facing reminder. Reusing it for reminders would change its meaning and would require adding it to the backend `Feature` enum (invariant #1, `/trace-flag`). See OQ-5.

### 3. Cron scheduling (in-process, not external)

- Jobs are **in-process**: `CronService.setCronJobs()` builds a `cron` `CronJob` per active `cron_jobs` row, all in `Asia/Kolkata`, and registers it in `SchedulerRegistry` [EV `modules/cron/cron.service.ts:90–198`, e.g. `MEETING_REMINDER` at :182–198]. Every callback is wrapped by `runCronJob()` so a rejection is logged per job [EV :50–57].
- Master switch `cron_enabled` stops all jobs [EV :93–103]. Armed after bootstrap from `GlobalService` [EV `modules/global/global.service.ts:190`]; also re-armed by `PATCH /saas/settings` and `GET /clear/cache/all` [EV `modules/global/module.spec.md:145, 169`].
- New jobs are seeded once by name; only `SEND_EMAIL_QUEUE_EMAIL`, `SYNC_BROADCAST_EMAIL_STATS`, `RETRY_JURY_NDA_EMAILS` are seeded active, all others inactive [EV `cron-job.repository.ts:41–231`, :211–219].
- Operators flip `cron_jobs.active` through sc-saas-admin's generic table engine (`cron_jobs` is listed in `sc-saas-admin/modules/common.php:177`) — no admin code change needed to enable a new job. [EV + INFERRED]
- The `POST api/v1/notifications/cron/*` routes [EV `modules/notifications/notifications.controller.ts:298–335`] are **unauthenticated** manual triggers, not the scheduler [EV `modules/notifications/module.spec.md:74`]. Admin does not drive schedules. This spec does **not** add another one (OQ-12).
- Process model (one Node process or a cluster per tenant) is not in the repo [NOT SPECIFIED] — so the claim must be safe under concurrent runs.

### 4. Events data

**`events`** [EV `modules/events/entities/events.entity.ts`]
- `event_type` (`webinar`, `one_to_one`, `seminar`, `conference`, …) [:40–46; enum `core/constants/enum.ts:1571–1593`]
- `date`, `time_from`, `time_to` [:65–72]; multi-day `dates` JSON [:74–79]. Admin writes `date/time_from/time_to` = the **first** entry of `dates` on every save [EV `sc-saas-admin/modules/events/edit/info.php:360–369`].
- `delivery_mode` `online | in_person` [:116–122; enum `enum.ts:1636–1639`]
- **Joining link** = `event_registration_url` and **venue** = `location`. This is exactly how the existing registration email picks them [EV `events.service.ts:1406–1412`, :1488–1494]. [`event_registration_url` doubling as the join link is EV-by-usage; naming is misleading]
- Liveness: `publish` [:192], `cancelled` [:195], `archived` [:198], `publish_status` (`draft|published|cancelled|deleted`) [:32–38; `enum.ts:1646–1651`], `deleted_at` (AbstractEntity).
- Cancel: `cancelEvent()` sets `publish_status = cancelled`, `cancelled = 1` [EV `events.service.ts:1825–1828`].
- Reschedule: admin edits `dates`/`date`/`time_from` **directly in the DB** [EV `info.php:346, 360–369`] — no backend hook fires.

**`events_attendees`** [EV `modules/events/entities/event-attendees.entity.ts`]
- `user_id` nullable [:24–25], `event_id` [:27–28], `meeting_id` [:30–31], per-slot `date/time_from/time_to` [:33–40], `response` (`attending|declined|tentative|pending`) [:54–60; `enum.ts:963–968`], `type` `internal|external` [:77–83], `approval_status` (`pending_moderation|approved|rejected|rescheduled`) [:85–91; `enum.ts:1658–1663`].
- Writers and the status they leave:

| Path | Result | Evidence |
|---|---|---|
| Webinar RSVP attending | `response = attending`, `approval_status = approved` | `events.service.ts:1395–1400` |
| Webinar declined/tentative | `approval_status = rejected` | `events.service.ts:1374–1393` |
| Other non-1:1 types (seminar, conference, workshop, …) | `response = attending`, `approval_status` stays default `pending_moderation` — no branch sets it | `event-attendees.repository.ts:255–279`; `events.service.ts:1374–1449` only handles WEBINAR [INFERRED] |
| 1:1 Automatic | `approved` + meeting booked | `event-attendees.repository.ts:270–275`; `events.service.ts:1284–1290` |
| 1:1 Manual | `pending_moderation` until admin approves | `events.service.ts:1291–1293` |
| Public register (`/attend`, `/attend2`) | `user_id` NULL, `type = external` | `event-attendees.repository.ts:435–487` |
| Admin "add attendee" | `user_id` set only if chosen; `time_zone = Asia/Calcutta` | `sc-saas-admin/modules/events/add_attendee.php:196–219` |
| Withdraw (1:1) | row hard-deleted | `event-attendees.repository.ts:366–370` |

- The bell's existing "registered" test is `response = 'attending' AND deleted_at IS NULL` [EV `modules/notifications/repositories/notification-counters.repository.ts:324–326`].
- **Timezone:** event and slot times are IST wall-clock (`EVENT_SCHEDULE_TIMEZONE = 'Asia/Kolkata'`, `enum.ts:29`; SAN-710/SAN-997 notes at `events.service.ts:174–181` and `modules/events/module.spec.md:80`). The notifications module already computes IST in SQL (`IST_NOW_SQL = UTC_TIMESTAMP() + INTERVAL 330 MINUTE`, `notification-counters.repository.ts:49–52`).
- Paid events: `events.is_payment_required` [:184–190] is not checked anywhere in the attend flow [EV grep: only the entity declares it] — whether an unpaid registration is "registered" is [NOT SPECIFIED] (OQ-2).

**Existing event emails:** `sendEventRegistrationPublicEmail` (registration confirmation) and the 1:1 templates [EV `core/services/ses-email.service.ts:4696–5074`]. **No event reminder email or template exists.**

### 5. Notification Centre pieces to reuse

- `notifications` row: `to_user_id`, `title` (NOT NULL), `message`, `object_uuid`, `url`, `privacy`, `send_to`, `type` (MySQL enum), `has_read`, `read_at`, `actioned_at`, `category`, `source_type`, `source_id` [EV `modules/notifications/entities/notification.entity.ts:13–77`]. **No unique constraint** — cannot by itself guarantee exactly-once.
- `NotificationType` enum [EV `enum.ts:347–361`]; `NotificationCategory` `action_required|new|system` [EV `enum.ts:424–428`].
- In-app preference: `InAppCategory.EVENT_REMINDERS = 'eventReminders'` [EV `enum.ts:377–385`, value at :384 — the enum is named `InAppCategory`, not `InAppNotificationCategory`]. The type→category map `NOTIFICATION_TYPE_IN_APP_CATEGORY` has **no** event entry yet [EV `enum.ts:398–416`]. Muting is applied at read time; rows are always written [EV `modules/notifications/module.spec.md:59–66`].
- Frontend already shows the "Event reminders" toggle, gated on `features.events` [EV `sc-saas-frontend/src/app/modules/account/pages/notification-settings/notification-settings.component.ts:46`; `core/domain/profile.model.ts:28`].
- Writer precedent: `ApplicationStatusNotificationsService.notifyApplicationStatus()` — flag check, de-dup, one row per recipient, `fetch-count` per recipient, never throws [EV `modules/notifications/application-status-notifications.service.ts:56–92`]. It lives in its own `ApplicationStatusNotificationsModule` [EV `application-status-notifications.module.ts:12–21`] because of import cycles. **`NotificationsModule` imports `CronModule`** [EV `notifications.module.ts:27`], so a cron service cannot import `NotificationsModule` back — the same "small module" trick is needed.
- Counters: `bell` = connections + communityWall + jobs + (mode B opportunities) + meetings + `statusUpdates` [EV `modules/notifications/notification-counters.service.ts:417–423`]. NEW `notifications` rows of other types are **not** counted in `bell` (SAN-1381 Decision #3; SAN-1471 D-4 was an approved exception).
- Frontend: `NotificationTypes` [EV `sc-saas-frontend/src/app/modules/notifications/notifications.enum.ts:1–21`]; per-type icon/CTA map on `/notifications` [EV `modules/notifications/pages/notifications/notifications.component.ts:17–28`]; bell component [EV `shared/common-components/notification-bell/notification-bell.component.ts`]. Logged-in event landing: `/calender/events?eventId={uuid}` (opens the matching event) [EV `modules/calender/events-calender/events-calender.component.ts:261–262`; redirect precedent `modules/public-events/public-events.component.ts:149`].

### 6. Off-platform channels

- Email goes backend `SESEmailService` → sc-saas-3rdparty-webservices [EV workspace `CLAUDE.md`, "Email delivery"]; WhatsApp via `WhatsappService` (direct, not via the gateway) [EV `sc-saas-backend/CLAUDE.md`].
- Consent (EX-20) and quiet hours (EX-21) are separate, unbuilt Phase 2 items. Sending email/WhatsApp reminders before they exist risks shipping a channel with no consent check and no quiet-hours suppression (a 1 h reminder for an 08:00 event lands at 07:00). [INFERRED]

## Proposed design (every **[DDP]** item was decided as written — see Open questions, resolved 2026-10-08)

**P-1 — Channel: in-app only** [DDP → OQ-1]. Mirrors SAN-1471 D-6. No email, no WhatsApp, no sc-saas-3rdparty-webservices change.

**P-2 — Who is reminded** [DDP → OQ-2, OQ-3]
- `events_attendees` rows with `user_id IS NOT NULL`, `deleted_at IS NULL`, `response = 'attending'`, `approval_status <> 'rejected'`.
- **One-on-One:** only `approval_status = 'approved'` bookings, timed from the attendee's own slot (`events_attendees.date + time_from`).
- **Every other type:** timed from the event start (`events.date + events.time_from`).
- Event must be live: `deleted_at IS NULL`, `publish = 1`, `cancelled = 0`, `archived = 0`, `publish_status = 'published'`.
- Recipient = the attendee's own `user_id` only (registration is per user, `events.service.ts:1115–1279`), not the profile team. [INFERRED; departs from SAN-1471 D-10 on purpose]
- External/public attendees (`user_id` NULL) get nothing (no in-app identity).

**P-3 — Windows** [DDP → OQ-6, OQ-7]
- Start `S` = IST wall-clock `TIMESTAMP(date, time_from)`; now `N` = `UTC_TIMESTAMP() + INTERVAL 330 MINUTE` (same constant as `notification-counters.repository.ts:49–52`). All comparisons happen in SQL, in IST, so the server/cron timezone does not matter.
- **24 h reminder:** due when `S − 24h ≤ N < S − 1h`, and the registration existed before the 24 h mark (`events_attendees.created_at` (UTC) + 330 min `≤ S − 24h`). People who register inside the last 24 h already got a confirmation and get only the 1 h reminder.
- **1 h reminder:** due when `S − 1h ≤ N < S`.
- Catch-up: any due-but-unsent reminder still inside its window is sent on the next run (so a restart doesn't lose it, unlike the meeting reminder). Nothing is sent after `S`.
- Multi-day: only the first day (`events.date/time_from`) [DDP → OQ-3].

**P-4 — Exactly once per (attendee, window, start)** [technical → OQ-10, dev lead]
- Add two nullable `datetime` columns on `events_attendees`: `reminder_24h_sent_for`, `reminder_1h_sent_for`. Each holds the start `S` the reminder was sent for. Precedent for a per-row "sent" marker: `meetings.feedbackEmailSent` [EV `meetings.repository.ts:1254`], `events.broadcast_email_sent` [EV `events.entity.ts:212–218`].
- **Claim before write:** `UPDATE events_attendees SET reminder_24h_sent_for = :S WHERE id = :id AND (reminder_24h_sent_for IS NULL OR reminder_24h_sent_for <> :S)`. Only when `affectedRows = 1` does the run write the notification. Two overlapping runs or two processes can't both win (row-level atomic UPDATE). [INFERRED; standard MySQL semantics]
- **Reschedule:** a new `S` differs from the stored one, so both windows re-arm and fire again for the new time. An old reminder already sent is not retracted [DDP → OQ-8].
- **Cancel / reject / withdraw / unpublish:** excluded by the P-2 filters at selection time, so nothing further is sent.
- **Write failure after claim:** the reminder is lost for that window (at-most-once). Logged at `error`. Accepted trade-off vs. double-sending [DDP → OQ-10].
- Admin inserts into `events_attendees` (`add_attendee.php:197–215`) don't name the new columns, so they stay NULL — safe. TypeORM `synchronize: true` adds them [EV `core/database/database.module.ts:32`, per SAN-1471 spec]. Backend must deploy before the cron row is switched on.

**P-5 — Cron job**
- New `CronJobName.EVENT_REMINDER = 'eventReminder'`, seeded `*/5 * * * *`, **inactive** (default rule, `cron-job.repository.ts:211–219`), registered in the `setCronJobs()` switch via `runCronJob()`.
- Service `modules/cron/event-reminder.service.ts`, `EventReminderService.sendEventReminders()`:
  1. Return at once unless `saasFeatures[Feature.NOTIFICATION_CENTRE_ENABLED] === true` **and** `saasFeatures[Feature.EVENTS]` [DDP → OQ-5].
  2. One SQL per window selects due rows (P-2, P-3), bounded (e.g. `LIMIT 500`, rest on the next run).
  3. Per row, isolated in try/catch: claim (P-4) → write row → collect recipient.
  4. Emit `fetch-count` once per distinct recipient.
- Logging: `logger.log` for counts; `logger.error` only for real failures (both `warn` and `error` reach Sentry — `modules/cron/module.spec.md:59`).

**P-6 — Writer** (follows SAN-1471 A-1)
- `EventReminderNotificationsService.notifyEventReminder(...)` in a small `EventReminderNotificationsModule` (imports `GatewayModule`; provides `NotificationsRepository`), imported by `CronModule`. A new `NotificationsRepository.addEventReminderNotification(...)` builder.
- In-app preference: add `[NotificationType.EVENT_REMINDER]: InAppCategory.EVENT_REMINDERS` to `NOTIFICATION_TYPE_IN_APP_CATEGORY`. Rows are always written; muted users don't see them (SAN-1478 read-time rule) [DDP → OQ-11 (skip writing for muted users instead?)].

**P-7 — Row contract**

| Column | Value |
|---|---|
| `uuid`, `status` | TypeORM / `1` |
| `from_user_id`, `startups`, `investors` | `NULL` |
| `to_user_id` | `events_attendees.user_id` |
| `title`, `message` | §Copy |
| `object_uuid` | `events.uuid` |
| `url` | `/calender/events?eventId={events.uuid}` [DDP → OQ-9] |
| `privacy` / `send_to` | `private` / `user` |
| `type` | `event_reminder` |
| `has_read` / `read_at` / `actioned_at` | `0` / `NULL` / `NULL` |
| `category` | `new` [DDP → OQ-4] |
| `source_type` / `source_id` | `events_attendees` / attendee id |

**P-8 — Bell:** under the recommended default, reminder rows appear in the bell **panel** list and on `/notifications`, but do **not** add to the `bell` number (keeps SAN-1381 Decision #3) [DDP → OQ-4].

### Copy (default — product may edit, see OQ-13)

- `{event}` = `events.event_title`; `{date}` = `DD MMM YYYY` of `S`; `{time}` = `hh:mm a` of `S` + " IST" (format directly from the IST wall-clock value; never `convertTimeToTimezone()` — `modules/events/module.spec.md:80`).
- `{where}` = online: "Join link: {events.event_registration_url}" (or "Joining link will be shared by the organiser" if empty); in person: "Venue: {events.location}" (or "Venue to be announced" if empty). 1:1 online: "Join from your Meetings page".

| Window | Title | Message |
|---|---|---|
| 24 h | Event tomorrow | {event} starts on {date} at {time}. {where} |
| 1 h | Starting in 1 hour | {event} starts at {time}. {where} |

## Acceptance criteria

**Gate**
- [ ] With `notification_centre_enabled` off, or `events` off, or `cron_enabled` off, or the `EVENT_REMINDER` cron row inactive: no reminder row, no claim-column write, no socket emit.
- [ ] No email or WhatsApp is sent by this feature (P-1).

**Selection**
- [ ] A webinar attendee (`attending`, `approved`) registered 3 days before the event gets exactly one 24 h row and exactly one 1 h row.
- [ ] A seminar/conference/workshop attendee with `attending` + `pending_moderation` is reminded (P-2), unless OQ-2 decides otherwise.
- [ ] Declined/tentative webinar RSVPs, rejected attendees, withdrawn (deleted) 1:1 applications and Manual-mode 1:1 applications still pending are not reminded.
- [ ] Approved 1:1 bookings are reminded relative to their own slot time, not the event's first-day time.
- [ ] Attendees with `user_id` NULL are skipped without error.
- [ ] Cancelled, unpublished, archived, deleted or `publish_status <> published` events produce no reminder.
- [ ] Someone registering 10 h before start gets no 24 h reminder and does get the 1 h reminder.

**Timing and idempotency**
- [ ] With the job every 5 min, a reminder is written no earlier than its window start and no later than one run after it (≤ 5 min late), as long as the backend is up.
- [ ] After a restart inside a window, the due reminder is still sent once on the next run.
- [ ] Running `sendEventReminders()` twice concurrently (or twice in a row) for the same due rows writes each reminder once (claim `affectedRows` test).
- [ ] Moving an event (admin edits `dates`) after the 24 h reminder re-arms both windows for the new start; moving it before the reminders changes when they fire.
- [ ] Nothing is sent once `N ≥ S`.
- [ ] Times are compared in IST in SQL; a 09:00 IST event gets its 1 h reminder at 08:00 IST regardless of server timezone (jest with mocked SQL clock; manual check on a dev tenant).

**Rows, preferences, sockets**
- [ ] Each row matches §P-7, with copy per §Copy (online → join link; in person → venue).
- [ ] Each recipient gets a `fetch-count` emit after their rows are written.
- [ ] A user with `notification_settings.inApp.eventReminders = false` does not see reminder rows in `GET notifications` (read-time muting) and the row still exists.
- [ ] `bell` number is unchanged by reminder rows (unless OQ-4 decides otherwise).
- [ ] Mark-all-read marks reminder rows read (they are `new`).

**Frontend**
- [ ] `event_reminder` items render in the bell panel and on `/notifications` with an event icon; clicking marks read and navigates to `url`.

**Isolation**
- [ ] All queries/updates touch only this deployment's DB; no hard-coded host/tenant; `/check-isolation` passes.

## Per-repo plan

### backend (`sc-saas-backend`) — SAN-1829

- `core/constants/enum.ts`: `NotificationType.EVENT_REMINDER = 'event_reminder'` (:347–361; synchronize alters the MySQL enum); `NOTIFICATION_TYPE_IN_APP_CATEGORY` entry → `InAppCategory.EVENT_REMINDERS` (:398–416); `CronJobName.EVENT_REMINDER = 'eventReminder'` (:1432+).
- `modules/events/entities/event-attendees.entity.ts`: `reminder24hSentFor` / `reminder1hSentFor` (`datetime`, nullable) — subject to OQ-10.
- `modules/events/repositories/event-attendees.repository.ts`: `getDueEventReminders(window, limit)` (raw SQL per P-2/P-3) and `claimEventReminder(attendeeId, window, startAt): Promise<boolean>` (conditional UPDATE, `affected === 1`).
- `modules/notifications/`: `event-reminder-notifications.module.ts` + `.service.ts` (writer, P-6), `event-reminder.copy.ts` (§Copy), `NotificationsRepository.addEventReminderNotification()`.
- `modules/cron/event-reminder.service.ts` (P-5); register in `cron.module.ts`; seed in `repository/cron-job.repository.ts` (inactive, `*/5 * * * *`); `case CronJobName.EVENT_REMINDER` in `cron.service.ts`.
- Update `modules/cron/module.spec.md` (job list) and `modules/notifications/module.spec.md` (new type, writer).
- Jest: window maths at the edges (24h−1s, 1h, S), late registrant, 1:1 slot timing, every exclusion filter, claim race (second claim returns false), reschedule re-arm, flag/`events` off, NULL user, row contract, muting map, failure isolation (one bad row doesn't stop the batch).

### frontend (`sc-saas-frontend`) — SAN-1830

- `modules/notifications/notifications.enum.ts`: `EventReminder = "event_reminder"`.
- `modules/notifications/pages/notifications/notifications.component.ts`: type meta entry (icon e.g. `bi-calendar-event`, CTA "View event").
- `shared/common-components/notification-bell/`: icon for the type; click → mark read + navigate to `url`.
- No model change under the recommended default (OQ-4 would add `eventReminders?: number` to `NotificationCounters`).
- Karma: renders in both places; click navigates to `/calender/events?eventId=…`.

### tenants / admin / tenants-admin / 3rdparty-webservices / ai-startups-analyzer

- **No change under the recommended defaults.**
- **tenants:** only if OQ-5 picks a new flag (new `tenant_users` column → backend `Feature`, frontend `IFeatures`, admin `config.php`, `/trace-flag`).
- **admin:** only if OQ-6 makes windows admin-configurable (spa_settings UI) or OQ-8 asks for retract/notify-on-reschedule from admin's direct-DB edit in `modules/events/edit/info.php`. Enabling the cron row uses the existing generic `cron_jobs` table page (`modules/common.php:177`).
- **3rdparty-webservices:** only if OQ-1 adds email (template + `SESEmailService` method in backend; the gateway itself is generic).

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| Flags (#1) | None under default; reuses `notification_centre_enabled` + `events`. If OQ-5 → `events_notifications` or a new flag, it becomes a 3–4 repo flag change | `/trace-flag notification_centre_enabled`, `/trace-flag events` (and the chosen flag) |
| Backend API (#2) | No new routes. `GET notifications` gains one `type` value; shape unchanged. Counters unchanged unless OQ-4 | `/audit-contract` vs frontend `core/service/notifications.service.ts` + `NotificationCounters` |
| `notifications` row shape | One new type; written only by backend (admin does not write these rows) | review |
| `events_attendees` schema (shared tenant DB with admin) | Two additive nullable columns; admin inserts unaffected | deploy order: backend first |
| Tenant scoping (#5) | One deployment = one tenant; cron runs against its own DB | `/check-isolation` |
| Auth (#4), verification (#3), PowerPitch (#6) | Not touched | — |
| Socket | Payload-free `fetch-count` only | — |

## Test plan

No "guardian" skill exists in this workspace; say so in the PR where automated coverage can't be added.

- **backend:** jest above; `npm run build`; `npm run lint`. Manual on a dev tenant: create webinar / in-person seminar / 1:1 events at S = now+24h05m and now+65m; enable the cron row; watch rows appear once; run the service twice by hand; edit the date in admin and confirm re-arm; cancel and confirm silence; `EXPLAIN` the due-rows query.
- **frontend:** karma above; `npm run build`; manual bell + `/notifications`.
- **cross-repo:** flag off → nothing; tenant A only → tenant B unaffected.

## Rollout

1. **backend** — enum, columns, writer, cron service, seed (inactive). Harmless until both flags are on and the cron row is active.
2. **frontend** — type rendering. An older frontend shows the row with generic styling. [INFERRED from the existing fallback map]
3. Per tenant: `notification_centre_enabled` + `events` on → set `cron_jobs.active = 1` for `eventReminder` in admin → `PATCH saas/settings` (or restart) to re-arm.
4. Verify on the internal tenant first.

## Out of scope

- Email / WhatsApp / SMS reminders (unless OQ-1 changes this), consent (EX-20), quiet hours (EX-21).
- Changing `meeting-reminder.service.ts` or its exact-minute logic, and its IST/UTC date observation (§1) — candidate for a separate `/bug-fix`.
- Reminders for external/public attendees with no user account.
- Retracting or editing already-sent reminders.
- Securing the existing unauthenticated `notifications/cron/*` routes.

## Open questions

None. All 14 were resolved by Mahima on 2026-10-08 by accepting every recommended default:

| OQ | Decision |
|---|---|
| OQ-1 Channels | In-app only |
| OQ-2 Registrations | `attending` and not `rejected` (incl. `pending_moderation`); unpaid registrations on paid events count |
| OQ-3 Types / multi-day | Approved 1:1 bookings included in-app; multi-day events reminded before the first day only |
| OQ-4 Category / bell | Both reminders `new`, shown in the panel, not counted in `bell` (SAN-1381 Decision #3 kept) |
| OQ-5 Gate | `notification_centre_enabled` AND `events`; no new flag, `events_notifications` unchanged |
| OQ-6 Windows | Fixed 24 h and 1 h |
| OQ-7 Late registrants / runs | Registered inside the last 24 h → 1 h reminder only; a missed reminder is sent late inside its window, not dropped |
| OQ-8 Reschedule / cancel | Reschedule re-arms both reminders; nothing retracted; no separate change/cancel notice |
| OQ-9 Click target | `url` = `/calender/events?eventId={uuid}`; join link / venue in the message text |
| OQ-10 Idempotency (dev lead) | Two nullable "sent for start" columns on `events_attendees` + atomic conditional UPDATE claim |
| OQ-11 Muted users (dev lead) | Always write; hide at read time (SAN-1478 rule) |
| OQ-12 Manual trigger (dev lead) | None |
| OQ-13 Copy | §Copy table approved as written |
| OQ-14 Cadence (dev lead) | `*/5 * * * *` |

## Implementation notes (2026-10-08)

Built on branch `ai_native_setup_mahima` in `sc-saas-backend` and `sc-saas-frontend`, on top of the uncommitted SAN-1471 work. Nothing is committed. Every OQ decision above was implemented as written. Deviations and additions:

- **Registration-time check (P-3).** The 24 h rule compares `UNIX_TIMESTAMP(ea.created_at)` with `S − 24h` turned into IST epoch seconds (`TIMESTAMPDIFF(SECOND, '1970-01-01 05:30:00', S − 24h)`). The spec's form was `created_at + 330 min`. Both give the same answer when the MySQL session time zone is UTC. No connection `timezone` is configured, and `created_at` is a TIMESTAMP, so this form also works under any other session time zone.
- **Deleted users skipped.** The selection also joins `users` with `deleted_at IS NULL`, so soft-deleted accounts get no reminders.
- **Claim keeps `modified_at`.** The claim UPDATE sets `modified_at = modified_at`, so a reminder does not count as an edit of the attendee row.
- **Writer surface (P-6).** `EventReminderNotificationsService.notifyEventReminder(window, reminder)` writes one row and returns `true`/`false` (it never throws). `emitFetchCount(userIds)` emits once per distinct recipient. `EventReminderService` calls `emitFetchCount` once per run, after both windows. The writer module does not provide `UserRepository` (the recipient is the attendee's own `user_id`). A new `EventReminderWindow` enum (`'24h' | '1h'`) is in `core/constants/enum.ts`.
- **Copy details.** `{time}` uses lowercase `am`/`pm` (moment's `a`). It is formatted directly from the IST wall-clock string, without a Date or moment, so the server time zone cannot shift it. Other fallbacks:
  - a NULL `delivery_mode` is treated as online;
  - a 1:1 in-person event shows the venue;
  - an empty event title becomes "Your event".
- **Frontend.** The bell reuses `statusIcon()` (it now also returns the event icon). `/notifications` gets a `TYPE_META` entry with no fixed route, so a click opens the row's `url`. The karma specs are in new `*.event-reminder.spec.ts` files next to the SAN-1471 specs.
- **Module specs updated.** Backend: `modules/notifications`, `modules/cron`, `modules/events`. Frontend: `modules/notifications`. The cron job-name list also gained the missing `NOTIFICATIONS_PURGE` / `RETRY_JURY_NDA_EMAILS`, and the list of jobs seeded active now includes `RETRY_JURY_NDA_EMAILS`.
- **Not yet verified.** The due-rows SQL has not been run against MySQL; no local DB was available. The jest tests check the SQL's clauses and boundary operators, and emulate the conditional UPDATE's semantics for the claim tests. Still pending:
  - the manual dev-tenant run from the Test plan (rows appear once; re-arm on admin date edit; silence on cancel);
  - `EXPLAIN` of the due-rows query.

  No index was added.
- **Gates.** `/check-isolation`, `/audit-contract` and `/trace-flag` were checked inline against their agent checklists.
  - Isolation: no hardcoded host and no cross-tenant state; every query runs on this deployment's DB.
  - Contract: no route or DTO change. `GET notifications` gains one `type` value, and the frontend handles it.
  - Flags: `notification_centre_enabled`, `events` and `cron_enabled` are consumed unchanged and exist in tenants, backend `Feature` and frontend `IFeatures`.
- **Auth model.** No route was added or changed. The cron job runs in-process, with no HTTP surface.

## Linear tracking

- **Parent:** SAN-1472 (project "Enhancement", assignee Mahima Sharma, In Progress).
- **Sub-issues:** Todo, priority Low, assignee Mahima Sharma, project Enhancement, parent SAN-1472, labelled `Feature` + repo badge. Only repos that need changes under the recommended defaults; add tenants/admin sub-issues later only if OQ-5/OQ-6/OQ-8 require them.

| Repo | Issue | Notes |
|---|---|---|
| backend | SAN-1829 | — |
| frontend | SAN-1830 | blocked by SAN-1829 |
