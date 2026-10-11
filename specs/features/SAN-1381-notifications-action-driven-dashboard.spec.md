---
id: SAN-1381                    # renamed from NOTIF-001 on 2026-10-08 (SAN-1390); file renamed to match
aliases: [NOTIF-001]            # older specs and code comments still cite NOTIF-001
title: Notifications and an Action-Driven Dashboard (Phase 1 — counters, bell, catch-up, admin command centre)
type: feature
status: done                    # Code complete and docs updated 2026-10-08 (SAN-1467). Approved by vishali.k 2026-10-01; BRD §18 sign-off recorded 2026-10-08 (SAN-1390). Rollout (SAN-1466), QA (SAN-1458/1459/1462/1464) and baselines (SAN-1465) are still open: see specs/gap-register.md G-001…G-008.
linear: https://linear.app/sanchiconnect/issue/SAN-1381 (milestone "Notifications and an Action-Driven Dashboard", project Enhancement)
owner: vishali.k@sanchiconnect.com
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1 (1 Oct 2026), business owner Dr. Sunil Shekhawat"
repos: [tenants, backend, frontend, admin]   # dependency order
contracts:
  api:
    - "GET   api/v1/notifications/counters                 (backend, NEW — one batched call: per-section counters + bell total + catch-up summary)"
    - "POST  api/v1/notifications/sections/{section}/visit (backend, NEW — records a qualifying 3-second visit; sets last_seen_at)"
    - "POST  api/v1/notifications/item-views               (backend, NEW — {item_type, item_uuid}; mode-B 'opened' for challenges/programs/events)"
    - "PATCH api/v1/notifications/{uuid}/read              (backend, NEW — per-item read)"
    - "PATCH api/v1/notifications/mark-all-read            (backend, EXISTING — semantics narrowed: new-since-last-visit items only)"
    - "GET   api/v1/notifications                          (backend, EXISTING — response items gain read_at, actioned_at, category, group; additive)"
    - "PATCH api/v1/jobs/applications/{uuid}/viewed        (backend, NEW — marks a job application opened by the poster's team)"
    - "GET   api/v1/notifications/count                    (backend, EXISTING — UNCHANGED, kept for back-compat; frontend migrates to /counters)"
  flags:
    - notification_centre_enabled   # NEW tenant flag (tenants → backend Feature enum → frontend IFeatures → admin config.php)
  events:
    - "socket 'fetch-count' (EXISTING, reused) — emitted on every source-status change that moves a counter"
tenant_scoped: true
depends_on: []
created: 2026-10-01
---

# Notifications and an Action-Driven Dashboard — Phase 1

## Reference

This spec comes from the BRD **"Notifications and an Action-Driven Dashboard for SanchiAPP" v1.1**, dated 1 Oct 2026, owned by Dr. Sunil Shekhawat. It includes wireframes W-01 to W-12. There is no Linear issue yet.

This spec covers **BRD Phase 1 only** (BRD §14):
- FR-U1 to FR-U5
- FR-A1 to FR-A5
- EX-01 (catch-up card)
- EX-08 (empty states)
- EX-10 basic (admin command centre with counts and oldest age)

Phases 2 and 3 are listed under *Out of scope* as follow-up specs.

Every code claim below was checked against the live repos while this spec was written. Tags follow `specs/spec-authoring-practices.md`:
- **[EV]** evidenced, with a path
- **[INFERRED]** a reasonable conclusion that needs checking
- **[NOT SPECIFIED]** nothing in the source says either way
- **[DESIGN DECISION PENDING]** needs a decision from the product owner or dev lead

## Problem

Today a user sees the same dashboard whether or not anything has changed. Pending connection requests, new wall posts, live opportunities and new job applicants go unnoticed. Admin queues (outreach approvals, applicants, tasks, tickets) age with no visible backlog.

The BRD asks for three counter types, kept strictly apart:

| Type | Badge | Behaviour | In bell? |
|---|---|---|---|
| Action required | red | Stays until you act | yes |
| New since last visit | orange | Clears after a qualifying visit | yes |
| Live | outlined | Running count of what is open now | no |

> **Admin bell amendment (2026-10-06, product decision by Mahima):** clicking a queue in the *admin* bell marks it read for that admin. Each red queue gets a per-admin `admin_section_last_seen` row (`bell_outreach`, `bell_ecosystem`, `bell_tasks`, `bell_support`); from then on the bell counts only that queue's pending items created after the click. Orange sections (`engagements`) clear immediately instead of after the 3-second visit. Sidebar badges, list pages and the command centre are unchanged and still show the full pending totals, so red items there still stay until acted on. An admin who has never clicked a queue sees its full count. Implemented in `sc-saas-admin/includes/notification_centre_functions.php` (`bell_count`) and `themes/default/html/elements/header.php`.

> **Engagements amendment (2026-10-06, product decision by Mahima):** Engagements is no longer an orange "new since your last visit" counter. It is a red action queue: meetings waiting on admin moderation (`moderation_exists = 1`, `moderation_status = 'pending'`). A meeting stays in the count until an admin accepts or rejects it; visiting the meetings page no longer clears it, and the 3-second visit timer no longer runs there. Mentorship requests are left out, because the mentor approves them, not an admin. The bell follows the other red queues: clicking it writes a `bell_engagements` row, and from then on the bell counts only pending meetings created after the click. Implemented in `sc-saas-admin/includes/notification_centre_functions.php` and `themes/default/html/elements/footer.php`.

It also asks for a bell with a notification centre, a catch-up card, and an admin command centre.

## Current state (what already exists — reuse, don't reinvent)

### Backend (`sc-saas-backend/src/`)

**Notifications module** [EV `modules/notifications/`]
- Table `notifications` (`entities/notification.entity.ts`) has:
  - `from_user_id`, `to_user_id`
  - `type`, an enum of `platform_message | connection_request | connection_action | startup_suggestion | investor_suggestion`
  - `send_to`, an enum of `all | user`
  - `has_read`, `object_uuid`, `url`, `title`, `message`
