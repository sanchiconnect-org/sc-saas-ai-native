---
id: SAN-1478
title: "Notifications Phase 2 — EX-19 Notification preferences (this phase: In-app channel toggle per category)"
type: feature
status: in-review                 # approved by Mahima 2026-10-06 ('we have to add this turn off and on feature'); implemented 2026-10-06 on ai_native_setup_mahima (backend SAN-1741, frontend SAN-1742 — both In Review, uncommitted)
linear: https://linear.app/sanchiconnect/issue/SAN-1478/notifications-p2-ex-19-notification-preferences-category-channel   # parent issue (project "Enhancement"); sub-issues SAN-1741 (backend), SAN-1742 (frontend)
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-19 (W-07), Phase 2. Scope narrowed by Mahima 2026-10-06 to the In-app column only."
repos: [backend, frontend]        # dependency order. admin unaffected (D-5)
contracts:
  api:
    - "PATCH api/v1/users/profile/notification-settings   (backend, EXISTING, JwtAuthGuard — NotificationSettingsDto gains OPTIONAL `inApp` object; storage changes from replace to merge (A-2))"
    - "GET   api/v1/users/profile (and every response that returns the user) (EXISTING — `notificationSettings` JSON may now carry `inApp`; additive)"
    - "GET   api/v1/notifications                         (backend, EXISTING — with notification_centre_enabled ON, rows of muted categories are excluded in SQL (A-4); shape UNCHANGED)"
    - "GET   api/v1/notifications/counters                (backend, EXISTING — `bell` excludes muted categories; `catchUp` terms of muted categories are 0 (null when all 0); additive field `inAppMuted: string[]` (A-5))"
    - "No NEW routes"
  flags:
    - notification_centre_enabled   # EXISTING. Reused, no new flag. Gates the Notification Settings nav tab (D-2, done), the In-app table (D-2) and all backend filtering (A-6)
  events:
    - "socket per-type toast events (EXISTING `connection_requested`, `connection_accepted`) — backend skips emitNotification() to a recipient who muted the category; `fetch-count` is still emitted (A-7)"
    - "users.notification_settings JSON — additive key `inApp` (missing key or missing sub-key = enabled)"
tenant_scoped: true
depends_on: [SAN-1381]           # Mahima 2026-10-06: needs SAN-1381 Phase 1 CODE merged (bell, counters, centre — present in all repos), not SAN-1381 status=done; proceed while Phase 1 Linear items close out
created: 2026-10-06
updated: 2026-10-06               # D-1..D-8 recorded from Mahima; all OQs resolved; approved
---

# Notifications Phase 2 — EX-19 Notification preferences (In-app channel)

## Reference and evidence tags

- **Source:** Linear SAN-1478 (placeholder, no comments). Verbatim: "Preferences per category, per channel and per frequency. Mandatory account and system notices cannot be muted. Existing base to extend: the frontend `/account/edit/notification` page and the `users.notification_settings` JSON (meetingRequests, fundingRequests, newChatConversation × email/whatsapp)."
- **Scope set by Mahima (2026-10-06):** build ONLY the **In-app** toggle.
  - No per-category Email/WhatsApp, and no frequency, in this phase.
  - The final category list is in D-6.
- **Evidence tags** (`specs/spec-authoring-practices.md`): **[EV]** = `file:line`; **[INFERRED]**; **[NOT SPECIFIED]**.
- **Owner decisions** are cited **(Mahima, 2026-10-06)**.

## Problem

Users cannot turn off in-app notifications by topic. The Phase 1 bell, sidebar badges, toasts and dashboard catch-up card (SAN-1381) show everything. The only preference page today controls email and WhatsApp for three hard-coded topics. EX-19 asks for per-category control; this phase delivers the In-app channel, with account and security notices always on.

## Owner decisions (Mahima, 2026-10-06)

Mahima was shown the full proposed behaviour (D-4 to D-8) and replied: "we have to add this turn off and on feature". That reply resolves every former open question with the author's recommendation.

**D-1 — Where the setting lives.**
- Users enable or disable in-app (platform) notifications **per category** on the existing `/account/edit/notification` page.
- The existing Email/WhatsApp toggles on that page **stay**.

**D-2 — Flag gating of the page and the table.**
- The "Notification Settings" tab in the account-settings top nav is shown only when `brandDetails.features.notification_centre_enabled === true`.
  - **Done (uncommitted, working tree):** `sc-saas-frontend/src/app/modules/account/pages/edit-profile/account-setting-page-top-nav/account-setting-page-top-nav.component.ts:82–90`, with `showMenu` at :88.
  - It keeps the existing exclusion of `ACCOUNT_TYPE.INDIVIDUAL` and `ACCOUNT_TYPE.JOB_SEEKER` [EV :84].
- The In-app table on the page also renders only when the flag is on.
- Note [INFERRED]: the route itself is not guarded (there is no route-level flag guard in this app, per `sc-saas-frontend/CLAUDE.md`). A user with the flag off can still open the page by direct URL; they see only the Email/WhatsApp toggles.

**D-3 — Merge on save stays, as a defensive change.**
- The identical Notification Preferences card in `edit-profile.component.html` is **commented out** (`<!--` at :474 to `-->` at :577) [EV]. So today the only UI save path is the notification-settings page.
- The backend merge-on-save change (A-2) is still made.

**D-4 (was OQ-1) — Layout.**
- A **separate "In-app notifications" table, placed below** the existing Email/WhatsApp table.
- The existing Email/WhatsApp table is unchanged, including its "Connection Requests" → `fundingRequests` binding.

**D-5 (was OQ-2) — What "in-app off" means for a category.**
- Rows are **still created**, so re-enabling restores them.
- When muted, the category is:
  - hidden from the `GET notifications` list (bell panel and `/notifications` page);
  - excluded from the bell number;
  - removed from the sidebar badge, **including the red "needs action" Connections and Jobs badges**;
  - not sent as a server toast;
  - left out of the **dashboard catch-up card**.
- The underlying page content is unaffected. For example, the Connections page still lists pending requests.
- SAN-1471 ACTION_REQUIRED items also respect muting. There is no bypass.
- **Admin is unaffected:** read-time filtering means admin-written rows are filtered too. There is no admin sub-issue.
- A user who never saved = all categories ON.

**D-6 (was OQ-3) — Categories.** The In-app table has 8 rows:

| # | Row | `inApp` key |
|---|---|---|
| 1 | Connection requests | `connectionRequests` |
| 2 | Job applications | `jobApplications` |
| 3 | Application updates (new) | `applicationUpdates` |
| 4 | Deadlines and closing soon | `deadlines` |
| 5 | Comments, mentions, reactions | `communityActivity` |
| 6 | New community posts | `communityPosts` |
| 7 | Event reminders | `eventReminders` |
| 8 | Account and security notices — always on, disabled | none (not stored) |

- "Application updates" covers SAN-1471's `cfa_application_status`, `program_application_status`, `vs_program_application_status` and `mentor_application_status`.
- `job_application_status` goes under Job applications.

**D-7 (was OQ-4) — Types with no row of their own.**
- `platform_message` → Account and security (always on).
- `startup_suggestion` / `investor_suggestion` broadcasts and chat toasts are always shown (unmapped).

**D-8 (was OQ-5) — Deadlines and closing soon.**
- Controls only the closing-soon line on the dashboard catch-up card, plus future deadline reminders.
- Closing-soon chips on CFA/challenge cards are item metadata, not notifications, and are unaffected.
- The mode-B "new opportunities" counters (challenges/programs/events) are not controlled by any toggle.

## Current state (checked against code, 2026-10-06)

### Storage and endpoint (backend)