- It has **no** `read_at`, `actioned_at` or category column.
- There is **no** per-item read; only `PATCH mark-all-read` exists.
- `send_to=all` rows share one `has_read` flag. A broadcast read by one user is therefore "read" for everyone.
- The list query has an unbracketed `.andWhere(to_user).orWhere(send_to=all)` bug, already recorded in the module spec.

**Badge aggregate** [EV `notifications.service.ts → getNotificationCount()`, `types/notification.type.ts`]
- Already returns `pendingConnectionCount`, `sentConnectionCount`, `unreadNotificationCount`, `unreadMessageCount`, `pendingAcceptanceMeetingCount`, `pendingProgramFormSubmissionCount`, and others.
- It is reused by `GET dashboards/user`.
- It is derived from source statuses, which is already the shape NFR-03 requires.

**Real-time** [EV `core/sockets/gateways/sockets.gateway.ts`]
- `FetchCountGateway` exposes `emitFetchCountToRoom(userId)` and `emitNotification`.
- Connections emit `connection_requested` and `connection_accepted`.
- ⚠ The gateway has **no auth**: any client can `joinRoom` any user id. See Risks.

**Other existing pieces**
- **Activity:** `users.last_logged_in` is overwritten at login [EV `modules/auth/auth.service.ts:405`]. Nothing tracks per-section last-seen, and the previous login time is not kept.
- **Cron:** `@nestjs/schedule` through `SchedulerRegistry`. Jobs are rows in `cron_jobs` (`name, time, active`), gated by `Feature.CRON_ENABLED`, and run in Asia/Kolkata time [EV `modules/cron/cron.service.ts`]. There is no notification-purge job.
- **Event emitter:** `@nestjs/event-emitter` is not installed. Notifications are written by direct repository calls.

### Source records the counters derive from

| BRD | Source | Status / columns that exist today | Gap |
|---|---|---|---|
| FR-U1 | `connections` [EV `modules/connections/entities/connections.entity.ts`] | `other_user_id` = recipient, `connection_status` ∈ `pending_moderation, pending, accepted, rejected, blocked`, `parent_id IS NULL` for top-level rows. Withdraw = soft delete (`DELETE connections/:uuid`). Count already exists: `getConnectionTypeCounts(RECEIVED)` [EV `repositories/connections.repository.ts:902`] | none — "declined" = `rejected`, "withdrawn" = `deleted_at` |
| FR-U2 | `comm_wall_posts` [EV `modules/community-wall/entities/community-wall-posts.entity.ts`] | `status` (false = hidden), `deleted_at`, `show_to_user_types` (NULL = everyone), `is_admin_post`, `user_id`, `created_at` | **no communities/groups/membership tables**, no moderation-status column, no last-seen (see OQ-1) |
| FR-U3 challenges | `challenges` + `challenge_participants` | `challenge_status` (active/inactive), `approval_status` (approved), `dead_line` (date), `privacy_type`; participant per `startup_id` | **no persona targeting** (OQ-6); no item-view tracking |
| FR-U3 programs | `application_programs` / `programs` + `program_startup_rounds` | `status`, `test_mode_enabled`, `applications_closed`, `program_closed`, `application_start_date`, `application_closed_date`, `membership_stakeholder_type` | which program table backs the "Programs" tab (OQ-7) |
| FR-U3 events | `events` + `events_attendees` | `publish_status` ∈ `draft, published, cancelled, deleted`, `date`, `time_to`, `dates` (JSON), `time_slot_booking_allowed_usertypes` | none for counting |
| FR-U4 | `job_applications` [EV `modules/job/entities/job-application.entity.ts`] | `application_status` ∈ `pending, short-listed, rejected, in-moderation`; the team rule is in `validateJobResource` | **no new/viewed state, no opened timestamp** — add columns |
| FR-A1 | `partner_broadcast_requests` (tenant DB) and `program_promotions` (main DB, outreach) | `status` ∈ `pending, approved, rejected, sent` + `target_scope`; `approval_status` ∈ `pending, approved, rejected` | **no Submitted / Under review / Returned states** (OQ-2) |
| FR-A2 | persona tables `startups, investors, mentors, corporates, service_providers, partners, program_office_members, individuals` | `approval_status` ∈ `pending, approved, rejected, submitted, not_qualified, limited_access` (`ProfileAccountStatuses`, `core/constants/enum.ts:396`) | **no Academia persona**; Incubators = `partners.partner_type='incubator'` (OQ-3) |
| FR-A3 | `meetings`, `mentorship` | `created_at`, `meeting_module`, `moderation_status`; `mentorship.approval_status` | admin last-seen tracking |
| FR-A4 | `tasks` [EV `sc-saas-admin/modules/task_management/`] | `task_status` ∈ `open, assigned, completed, cancelled`, `assigned_to_ids` (JSON of `spa_admin_users.id`), `due_date`. The backend controller is a stub | **no team-queue concept** (OQ-5) |
| FR-A5 | `tickets` + `ticket_issue_types`; `platform_feedbacks` | `ticket_status` ∈ `open, closed` only, `severity`, `closed_at`, `reopened_at` | **no feedback/grievance split, no "awaiting user" status, no SLA or acknowledged columns** (OQ-4) |

### Frontend (`sc-saas-frontend/src/app/`)

- **Header** [EV `layouts/protected/protected-layout-header/…html` ~95–118]
  - Has only Messages and Connections icon badges.
  - There is **no bell**, and nothing renders `unreadNotificationCount`.
- **Notifications page** `/notifications` [EV `modules/notifications/pages/notifications/`]
  - Opening it marks *all* notifications read.
- **Notification state**
  - Service `core/service/notifications.service.ts`.
  - NgRx `core/state/notifications/` (`SetNotificationsCount`, `getNotificationsCount`).