- `users.notification_settings` is a nullable JSON column typed `any` [EV `sc-saas-backend/src/modules/user/entities/user.entity.ts:173–174`].
- `PATCH api/v1/users/profile/notification-settings`, `JwtAuthGuard`, body `NotificationSettingsDto` [EV `sc-saas-backend/src/modules/user/user.controller.ts:240–258`]. Class-level `@UseGuards(FeatureGuard)`, no `@Features` on this route [EV `user.controller.ts:62`].
- `NotificationSettingsDto` has three **required** keys `meetingRequests`, `fundingRequests`, `newChatConversation`, each `{ whatsapp, email }` [EV `sc-saas-backend/src/modules/user/dto/notification-settings.dto.ts:11–39`].
- **The service REPLACES the whole JSON**: `user.notificationSettings = notificationSettingsDto` [EV `sc-saas-backend/src/modules/user/user.service.ts:533`].
- The global `ValidationPipe({ whitelist: true })` silently strips unknown keys [EV `sc-saas-backend/src/main.ts:111`].
- The three keys are seeded when the JSON is NULL [EV `user.service.ts:219–235, 875–888`; `user/repositories/user.repository.ts:263–278, 312–327`; `auth/auth.service.ts:247–262, 660–673, 849–863`].
- `NotificationSettingsType` [EV `sc-saas-backend/src/core/types/notification-type.ts:1–10`].
- `shouldSendNotification()` / `shouldSendWhatsappNotification()` [EV `sc-saas-backend/src/core/utils/app.utils.ts:1079–1102`] serve the email/WhatsApp channels only.

### Writers of `notification_settings` outside the PATCH

- **sc-saas-admin** writes the three-key default JSON:
  - when it creates stakeholder accounts [EV `sc-saas-admin/includes/stakeholder_account_creation_funcs.php:1360` (+7 sites)];
  - on CSV import [EV `sc-saas-admin/modules/csv/import.php:543` (+7 sites)].
  - Missing `inApp` = all ON, so no change is needed.
- **Frontend:**
  - `NotificationSettingsComponent` is the only live UI save path [EV `account-routing.module.ts:37–39`; `notification-settings.component.ts:141–171`; `.html:46–97`].
  - The `EditProfileComponent` card is commented out (D-3).
  - Both use `ProfileService.updateNotification()` [EV `src/app/core/service/profile.service.ts:359–360`].
  - Model: `profile.model.ts:19–23, 56`.

### In-app surfaces (Phase 1, SAN-1381)

- **Notification rows:** `NotificationType` has 5 values [EV `sc-saas-backend/src/core/constants/enum.ts:347–353`]. Writers [EV `notifications/repositories/notifications.repository.ts:72–213`]:
  - `connection_request` / `connection_action` are per user;
  - `platform_message`, `startup_suggestion`, `investor_suggestion` are broadcasts (`send_to = all`).
- **List:** `to_user_id = me OR send_to = all`, paginated [EV `notifications.repository.ts:35–65`, bracket :48–55]. The user is loaded at [EV `notifications.service.ts:79`]; the flag check is at :95.
- **Counters** (flag-gated) [EV `notifications.controller.ts:176–178`; `notification-counters.service.ts`]:
  - every term is derived from source status, not rows (:123–185);
  - `bell` [EV :228–232];
  - `closingSoon` [EV :193–210];
  - `catchUp` [EV :234–242];
  - the user is loaded at [EV :95].
- **Dashboard catch-up card** builds its phrases from `catchUp.connections`, `catchUp.communityWall` and `catchUp.closingSoon` [EV `sc-saas-frontend/src/app/modules/dashboard-v2/components/dashboard-catch-up/dashboard-catch-up.component.ts:82–95`]. It renders only when `catchUp` is non-null and has phrases (:55).
- **Frontend bell and badges:**
  - The bell shows `counters.bell − bellBaseline` [EV `notification-bell.component.ts:66–77`].
  - Sidebar badges [EV `core/state/notifications/nav-badge.util.ts:6, 14–34, 56`].
- **Toasts:**
  - `SocketService.listenTOEvents()` [EV `src/app/core/service/socket.service.ts:39–51`].
  - Emitters: `connections.service.ts:1293–1299` (`connection_requested`) and `:2789` (`connection_accepted`); chat emitters at `chat.service.ts:574–575, 767–768` and `conversations.service.ts:183–184`.
- **Flag:**
  - backend `enum.ts:1287`;
  - `NotificationCentreService.isEnabled()` [EV `notification-centre.service.ts:78–80`];
  - frontend `brand.model.ts:216`.