- **Polling** [EV `app.component.ts` ~548–561]
  - Polls `notifications/count` every 30 s with `setInterval`.
  - It is **not visibility-aware**.
  - The socket `fetch-count` event also triggers a refresh [EV `app.component.ts:361`].
- **Nav menu** [EV `shared/constants/navMenus.ts`]
  - Items are filtered by `featureKey` and rendered in `layouts/public/public-layout-sidebar/`.
  - Badges are hard-coded by `item.id` (`engage`, `programs`, `calender`, `growth-metrics`).
- **Dashboard** [EV `modules/dashboard-v2/`]
  - `dashboard-v2` is only shown when `features.new_dashboard_layout` is on.
  - Legacy per-role dashboards have their own `countBoxes` (`modules/calender/helpers.ts` ~116).
- **Visibility timer:** no foreground "visit" timer exists anywhere. The only `visibilitychange` uses are autosave handlers.
- **Notification settings** `/account/edit/notification`: email/whatsapp toggles over `users.notification_settings` JSON. This is Phase 2's foundation (W-07).

### Admin (`sc-saas-admin/`)

- **Badge pattern to copy** [EV `modules/common.php:637–694`; `themes/default/html/elements/header.php` ~230–300]
  - "Quick Links" red badges are live `COUNT(*)` queries in `common.php`.
  - `pendingSpokeBroadcastCount` counts `partner_broadcast_requests` with `status='pending' AND target_scope='hub'`, gated by `can_broadcast_messages`.
  - `pendingPromotionsCount` counts main-DB `program_promotions`.
- **No admin bell** and no admin notification table.
- **Menus** come from `spa_menu_management` and are built by `getMenus()` [EV `includes/core_functions.php:2073`].
  - They are role-filtered through `spa_admin_roles.menus`.
  - Admin (non-partner) menus are **not** flag-gated.
- **Dashboard** [EV `modules/index.php`, `includes/counter_generator.php`]
  - Uses config-driven `spa_dashboard_counters`.
- **Permissions:** `spa_admin_users` has `can_accept_reject_profiles`, `profiles_access`, `can_broadcast_messages`, and others; roles are in `spa_admin_roles`.
- **No cron in admin.** Scheduled work lives in backend `modules/cron/`.

### Tenants (`sanchiconnect-saas-tenants/`)

- **Flags** are boolean columns on `TenantUsersEntity` (~234 of them).
  - Existing notification-ish flags: `events_notifications`, `call_for_applications_submitted_email_enabled`.
  - None of them gate a notification centre.
- **No timezone column and no SLA columns** exist on `tenant_users`.
- Per-tenant key/value config lives in the tenant-DB `spa_settings` [EV `src/modules/global/admin/spa_settings.entity.ts`, seeded at `admin.repository.ts:55`].
  - It already holds `timezone` (default `Asia/Kolkata`).
  - This is the natural home for SLA values and counter modes.

## Decisions taken in this spec (author, with rationale — reviewer may overturn)

1. **Phase 1 only.** Phase 2 and 3 items each get their own spec once Phase 1 lands. The BRD itself phases them (§14), and Phase 2 needs a consent/preferences data model that has not been designed yet.
2. **One new tenant flag, `notification_centre_enabled`**, default `false`.
   - It gates the new endpoints, frontend bell and badges, and admin bell and command centre for both audiences.
   - The flag lets us ship it dark and enable it per tenant, which is how every cross-repo feature here rolls out.
3. **Action-required and live counts derive from source status every time, and are never stored as tallies** (NFR-03).
   - The `notifications` table holds the bell's *list items* and read state only.
   - The badge number never comes from counting `notifications` rows, except for "personal activity" items, which are Phase 2.
4. **The counter service lives in the existing backend `notifications` module**, not a new module.
   - The BRD's NFR-12 says "low-code platform"; here that means one shared NestJS service reused by all sections.
   - `getNotificationCount()` is extended, not duplicated.
5. **Keep `GET notifications/count` unchanged.** Add `GET notifications/counters` beside it.
   - The existing response is used by the dashboard tiles and three other call sites.
   - Changing its shape would break deployed frontends during a staggered deploy.
6. **New tenant-DB tables** are owned by backend TypeORM entities and migrations, the same as `partner_broadcast_requests`:
   - `notification_section_last_seen` (`user_id`, `section`, `last_seen_at`, unique (`user_id`, `section`)). Used for user sections.
   - `admin_section_last_seen` (`admin_user_id`, `section`, `last_seen_at`). Used for admin sections (FR-A2 auto-approve mode, FR-A3).
   - `notification_item_views` (`user_id`, `item_type`, `item_id`, `first_viewed_at`, unique (`user_id`, `item_type`, `item_id`)). Used for mode B.
   - These match BRD §13 "Section last-seen" and "Item view".
   - There is no `tenant` column, because the backend runs one deployment per tenant (invariant #5).
7. **Job application opened state:** add `job_applications.viewed_at` (nullable datetime) and `viewed_by_user_id`.
   - "New" = `viewed_at IS NULL AND application_status = 'pending'`.
   - Any team member who passes `validateJobResource` sets it.
   - Status changes to `short-listed` or `rejected` also clear it, because the status is no longer `pending`.
   - Applications `in-moderation` are not counted, since the poster can't act on them yet [INFERRED].
8. **Catch-up card "since" time:** add `users.previous_logged_in`, copied from `last_logged_in` at login before it is overwritten.
   - Without this, "since your last login" is always "since a second ago".
9. **First-login baseline** (FR-U2): if there is no `notification_section_last_seen` row, the baseline is `users.created_at`.
10. **Notifications table extension (additive):**
    - New columns: `read_at`, `actioned_at`, `category` (`action_required | new | system`), `source_type`, `source_id`.
    - Per-user read state for `send_to=all` rows goes in a new `notification_reads` table (`notification_id`, `user_id`, `read_at`).
    - `has_read` stays and is written alongside the new columns for back-compat.
    - Fix the unbracketed `orWhere` bug in the same change.
11. **90-day history:** add a new cron row `notifications_purge` to `cron_jobs`, seeded `active=false`.
    - It soft-deletes `notifications` older than 90 days.
    - This follows the existing cron pattern.
12. **Polling:** keep the existing 30 s poll, which beats the BRD's 60 s, but pause it while `document.hidden`.
    - The existing socket `fetch-count` push is the real-time path.
    - Emit `fetch-count` from every service whose status change moves a counter. Today only connections and chat emit it.
13. **Mode A/B (D1)**
    - `spa_settings` key `notif_opportunity_counter_mode` ∈ `A | B`, default `B`.
    - SLA values (D8) also go in `spa_settings`:
      - `sla_outreach_decision_hours` = 48
      - `sla_grievance_ack_hours` = 24
      - `sla_grievance_resolve_days` = 7
    - Engagement types (D7) go in key `notif_engagement_types`, default `meeting,mentor_session`.
    - [INFERRED] The backend can read tenant-DB `spa_settings` directly. Admin already does, through PHP constants. Confirm the backend path during implementation.
14. **Admin counters stay in PHP**, as live `COUNT(*)` queries like `pendingSpokeBroadcastCount`. Admin does not call the backend for counts.
    - The admin app already reads the tenant DB directly. A backend hop would add a cURL call to every admin page load.
    - Admin counter SQL and backend definitions must agree. Both reference the same status lists, documented in §Counter definitions.
15. **Timezone:** compare deadlines and "closes in" in `spa_settings.timezone` (default `Asia/Kolkata`). Store in UTC (NFR-07).

## Counter definitions (the single source of truth for both backend and admin)

### User side (backend `GET notifications/counters`)

**`connections`** (FR-U1) — red
- Counts: `connections` where `other_user_id = me`, `connection_status = 'pending'`, `parent_id IS NULL`, `deleted_at IS NULL`, and the sender is active.
- Reuses `getConnectionTypeCounts(RECEIVED)`.

**`community_wall`** (FR-U2) — orange
- Counts: `comm_wall_posts` where `status = 1`, `deleted_at IS NULL`, `user_id ≠ me`, `show_to_user_types` is NULL or contains my type, and `created_at > last_seen(community_wall)`.
- The baseline is `users.created_at` when there is no last-seen row.
- Scope is subject to OQ-1.

**`opportunities`** (FR-U3)
- Split into `{challenges, programs, events}`. The sum equals the tab badge.
- **Mode B (orange, in bell):** live + eligible + not in `notification_item_views` + not applied or registered.
- **Mode A (outlined, not in bell):** live + eligible.
- "Live" means:
  - Challenges: `challenge_status='active'`, `approval_status='approved'`, and `dead_line ≥ today` in tenant timezone.
  - Programs: `status=1`, `test_mode_enabled=0`, `applications_closed=0`, `program_closed=0`, and now between start and close.
  - Events: `publish_status='published'`, not cancelled, and end ≥ now.
- Also returns `closing_soon[]`: items closing within 72 h that I have not applied to.

**`jobs`** (FR-U4) — red
- Counts: `job_applications` on jobs owned by any member of my team, where `application_status='pending'` and `viewed_at IS NULL`.
- Returns a per-job breakdown.
- Closing a job does not clear it.

**`bell`**
- = connections + community_wall + jobs + (opportunities if mode B).
- Live counts are excluded.

**`catch_up`**
- Counts since `previous_logged_in`.
- `null` when everything is 0, which signals the EX-08 empty state.

### Admin side (PHP, `sc-saas-admin/modules/common.php`)

Each counter is visible only when the admin has the permission shown (NFR-06).

| Key | Type | Definition | Permission |
|---|---|---|---|
| `outreach` (FR-A1) | red | `partner_broadcast_requests status='pending' AND target_scope='hub'` + `program_promotions approval_status='pending'` for this tenant's domain. Oldest age shown; overdue when older than `sla_outreach_decision_hours`. Subject to OQ-2 | `can_broadcast_messages` / promotions |
| `ecosystem.{persona}` (FR-A2) | red | `approval_status='pending'` per enabled persona table. Sum = menu total. Personas whose tenant flag is off are hidden | `can_accept_reject_profiles` + `profiles_access` |
| `engagements` (FR-A3) | red, shared (amended 2026-10-06) | `meetings` rows with `moderation_exists = 1` and `moderation_status = 'pending'` (not soft-deleted), when `meeting` is in `notif_engagement_types` | engagement/meetings menu role |
| `tasks` (FR-A4) | red | `tasks` with `task_status IN ('open','assigned')`, `status=1`, and (`assigned_to_ids` contains me OR team-queue rule per OQ-5). Overdue = `due_date < today` | `task_management` flag + tasks menu role |
| `support.{feedback,grievance}` (FR-A5) | red | `tickets` with `ticket_status='open'`, split per OQ-4. "Awaiting user" is a grey sub-count, excluded from red | `ticket_management` flag + tickets menu role |
| `bell` | — | Sum of the above | — |

Action-required queues are shared: every permitted admin sees the same number (D5). Engagements are tracked per admin.

## Acceptance criteria

These are lifted from the BRD and made concrete. Wireframe references are in brackets.

**Connections (FR-U1) [W-03]**
- [ ] With 3 pending incoming requests, the Connections badge shows **3** in red.
- [ ] After accepting one, it shows **2** without a page refresh, through `fetch-count` or the optimistic store update.
- [ ] Opening `/connections` and leaving without acting keeps it at 3.
- [ ] Sent requests never count.
- [ ] A withdrawn (soft-deleted) request drops out.
- [ ] A deactivated sender drops out.

**Community wall (FR-U2) [W-04]**
- [ ] With 5 visible posts newer than last-seen, the wall badge shows **5**.
- [ ] 2 s on the wall leaves the badge at 5. 3 continuous foreground seconds clears it.
- [ ] Switching browser tabs pauses the timer.
- [ ] Last-seen is set to the moment the user **leaves** the wall.
- [ ] The user's own posts, hidden posts (`status=0`) and deleted posts never count.
- [ ] A post hidden before being seen drops out.
- [ ] A new user's first login shows 0 for posts created before registration.
- [ ] A "New since your last visit" divider sits above the oldest unseen post.

**Opportunities (FR-U3) [W-05]**
- [ ] Mode B: with 4 live eligible items, 1 opened (3 s on the detail page) and 1 applied, the badge shows **2**.
- [ ] Category counts add up to the tab badge.
- [ ] An item leaves the count at its close date/time in the tenant timezone.
- [ ] Items closing within 72 h and not applied to show a red "Closes in N days" marker.
- [ ] Mode A shows an outlined badge that is excluded from the bell.
- [ ] Changing `spa_settings.notif_opportunity_counter_mode` switches the mode with no deploy.
- [ ] Items the user is ineligible for never appear in their count. Eligibility is defined per OQ-6.

**Jobs (FR-U4) [W-06]**
- [ ] Two jobs with 3 and 2 unopened applications give a Jobs badge of **5**, with per-job counts of 3 and 2.
- [ ] Opening one application (any team member) reduces both counts by 1.
- [ ] Changing status to short-listed or rejected also reduces them.
- [ ] Closing a job does not clear its unopened applications.

**Bell (FR-U5) [W-01, W-02]**
- [ ] The bell shows the sum of red and orange counters. Live counts are excluded, so the bell can reach 0.
- [ ] The panel lists notifications newest first, grouped into Today and Earlier. Each item deep-links to its record.
- [ ] Accept and Decline on a connection request work inside the panel and update every badge immediately.
- [ ] "Mark all as read" clears new-since-last-visit items only. Red items stay, and the panel footer says so.
- [ ] Notifications older than 90 days are removed by `notifications_purge` once it is enabled.

**Display rules (BRD §7.2, applies to all badges)**
- [ ] No badge is shown at 0.
- [ ] Counts above 99 show as "99+".
- [ ] Every badge has an `aria-label`, e.g. "4 pending connection requests".
- [ ] Contrast meets WCAG 2.1 AA (NFR-08).
- [ ] Clicking a badge opens the list already filtered, e.g. `/connections/pending-requests`.

**Catch-up card and empty state (EX-01, EX-08) [W-01]**
- [ ] The catch-up card appears only when something changed since `previous_logged_in`. Each phrase links to its filtered list.
- [ ] The card can be dismissed for the current login.
- [ ] When every counter is 0, the dashboard shows "You're all caught up" with one suggested action.

**Admin (FR-A1 to FR-A5, EX-10 basic) [W-08 to W-12]**
- [ ] With 6 pending startups, 2 mentors and 1 investor, the Ecosystem badge shows **9** and the persona tabs show 6, 2 and 1.
- [ ] Approving a startup reduces both the Startups tab and the Ecosystem total by 1.
- [ ] Personas disabled for the tenant do not appear.
- [ ] The outreach list sorts oldest first and shows waiting time. Items past SLA are marked Overdue.
- [ ] Rejecting an outreach request requires a reason, which reuses the SAN-392 `rejection_message` flow.
- [ ] Engagements is red and shared. A meeting leaves the count only when an admin accepts or rejects its moderation request (amended 2026-10-06).
- [ ] Tasks lists overdue items first. The count drops on complete or cancel.
- [ ] Support shows separate Feedback and Grievance counts, plus a grey "awaiting user" sub-count, per OQ-4.
- [ ] The command centre lists every queue the admin may see, with its count and oldest-item age, and SLA breaches in a strip at the top.
- [ ] An admin without the queue permission sees neither the badge nor the card (NFR-06).
- [ ] Every approve, reject or resolve that clears a counter is audit-logged with user, time and reason (NFR-11). Check which actions already log before adding new logging.

**Cross-cutting**
- [ ] With `notification_centre_enabled=false`, the platform behaves exactly as today: no bell, no new badges, and new endpoints return 403 through `FeatureGuard`.
- [ ] Badge = list count in every case. Automated tests compare the counter output with the list endpoint output (NFR-03, BRD §15).
- [ ] `GET notifications/counters` responds in ≤ 300 ms p95 on the largest tenant's data volume (NFR-01).

## Per-repo plan

### tenants (`sanchiconnect-saas-tenants`)
- Add the boolean column `notification_centre_enabled` (default `false`) to `src/modules/tenants/entities/tenant-users.entity.ts`. There is no migration file: this repo uses TypeORM `synchronize: true` (`src/core/database/database.module.ts:27`). **[Done, SAN-1401]**
  - Expose it in **three** places in `global.service.ts`: the `verifyTenant` select list, the `verifyTenant` `features` map, and the `getTenantSettings` select list. **[Done, SAN-1402]**
  - This is a shape change to the tenant-verification contract (invariant #3), but it is additive.
  - Test: `src/modules/global/global.service.notification-centre-flag.spec.ts`. **[Done, SAN-1400]**
- ~~Seed the `spa_settings` keys here.~~ **Moved to admin (SAN-1491).** The tenants repo's `spa_settings` is the cockpit DB's own table. Per-tenant `spa_settings` lives in each tenant's DB; sc-saas-admin creates rows on demand with `getSetting()`/`addSetting()`, and the backend reads them through its own `AdminSettingsEntity`. Both readers fall back to the D1/D7/D8 defaults when a row is missing.
- `sanchiconnect-saas-tenants-admin` needs nothing beyond the generic engine showing the new column. Run `/trace-flag` to confirm.

### backend (`sc-saas-backend`)

**Flag**
- Add `Feature.NOTIFICATION_CENTRE_ENABLED = 'notification_centre_enabled'` to `src/core/constants/enum.ts`.

**Entities and migrations** (Decisions #6–#11)
- `NotificationSectionLastSeenEntity`
- `AdminSectionLastSeenEntity`
- `NotificationItemViewsEntity`
- `NotificationReadsEntity`
- New columns on `notifications`: `read_at`, `actioned_at`, `category`, `source_type`, `source_id`
- New columns on `job_applications`: `viewed_at`, `viewed_by_user_id`
- New column on `users`: `previous_logged_in`

**`modules/notifications/`**
- `NotificationCountersService.getCounters(user)` implements §Counter definitions (user side).
  - Run the queries in parallel (`Promise.all`).
  - Reuse the existing repository methods for connections and meetings.
- Add the new controller routes listed in frontmatter `contracts.api`.
  - Guard each with `JwtAuthGuard` + `FeatureGuard` + `@Features(Feature.NOTIFICATION_CENTRE_ENABLED)` **per method**, because the guard ignores class-level metadata.
- Accept these section enums in `POST sections/{section}/visit`, rejecting anything else:
  - User: `community_wall`, `opportunities`
  - Admin: `engagements`, `ecosystem_{persona}`
- Narrow `mark-all-read` to `category='new'`, and write `notification_reads` for `send_to=all` rows.
- Fix the unbracketed `orWhere` in the list query.

**`modules/auth/auth.service.ts:405`**
- Copy `last_logged_in` → `previous_logged_in` before overwriting it.

**`modules/job/`**
- Add `PATCH applications/{uuid}/viewed`, protected by the same `validateJobResource` team check.
- Set `viewed_at` automatically when the poster fetches application detail.

**`fetch-count` emission**
- Call `emitFetchCountToRoom` on each counter-moving status change:
  - job application create and status change → poster's team
  - community post create → **not** per user (the poll covers it; fan-out to all users is too expensive) [INFERRED]
  - challenge, program and event publish → none (poll)
  - connection actions → already emitted

**`modules/cron/`**
- Add a `NOTIFICATIONS_PURGE` `CronJobName` and service, plus a `cron_jobs` seed row with `active=false`.

### frontend (`sc-saas-frontend`)

**Feature flag and data plumbing**
- Add `notification_centre_enabled: boolean` to `IFeatures` in `core/domain/brand.model.ts`.
- Add new methods to `core/service/notifications.service.ts`: `getCounters()`, `recordSectionVisit()`, `recordItemView()`, `markRead()`.
- Add a new `counters` slice to NgRx `core/state/notifications/`.

**Polling** (`app.component.ts` ~548)
- When the flag is on, poll `counters` instead of `count`.
- Pause the poll while `document.hidden`, and refresh on `visibilitychange` to visible.

**Visit timers**
- New `QualifyingVisitService`: a 3-continuous-second foreground timer driven by `visibilitychange`. Shared by the wall, opportunity detail pages, and job application detail.
  - It posts the visit on route leave, sending `left_at`.
  - It falls back to `navigator.sendBeacon` on unload.

**Header bell** (`layouts/protected/protected-layout-header/`)
- New bell component with a panel: tabs All / Needs action, Today / Earlier grouping, inline Accept/Decline (reusing `connections.service.ts` accept/reject), Mark all as read, and a footer note.
- The existing `/notifications` page remains as "view all".
  - Stop it from auto-marking all as read when the flag is on.

**Nav badges** (`shared/constants/navMenus.ts`, `public-layout-sidebar`)
- Add an optional `badgeKey` and `badgeType` to `INavMenuItem`.
- Replace the hard-coded `item.id` badge checks with one generic badge renderer:
  - colour by type
  - hide at 0
  - 99+ cap
  - `aria-label`
- Links:
  - `community-feed` → `community_wall`
  - challenges, programs and events nav ids → `opportunities.*`
  - `post-job` → `jobs`
  - `my-network` → `connections`

**Pages**
- `modules/community-feed/`: "New since your last visit" divider.
- Challenge, program and event list pages: orange unseen dot, red "Closes in N days" chip, category tab counts, and a "Applied" tag.
- `modules/hire/` and `modules/job-details/`: per-job red count, and a "New" / "Viewed" status label.

**Dashboard**
- Add a `catch-up-card` and `all-caught-up` empty state to `modules/dashboard-v2/`. The legacy dashboards depend on OQ-8.

### admin (`sc-saas-admin`)

**Flag constant**
- Add a `notification_centre_enabled` constant in `config/config.php`, following the brand-settings pattern.

**Counters** (`modules/common.php`, beside `pendingSpokeBroadcastCount`, ~660)
- Compute the admin counters from §Counter definitions, permission-gated, and only when the flag is on.
  - One function, `getAdminNotificationCounters($database, $mainDatabase, $admin)`, in `includes/`.
- Write `admin_section_last_seen` on qualifying visits through a small JS timer plus a POST to a new admin endpoint, `modules/notifications/visit.php`.
  - The endpoint needs a session check and a CSRF token, matching the existing admin AJAX endpoints.

**Header** (`themes/default/html/elements/header.php`)
- Add an admin bell next to Quick Links showing the sum and a dropdown of queues.
- Add sidebar menu badges by menu `table_name` or url, matching how `getMenus()` identifies items.

**Command centre**
- New `modules/command_centre.php` with a template. Each queue card shows count, oldest-item age and overdue count, and links to the filtered queue. The SLA-breach strip sits on top.
- Register it as a `spa_menu_management` row through a one-off `cli/add_command_centre_menu.php`, following the `cli/add_ocr_claims_sidebar_menu.php` precedent.

**Queue pages**
- Outreach (`modules/outreach_requests/list.php`) and approvals (`modules/broadcast_messages/approvals.php`): oldest-first sort, waiting-time column, Overdue chip.
- Ecosystem persona lists: a "Pending review" filter applied on badge landing.
- `modules/task_management/list.php`: overdue first.
- `modules/tickets/list.php`: Feedback / Grievance tabs and SLA columns, per OQ-4.

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| Flag `notification_centre_enabled` | New in tenants. Propagates to backend `Feature`, frontend `IFeatures`, admin `config.php` | `/trace-flag notification_centre_enabled` |
| Tenant-verification payload | Additive feature key | `/audit-contract` (tenants → frontend `brand.model.ts`) |
| Backend API | 5 new routes, `mark-all-read` semantics narrowed, `GET notifications` gains additive fields; `GET notifications/count` unchanged | `/audit-contract` against `core/service/notifications.service.ts` and admin cURL callers (none call notifications today [EV]) |
| Tenant-DB schema | New tables and columns created by backend migrations and read directly by admin PHP. Admin must not deploy reads before backend migrations run | Rollout ordering |
| Tenant scoping (invariant #5) | Backend: per-deployment, no cross-tenant reads. Admin: `$database` per `admin_domain`; main-DB `program_promotions` filtered by this tenant's domain, as the existing `pendingPromotionsCount` does | `/check-isolation` |
| Auth (invariant #4) | No change to the JWT model. New routes use the existing `JwtAuthGuard`. The socket gateway is unauthenticated and pre-existing, so it is not widened — see Risks | — |

## Test plan

- **Workspace-wide limitation:** there is no "guardian" test skill yet. Where automated coverage cannot be added, say so in the PR.
- **tenants:** migration runs up and down; the flag appears in `verify_tenant` output; `npm run build`.
- **backend:**
  - Jest unit tests for `NotificationCountersService`, one per counter, built from the BRD acceptance numbers (3 → 2, 5 posts, 4 − 1 − 1 = 2, 3 + 2 = 5, and so on).
  - A badge-equals-list test per counter.
  - `FeatureGuard` returns 403 when the flag is off.
  - `npm run build` and lint.
  - Measure `EXPLAIN` and timing for `counters` on a copy of the largest tenant DB (NFR-01).
- **frontend:**
  - Karma tests for `QualifyingVisitService`: a 2 s visit does not count, 3 s does, a hidden tab pauses the timer.
  - Badge component tests: hidden at 0, 99+ cap, `aria-label`.
  - `ng build --prod`.
  - Manual walk-through of W-01 to W-06 with sample data matching the BRD's bell total (21).
- **admin:** `php -l` on every touched file; manual walk-through of W-08 to W-12 with sample data matching the BRD's admin bell (27); an admin without permission sees no badge.
- **cross-repo:**
  - Flag off: no visible change anywhere.
  - Flag on in one dev tenant: user accepts a request → the badge drops in real time; admin approves a startup → admin badge drops.
  - Second tenant: counts stay independent.

## Performance measurements (NFR-01, SAN-1464, 2026-10-08)

**How it was measured:**
- Suite: `sc-saas-backend/src/modules/notifications/notification-counters.perf.integration.spec.ts`. It is opt-in: `NOTIF_PERF_DB=mysql://…/<db>_test npx jest notification-counters.perf --runInBand`.
- Environment: local MySQL 26.7 (Homebrew), Apple-silicon Mac, single connection.
- Calls: the real `NotificationCountersService.getCounters`, timed for 200 startup users after one warm-up call.
- Data: a synthetic tenant, because there was no copy of the largest real tenant. Sizes are 20k startups, 100k users, 300k wall posts, 300k connections, 2k challenges, 1k programs, 3k events, 200k item views, 20k jobs, 200k job applications and 500k notifications.

| Measure | Result | Budget |
|---|---|---|
| `getCounters` p50 / p95 / max | 128.7 / **133.6** / 137 ms (second run 129 / 134 / 156) | p95 ≤ 300 ms, **met** |
| Slowest statement: wall count (`countWallPostsSince`, ×2 per call: badge + catch-up) | 119 ms p95, `ALL` (full scan, ~300k rows) | — |
| Wall count with an index on `comm_wall_posts(created_at)` (test DB only) | 28 ms p95, `range` (~2.9k rows); `getCounters` p95 → 123 ms | — |
| Every other statement | ≤ 7 ms; indexed (`ref` / `eq_ref`) or a few-thousand-row scan of challenges / programs / events | — |

- **Dashboard-load overhead (flag on vs off):** not measured. It needs a browser run against the deployed app.
- **Recommendation for SAN-1426:** add an index on `comm_wall_posts(created_at)`. The wall count is the only full scan and it grows with post volume, but it fits the budget without the index at this size. It was not added to the entity, because `synchronize: true` would ALTER the live table at boot. Add it in a planned window, and run `EXPLAIN` on the real largest tenant.

## Rollout

1. **tenants:** deploy the flag column (default off) and seed the `spa_settings` keys.
2. **backend:** deploy migrations (additive only: new tables and nullable columns), the new routes behind the flag, and the `previous_logged_in` write. The purge cron is seeded inactive.
3. **frontend:** deploy the bell, badges and timers behind `features.notification_centre_enabled`. Old builds keep using `/count`, which is unchanged.
4. **admin:** deploy the counters, bell and command centre behind the flag. Run `cli/add_command_centre_menu.php` per tenant.
5. Enable the flag on one internal tenant and run the cross-repo smoke test.
6. Capture the 30-day baselines for BRD §4 metrics **before** enabling for client tenants. The BRD requires baselines in the 30 days before release.
7. Enable per tenant, then activate `notifications_purge` in `cron_jobs`.

## Risks

- **Unauthenticated socket gateway (pre-existing).**
  - Any client can `joinRoom` any user id and receive that user's `emitNotification` payloads.
  - This feature adds more `fetch-count` emits, which carry no payload, and no new payload-bearing emits. It therefore does not make the leak worse.
  - It should still be fixed before Phase 2 personal-activity pushes. See OQ-9.
- **Counter query cost.** Up to about 8 count queries run per poll per user.
  - Mitigations: one batched endpoint, parallel queries, index review on the columns below, and a 30 s poll paused when the tab is hidden.
  - Columns to index: `comm_wall_posts.created_at`, `job_applications(job_id, viewed_at)`, `connections(other_user_id, connection_status)`.
  - If p95 > 300 ms, add a short per-user cache invalidated on `fetch-count` (NFR-04).
- **Admin SQL and backend definitions drifting apart.** §Counter definitions is the single reference. Any change to a status enum must update both.
- **`mark-all-read` semantics change** affects the existing `/notifications` page. It only applies when the flag is on.

## Out of scope (follow-up specs)

- **BRD Phase 2:**
  - EX-02 Next actions
  - EX-03 Personal activity
  - EX-04 Application status updates
  - EX-05 Event reminders
  - EX-06 Profile completeness with reasons
  - EX-10 full (SLA colouring and trends)
  - EX-11 Escalation
  - EX-12 Admin digest
  - EX-17 "What you missed" email
  - EX-19 Preferences
  - EX-20 DPDP consent records
  - EX-21 Quiet hours
- **BRD Phase 3:**
  - EX-07 Recommendations
  - EX-09 Profile views
  - EX-13 Ecosystem pulse
  - EX-14 Program health
  - EX-15 Bulk actions
  - EX-16 Notification analytics
  - EX-18 Push and WhatsApp
- Excluded by the BRD: the SMS channel, AI summaries, and module redesign beyond the status fields the counters need.
- Fixing the pre-existing outreach (`program_promotions`) cross-tenant authorization gap in admin. Track it separately.
- Mobile push infrastructure. No FCM or web-push exists today; `users.push_token` is unused.

## Resolved design decisions (T0, 2026-10-01)

These were answered by the document owner (vishali.k@sanchiconnect.com) on 2026-10-01. Each one is tracked in Linear under SAN-1381.

| OQ | Decision | Linear | Effect on the plan |
|---|---|---|---|
| OQ-1 Wall scope (D2) | Count **all posts visible to the user**: `status=1`, `deleted_at IS NULL`, `show_to_user_types` match, user's own posts excluded. `is_admin_post=1` is treated as a tenant-wide announcement. No communities model in Phase 1. | SAN-1391 | Unblocks T3.2 / T4.9 |
| OQ-2 Outreach | "Broadcast/Outreach" counts **both** `partner_broadcast_requests` (`status='pending' AND target_scope='hub'`) and `program_promotions` (`approval_status='pending'`, this tenant's domain). **No new statuses:** Under review and Returned are not built in Phase 1, and the "Return" action from W-09 is deferred. | SAN-1392 | Unblocks T5.4; T2.9 is cancelled for the outreach part |
| OQ-3 Personas (D4) | Use **existing personas only**: Startups, Investors, Mentors, Corporates, Service providers, Partners (incubators and accelerators sit inside Partners), Program office, Individuals. **Academia is dropped.** Auto-approval is per persona, not per tenant. Program-office members are auto-approved at registration (`sc-saas-backend/src/modules/auth/auth.service.ts:1500`), so that tab uses orange "new since this admin's last visit". Every other persona defaults to `approval_status='pending'` and uses red. [INFERRED from code — verify during T5.5 that no other persona is auto-approved for any tenant.] | SAN-1393 | Unblocks T5.5 |
| OQ-4 Support (D6, D8) | Add **new ticket columns**: `ticket_category` ENUM('feedback','grievance'), an `awaiting_user` status, `acknowledged_at`, `acknowledged_by_id`, and an **Acknowledge** action. The `platform_feedbacks` ratings widget is **not** counted. | SAN-1394 | Confirms T2.8; unblocks T5.8 |
| OQ-5 Tasks (D5) | "In progress" = `task_status='assigned'`. The team queue = tasks with an empty `assigned_to_ids`, visible to every admin with the Tasks menu. Any of those admins can click "Assign to me". No schema change. | SAN-1395 | Unblocks T5.7; T2.9 is cancelled for the tasks part |
| OQ-6/7 Eligibility | **Challenges:** startups only. **Programs:** `application_programs` (call for applications) only, filtered by `membership_stakeholder_type` and the `approved_startups_can_apply_on_programs` rule. **Events:** `time_slot_booking_allowed_usertypes` (NULL = everyone). The `programs` and `vs_programs` tables are excluded from the count. | SAN-1396 | Unblocks T3.3 / T4.10 |
| OQ-8 / OQ-10 Placement | The catch-up card and "all caught up" state appear on **dashboard-v2 only** (tenants with `new_dashboard_layout`). Admin badges go on the **existing `spa_menu_management` rows**; the W-08 menu grouping is not added. | SAN-1397 | Unblocks T4.12, T4.13, T5.3 |
| OQ-9 Socket auth | Out of scope for this milestone. It is tracked as a **separate security issue** that must land before Phase 2 payload-bearing pushes (EX-03). Phase 1 only adds payload-free `fetch-count` emits. | SAN-1398 → new issue | Recorded in Risks |
| OQ-11 Linear | Assignee: Vishali, for the whole milestone. Project: Enhancement; milestone: Notifications and an Action-Driven Dashboard. | SAN-1381 | Done |

## Open questions

None. All design questions are resolved (see above).

**BRD v1.1 sign-off (§18), recorded 2026-10-08 for T0.1 (SAN-1390):**

| Role | Name | Sign-off | Recorded by |
|---|---|---|---|
| Business owner | Dr. Sunil Shekhawat | Confirmed by Mahima Sharma, 2026-10-08 | Mahima Sharma |
| Product/UX lead | not recorded | Confirmed by Mahima Sharma, 2026-10-08 | Mahima Sharma |
| Engineering lead | not recorded | Confirmed by Mahima Sharma, 2026-10-08 | Mahima Sharma |
| QA lead | not recorded | Confirmed by Mahima Sharma, 2026-10-08 | Mahima Sharma |

Mahima confirmed the sign-off; the signatories' names for the three lead roles were not supplied and should be filled in if a formal record is needed. The business owner is from the BRD cover (`source:` above).