### Category → in-app source (final mapping, D-5 to D-8)

| Category (`inApp` key) | Notification rows (`type`) | Counter / badge / catch-up | Toast | Effective today? |
|---|---|---|---|---|
| Connection requests (`connectionRequests`) | `connection_request`, `connection_action` | `bell` term `connections`; badge `connections`; `catchUp.connections` | `connection_requested`, `connection_accepted` | **Yes** |
| Job applications (`jobApplications`) | `job_application_status` (SAN-1471) | `bell` term `jobs.total`; badge `jobs`; SAN-1471 `statusUpdates` share | — | **Yes** for posters (counter/badge); applicant rows when SAN-1471 lands |
| Application updates (`applicationUpdates`) | `cfa_/program_/vs_program_/mentor_application_status` (SAN-1471) | SAN-1471 `statusUpdates` share | — | **No effect until SAN-1471 lands** |
| Deadlines and closing soon (`deadlines`) | — (future deadline reminders) | `catchUp.closingSoon` only (D-8) | — | **Yes** (catch-up line) |
| Comments, mentions, reactions (`communityActivity`) | — | — | — | **No effect yet** — no in-app source exists [EV grep `community-wall.service.ts`; no "mention" in backend modules] |
| New community posts (`communityPosts`) | — | `bell` term `communityWall`; badge `communityWall`; `catchUp.communityWall` | — | **Yes** |
| Event reminders (`eventReminders`) | — | — | — | **No effect yet** — no event-reminder job in `src/modules/cron/` [EV glob]; EX-05 = SAN-1472 |
| Account and security (mandatory) | `platform_message` | — | — | Always shown |
| *(unmapped, always shown)* | `startup_suggestion`, `investor_suggestion` | `opportunities.*` mode-B counters | chat toasts | Always shown |

- **Toggles with "no effect yet":** stored and shown now.
- Any future feature that produces those notifications must call `isInAppEnabled()` (A-1).

## Design (author decisions, made final by D-4 to D-8)

**A-1 — Extend the existing JSON; no new table.**
- `inApp: { connectionRequests?, jobApplications?, applicationUpdates?, deadlines?, communityActivity?, communityPosts?, eventReminders? }`, all booleans.
- A missing `inApp`, or a missing key, means ON.
- There is no key for Account and security.
- Backend artefacts:
  - an `InAppCategory` enum;
  - a `NOTIFICATION_TYPE_IN_APP_CATEGORY` map (type → category | `mandatory` | `unmapped`);
  - helpers `isInAppEnabled(settings, category)` and `mutedNotificationTypes(settings)` in `core/utils/app.utils.ts`.
- Mandatory and unmapped types are never muted.

**A-2 — PATCH merges instead of replacing.**
- Storage becomes `{ ...existing, ...dto, inApp: { ...existing?.inApp, ...dto.inApp } }`.
- It protects against:
  - older cached PWA builds;
  - the commented-out EditProfile card coming back;
  - partial callers.
- The legacy keys stay required.

**A-3 — Read-time filtering (D-5).** Rows are always written. All muting happens when reading.

**A-4 — The list filters in SQL.**
- `NotificationsRepository.getNotifications()` takes an optional `excludeTypes`.
- It adds `AND notifications.type NOT IN (:...excludeTypes)` outside the existing bracket, so pagination stays correct.
- Applied only when the flag is on.

**A-5 — Counters.**
- `bell` leaves out the muted categories' terms:
  - `connections`;
  - `communityWall`;
  - `jobs.total`;
  - SAN-1471's `statusUpdates`, counted only for non-muted types, ACTION_REQUIRED included.
- `catchUp`:
  - `connections`, `communityWall` and `closingSoon` are 0 for muted categories;
  - `catchUp` is `null` when all three are 0, so the card hides.
- The raw section fields (`connections`, `communityWall`, `jobs`, `opportunities`, including the `closingSoon` list used by card chips) are unchanged.
- An additive `inAppMuted: string[]` lists the muted keys; the frontend hides badges from it.

**A-6 — Flag gating.**
- The nav tab (done) and the In-app table render only when the flag is on (D-2).
- Backend filtering applies only when `NotificationCentreService.isEnabled()`. With the flag off, responses are byte-identical to today.
- The PATCH accepts `inApp` regardless of the flag.
- Rows are hidden when their module flag is off [EV `brand.model.ts:71, 75, 83, 129`]:

  | Row | Module flag |
  |---|---|
  | Connection requests | `connections` |
  | Job applications | `jobs` |
  | Comments, mentions, reactions | `community_feed` |
  | New community posts | `community_feed` |
  | Event reminders | `events` |

- Always shown: Application updates, Deadlines, Account and security [INFERRED: they cover several modules].

**A-7 — Toasts are suppressed server-side.**
- `connections.service.ts:1293, 2789` skip `emitNotification()` when the recipient muted `connectionRequests`.
- `emitFetchCountToRoom()` is always sent.
- The frontend `SocketService` is unchanged.
- Chat toasts are untouched (D-7).

**A-8 — Mandatory notices.**
- The Account and security toggle is checked and disabled.
- The backend never excludes `platform_message`.

## Acceptance criteria

**Storage and API**
- [ ] A PATCH with the three legacy keys plus `inApp: { connectionRequests: false }`:
  - returns 200;
  - stores `inApp.connectionRequests = false`;
  - stores the legacy keys exactly as sent.
- [ ] A later PATCH with only the legacy keys leaves the stored `inApp` unchanged (A-2).
- [ ] Non-boolean `inApp` values → 400. Unknown `inApp` keys are stripped.
- [ ] A user with no `inApp` (never saved, or created by admin) behaves as all ON.
- [ ] Email/WhatsApp behaviour (`shouldSendNotification`, `shouldSendWhatsappNotification`) is unchanged.

**Flag off**
- [ ] The nav tab is hidden (D-2, done).
- [ ] The In-app table is hidden.
- [ ] `GET notifications`, `GET notifications/count` and toasts are byte-identical to today for any stored `inApp`.

**Flag on (D-5)**
- [ ] The nav tab is visible for every account type except INDIVIDUAL and JOB_SEEKER (done).
- [ ] Connection requests OFF:
  - `connection_request` / `connection_action` rows are absent from `GET notifications`, and pagination `meta` excludes them;
  - `bell` excludes `connections`, and `counters.connections` keeps the raw count;
  - `inAppMuted` contains `connectionRequests`;
  - the Connections badge and its share of the parent badge are hidden;
  - `catchUp.connections = 0`;
  - no `connection_requested` / `connection_accepted` toast is sent, but `fetch-count` still arrives;
  - the Connections page still lists pending requests.
- [ ] New community posts OFF:
  - `bell` excludes `communityWall`;
  - the Community wall badge is hidden;
  - `catchUp.communityWall = 0`.
- [ ] Job applications OFF:
  - `bell` excludes `jobs.total`;
  - the Jobs badge is hidden.
  - After SAN-1471: `job_application_status` rows are excluded from the list and from `statusUpdates`, including ACTION_REQUIRED rows.
- [ ] Application updates OFF (after SAN-1471): the four program-application types are excluded from the list and from `statusUpdates`, including ACTION_REQUIRED rows.
- [ ] Deadlines OFF:
  - `catchUp.closingSoon = 0`;
  - the catch-up card shows no closing-soon line;
  - the CFA/challenge card chips are unchanged.
- [ ] When every catch-up term is 0 because of muting, `catchUp = null` and the card is hidden.
- [ ] Turning a category back ON restores the rows, bell term, badge and catch-up line (rows were never deleted).
- [ ] `platform_message`, `startup_suggestion` / `investor_suggestion` rows and chat toasts are always shown.
- [ ] Comments/mentions/reactions and Event reminders toggles save and reload, and change nothing else.

**UI**
- [ ] `/account/edit/notification` shows the existing Email/WhatsApp table unchanged. Below it, a separate "In-app notifications" table with the 8 D-6 rows.
- [ ] Account and security is checked and disabled.
- [ ] Rows are hidden per A-6.
- [ ] Save sends the legacy keys plus `inApp`. Reload shows the saved state; a missing key shows ON.
- [ ] After save, the bell and badges refresh without a reload.

**Isolation**
- [ ] Only this deployment's tenant DB and only the session user's row are touched (invariant #5). `/check-isolation` passes.

## Per-repo plan

### backend (`sc-saas-backend`) — SAN-1741, first

1. **DTO / types**
   - `InAppSettingsDto`: 7 keys, each `@IsOptional() @IsBoolean()`.
   - `@IsOptional() @ValidateNested() @Type(() => InAppSettingsDto) inApp?` on `NotificationSettingsDto` (`user/dto/notification-settings.dto.ts`).
   - `inApp?` on `NotificationSettingsType` (`core/types/notification-type.ts`).
2. **Enum, map, helpers** (`core/constants/enum.ts`, `core/utils/app.utils.ts`)
   - `InAppCategory`.
   - `NOTIFICATION_TYPE_IN_APP_CATEGORY`, per the D-5 to D-7 mapping:
     - `connection_*` → `connectionRequests`;
     - `platform_message` → `mandatory`;
     - suggestions → `unmapped`.
     - SAN-1471's five types are added to the map by whichever spec lands second.
   - `isInAppEnabled()` and `mutedNotificationTypes()`.
3. **Merge on save:** `user/user.service.ts:523–539` (A-2).
4. **List:** `notifications.repository.ts:35` takes `excludeTypes`; `notifications.service.ts:73` passes it when the centre is on (A-4).
5. **Counters:** `notification-counters.service.ts`, using the user loaded at :95:
   - muted terms out of `bell` (:228);
   - `catchUp` zeroing and nulling (:234–242);
   - `inAppMuted` added, including on the `NotificationCounters` type (:43).
6. **Toasts:** guard at `connections.service.ts:1293, 2789` (A-7). Load the recipient's `notificationSettings` if it is not already on the entity.
7. **Jest:**
   - the helper (missing key = ON; mandatory and unmapped never muted);
   - merge;
   - list exclusion and pagination;
   - `bell` and `catchUp` arithmetic per category;
   - flag off = byte-identical;
   - toast guard.
   - `npm run build`, `npm run lint`.
8. Update `modules/user/module.spec.md` and `modules/notifications/module.spec.md` (the latter is stale).

### frontend (`sc-saas-frontend`) — SAN-1742, after backend

0. **Done (uncommitted):** the flag-gated nav tab in `account-setting-page-top-nav.component.ts:82–90` (D-2). Commit it with this issue, keeping the INDIVIDUAL / JOB_SEEKER exclusion.
1. `profile.model.ts`: `inApp?` on `NotificationSettings`.
2. `notification-settings` page:
   - keep the existing Email/WhatsApp table unchanged;
   - add a separate "In-app notifications" table below it, rendered only when the flag is on (D-2, D-4);
   - the table has the 8 D-6 rows, Account and security checked and disabled, rows gated per A-6;
   - add an `inApp` form group (missing → ON);
   - `submitNotificationForm()` sends the legacy keys plus `inApp`, then refreshes the counters (`SetNotificationsCount`).
3. `notifications.model.ts`: `inAppMuted?: string[]`.
4. `nav-badge.util.ts`: skip muted badges — `connections` → connectionRequests, `communityWall` → communityPosts, `jobs` → jobApplications. The opportunities badges are not affected (D-8).
5. The bell and the dashboard catch-up card need no logic change: they read `bell` and `catchUp`, which the backend already filters.
6. `EditProfileComponent`: no change (card commented out).
7. Karma:
   - form defaults;
   - disabled mandatory row;
   - payload shape;
   - flag-off hides the table;
   - `computeNavBadges` with `inAppMuted`.
   - `npm run build`.

### admin (`sc-saas-admin`)
- No change (D-5). Admin-written SAN-1471 rows are filtered at read time. The admin-seeded three-key default JSON means all ON.

### tenants / tenants-admin / ai-startups-analyzer / 3rdparty-webservices
- No change. No new flag.

## Coordination with SAN-1471 (approved, not implemented)

- SAN-1471 adds 5 `NotificationType` values and the `statusUpdates` bell term [EV `SAN-1471-application-status-updates.spec.md:32, 260–267`].
- The mapping is fixed by D-6:
  - `job_application_status` → `jobApplications`;
  - `cfa_/program_/vs_program_/mentor_application_status` → `applicationUpdates`.
- Muting applies to ACTION_REQUIRED rows too (D-5).
- Whichever spec is implemented second does two things:
  - adds the five types to `NOTIFICATION_TYPE_IN_APP_CATEGORY`;
  - makes `statusUpdates` exclude muted types.
- Until then, the toggles are stored with no effect.

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| API (#2) — `PATCH users/profile/notification-settings` | Additive optional `inApp`; storage replace → merge. No admin cURL caller [INFERRED — admin writes the column directly] | `/audit-contract` (`profile.service.ts:359`) |
| API (#2) — `GET notifications`, `GET notifications/counters` | Flag on: muted types excluded from the list; `bell` and `catchUp` exclude muted terms; additive `inAppMuted` | `/audit-contract` (`core/service/notifications.service.ts`, `NotificationCounters`) |
| `users.notification_settings` JSON (backend + admin writers) | Additive `inApp`; admin's default stays valid | Review |
| Flag `notification_centre_enabled` (#1) | Reused. Now also gates the account nav tab (frontend) | `/trace-flag notification_centre_enabled` |
| Auth (#4) | Unchanged — `JwtAuthGuard`; identity from the session | — |
| Tenant scoping (#5) | Own deployment DB, session user's row only | `/check-isolation` |
| Socket gateway | Fewer per-type toasts for muted users; `fetch-count` unchanged | — |
| Verification shape (#3), PowerPitch (#6) | Not touched | — |

## Test plan

There is no "guardian" skill in this workspace. Say so in the PR wherever automated coverage cannot be added.

- **backend:** Jest as in the plan; `npm run build`, `npm run lint`. Manual on a dev tenant:
  - mute each category and check the list, `bell`, `catchUp`, `inAppMuted` and toasts;
  - PATCH with legacy keys only → `inApp` survives;
  - flag off → byte-identical responses.
- **frontend:** Karma as in the plan; `npm run build`. Manual:
  - the nav tab with the flag on and off, and for INDIVIDUAL / JOB_SEEKER;
  - both tables render, and the In-app table sits below the Email/WhatsApp table;
  - toggles persist;
  - the mandatory row is locked;
  - the bell, badges and catch-up card update after save;
  - the Connections page still lists requests while muted.
- **cross-repo:**
  - an admin-created user (three-key JSON) sees all toggles ON;
  - tenant isolation;
  - after SAN-1471, an admin-written status row is hidden when its category is muted.

## Rollout

1. **backend** first. It is inert until a user saves `inApp`, and the filtering is flag-gated.
2. **frontend** second, including the nav-tab change.
3. Enable per tenant with the existing `notification_centre_enabled` rollout. No migration.

## Out of scope

- Per-category Email/WhatsApp toggles and frequency (later EX-19 phases).
- Quiet hours (EX-20/21) and DPDP consent.
- Building the missing in-app sources: comments/mentions/reactions, event reminders (SAN-1472), deadline reminders, and SAN-1471's rows (own spec).
- Muting the mode-B opportunities counters (D-8).
- Muting suggestion broadcasts or chat toasts (D-7).
- Admin-side (operator) preferences; any admin change.
- `GET notifications/count` (legacy) — unchanged.
- Re-enabling the commented-out EditProfile card.
- Changing the existing Email/WhatsApp table, including the `fundingRequests` label quirk.

## Open questions

None. All were resolved by Mahima on 2026-10-06 (D-1 to D-8).

## Linear tracking

- **Parent:** SAN-1478 (project "Enhancement", assignee Mahima Sharma). No new project.
- **Sub-issues:** Todo, priority Low, assignee Mahima Sharma, project Enhancement, parent SAN-1478, labels `Feature` plus the repo badge.

| Repo | Issue | Notes |
|---|---|---|
| backend | SAN-1741 | — |
| frontend | SAN-1742 | blocked by SAN-1741; includes committing the nav-tab change |
