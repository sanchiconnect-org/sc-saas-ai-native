---
id: SAN-1480
title: "Notifications Phase 2 — EX-21 Quiet hours and batching (no push/WhatsApp 21:00–08:00 IST; low-priority items batched)"
type: feature
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1480/notifications-p2-ex-21-quiet-hours-and-batching   # existing issue (project "Enhancement", assignee Mahima Sharma, Backlog). single tracking issue, no separate project or sub-issues; see "Linear tracking"
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-21 (W-07 annotation 4), Phase 2. BRD itself is not in the workspace; only the Linear placeholder text is available."
repos: [backend]                 # dependency order. CERTAIN: backend. CONDITIONAL (added only if an Open question is decided that way): tenants (OQ-3 new flag) → backend → frontend (OQ-9 user-facing setting) → admin (OQ-3 tenant-configurable window / OQ-11 held-message log)
contracts:
  api:
    - "No NEW or CHANGED routes under the recommended defaults. (A user-facing toggle (OQ-9) would extend the EXISTING PATCH api/v1/users/profile/notification-settings with an optional key; additive.)"
  flags:
    - wa_send_messages              # EXISTING (tenants tenant_users.wa_send_messages → backend Feature.WA_SEND_MESSAGES). Consumed, unchanged
    - cron_enabled                  # EXISTING master cron switch. Consumed, unchanged
    - "No new flag (OQ-3 = always on). The `whatsappHeldRelease` cron row's `active` is the per-tenant switch (fail-open)."
  events:
    - "NEW table (tenant DB) `whatsapp_held_messages`"
    - "cron_jobs — ONE new CronJobName `WHATSAPP_HELD_RELEASE` (`whatsappHeldRelease`, `*/5 * * * *`), seeded INACTIVE, Asia/Kolkata"
tenant_scoped: true              # held messages contain user phone numbers + template data and live in each tenant's own DB
depends_on: [SAN-1478, SAN-1479] # SAN-1478 owns notification_settings JSON (merge-on-save); SAN-1479 adds the consent gate inside shouldSendWhatsappNotification — quiet-hours must layer on top of both, not race them
created: 2026-10-13
---

# Notifications Phase 2 — EX-21 Quiet hours and batching

## Reference and evidence tags

- **Source (verbatim, Linear SAN-1480, no comments):** "Placeholder (BRD Phase 2). Needs its own spec. BRD ref: EX-21 (W-07 annotation 4). No push or WhatsApp messages between 9 pm and 8 am IST; low-priority items batched rather than sent one at a time."
- **Builds on:** `specs/features/SAN-1381-notifications-action-driven-dashboard.spec.md` (Phase 1; lists EX-21 as Phase 2 and **EX-18 "Mobile push and WhatsApp" as Phase 3**, `SAN-1381-linear-breakdown.md:250, 259`), `SAN-1478` (preferences), `SAN-1479` (DPDP consent), `SAN-1471` / `SAN-1472` (both decided **in-app only**), `SAN-1475` / `SAN-1476` (cron + claim patterns; the 09:00 IST admin digest).
- **Tags** (`specs/spec-authoring-practices.md`): **[EV]** evidenced with `file:line`; **[INFERRED]** drawn from code, not stated; **[NOT SPECIFIED]** neither BRD text nor code says; **[DESIGN DECISION PENDING]** (**[DDP]**) needs a human decision — see Open questions.
- Paths without a repo prefix are in `sc-saas-backend/src/`.

## Problem

Off-platform messages are sent the moment the triggering action happens, at any hour. A connection request accepted at 23:30, an admin approving a profile at 22:00, or a meeting reminder for an 08:15 meeting all go out as WhatsApp messages in the middle of the night. EX-21 asks for (a) no push or WhatsApp messages between 21:00 and 08:00 IST, and (b) low-priority items to be batched instead of each one producing its own message.

## Current state (checked against code, 2026-10-13)

### 1. Push — there is no push channel to put quiet hours on

- `users.push_token` exists (`text`, default null) [EV `modules/user/entities/user.entity.ts:114–115`] and the frontend model mirrors it [EV `sc-saas-frontend/src/app/core/domain/profile.model.ts:73`]. No code writes or reads it for sending [EV grep: no other `pushToken` / `push_token` use in backend `src`]. SAN-1381 records the same: "No FCM or web-push exists today; `users.push_token` is unused" [EV `SAN-1381-…spec.md:573`].
- No FCM / Firebase / web-push / OneSignal sender in backend [EV grep `firebase|fcm|web-push|onesignal` → only commented-out OneSignal code in `modules/conversations/conversations.service.ts:120–133` and a `oneSignalPlayerId` select in `conversations.repository.ts:254–259` that has no matching column on `UserEntity` [EV grep user.entity.ts: no match]].
- No `SwPush` / `requestSubscription` / `showNotification` in the frontend [EV grep `sc-saas-frontend/src`: no match].
- sc-saas-3rdparty-webservices has no push module: its modules are `cometChat, convertKit, sendGrid, ses, shortIo, sms, videoSDK` [EV glob `sc-saas-3rdparty-webservices/src/modules/*/`].
- Push is BRD **EX-18, Phase 3** [EV `SAN-1381-linear-breakdown.md:259`].
- **Consequence:** the "push" half of EX-21 can only be delivered as a **policy hook** that EX-18 must call when it is built. [INFERRED]

### 2. WhatsApp — exists, one choke point, called directly (not via the gateway)

- Single sender: `WhatsappService.sendMessages(templateCode, messageData[])` [EV `core/services/whatsapp.service.ts:37–96`]. It reads the WATI endpoint/token from `spa_settings` (`type = 'whatsapp'`) [EV :19–35], loads the template, **returns silently unless `api_template_status = 'APPROVED'`** [EV :46–47], and POSTs `{template_name, broadcast_name, receivers[]}` to `{wati_api_endpoint}/api/v1/sendTemplateMessages` [EV :73–89].
- It goes **directly to WATI**, not through sc-saas-3rdparty-webservices [EV :79; `sc-saas-backend/CLAUDE.md` "whatsapp.service.ts … NOT via THIRD_PARTY_SERVICE_BASE_URL"]. So **sc-saas-3rdparty-webservices is not affected** by this feature.
- It swallows errors (`console.log(error)`) and returns nothing [EV :88–93], so callers cannot tell success from failure. Callers usually do not `await` it (e.g. `modules/verifications/verifications.service.ts:111`) [EV].
- `sendMessages` itself checks **no flag**. Callers gate on `saasFeatures[Feature.WA_SEND_MESSAGES]` (51 occurrences across 19 files) [EV grep count] and/or `shouldSendWhatsappNotification()` [EV `core/utils/app.utils.ts:1101–1120`], which requires `WA_SEND_MESSAGES`, then SAN-1479 consent (`consent.whatsapp.activity`), then the user's `newChatConversation.whatsapp` toggle.
- **85 call sites in 23 files** [EV grep count `.sendMessages(`], largest: `modules/global/admin-actions/admin-actions.service.ts` (38, admin-triggered actions), `meetings.service.ts` (8), `connections.service.ts` (6).
- Cron jobs that send WhatsApp [EV grep `modules/cron`]: `meeting-reminder.service.ts:145, 208` (`MEETING_REMINDER`, seeded `*/1 * * * *` — can fire at any hour), `growth-metrics-reminder.service.ts:211`, `startup-recommendation-to-investor.service.ts:112` (seeded `0 10 * * 1`) [EV `modules/cron/repository/cron-job.repository.ts:62–63, 90–91`].
- Flag `wa_send_messages`: tenants column default `false` [EV `sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-users.entity.ts:1059–1065`], exposed in tenant-settings [EV `sanchiconnect-saas-tenants/src/modules/global/global.service.ts:227, 552, 864`], backend `Feature.WA_SEND_MESSAGES = 'wa_send_messages'` [EV `core/constants/enum.ts:1278`]. Not in frontend `IFeatures` or admin `config/` [EV grep: no match] — it is backend-only today.
- **Existing per-template classification:** `whatsapp_templates.message_type` enum `authentication | utility | marketing`, default `utility` [EV `modules/global/admin/spa_whatsapp_templates.entity.ts:20–26`; `core/constants/enum.ts:1747–1751`]. These are WhatsApp/Meta's own template categories. **This is the only existing "priority-like" attribute on a WhatsApp message.** [INFERRED that it is set meaningfully per template — not verified against tenant data]
- Template codes (40+) in `WhatsappTemplateCode` [EV `core/constants/enum.ts:1876–1936`], including `one_time_password` (OTP, sent at `verifications.service.ts:111, 179, 263` behind `WA_SEND_MESSAGES`), `meeting_reminder`, `chat_message`, `connection_request_received`, `cron_incomplete_profile`, `cron_milestone_update_reminder`, `invitation_to_join`.
- **Batching at the API level only:** one `sendMessages` call can carry many `receivers` [EV :52–77]. There is **no per-user aggregation** (several items → one message) anywhere.

### 3. No quiet-hours, deferral, or WhatsApp queue exists

- No `quiet`, `dnd`, `send_after`, `scheduled_at`, or deferred-send concept in backend `*.ts` [EV grep — only unrelated comments].
- No WhatsApp outbox/queue table. The only send queue is **email**: `ses_email_queue` [EV `core/entities/ses-email-queue.entity.ts:9–169`] with `in_process`, `is_sent`, `email_sent_status`, `send_timestamp`, drained by cron `SEND_EMAIL_QUEUE_EMAIL` (`*/5`) [EV `cron.service.ts:275–280`; `cron-job.repository.ts:82–83`]. It is the closest precedent for a held-message table. [EV + INFERRED]
- **Priority concept for in-app only:** `NotificationCategory` `action_required | new | system` [EV `core/constants/enum.ts:448–452`] on `notifications` rows; `InAppCategory` (7 keys) for SAN-1478 muting [EV :399–407]. Neither applies to WhatsApp sends.
- **Batching precedent:** the SAN-1476 daily admin digest (email, 09:00 IST, admins only) [EV `cron-job.repository.ts:211–212`; `SAN-1476-…spec.md:3`]. The user-side "What you missed" email digest (EX-17) has **no spec and no code** [EV glob `specs/features/SAN-14*` — no EX-17 file]. So there is no user-facing batch to fold low-priority items into today.

### 4. Time zone handling (IST) — fixed IST everywhere; no per-user zone in use

- Every cron job is registered with `'Asia/Kolkata'` [EV `modules/cron/cron.service.ts:135, 152, …`].
- `EVENT_SCHEDULE_TIMEZONE = 'Asia/Kolkata'` [EV `core/constants/enum.ts:29`], reused by `notification-centre.service.ts:23` [EV].
- SQL IST clock: `IST_NOW_SQL = '(UTC_TIMESTAMP() + INTERVAL 330 MINUTE)'` [EV `modules/notifications/repositories/notification-counters.repository.ts:75`].
- `users.timezone` column exists (nullable varchar) [EV `modules/user/entities/user.entity.ts:131–132`], but no writer was found in `modules/user` or `modules/auth` [EV grep `timeZone\s*[:=]` → only meetings/events/facility/DTO fields]. [INFERRED: unpopulated for most users] — so a per-user quiet window has no data source today.

### 5. Email and in-app are not named by EX-21

- Email goes `SESEmailService` → sc-saas-3rdparty-webservices / `ses_email_queue`. In-app = `notifications` rows + socket `fetch-count` / toasts (SAN-1381). EX-21 names only push and WhatsApp. [EV issue text] Whether they are exempt is OQ-7.

## Proposed design (recommendations — every [DDP] item needs a decision before approval)

**P-1 — One gate at the choke point, not 85 call-site edits.**
- Add a `QuietHoursService` (backend, `core/services/quiet-hours.service.ts`) with `isQuietNow(): boolean` and `nextReleaseAt(): Date`, computed in **Asia/Kolkata** using the existing `EVENT_SCHEDULE_TIMEZONE` constant (so server TZ does not matter). Window default 21:00 → 08:00 [EV issue text] — fixed vs configurable is **OQ-1 / OQ-3** [DDP].
- `WhatsappService.sendMessages()` asks the gate before POSTing. If quiet and the template is not exempt (P-2), it **holds** the message (P-4) instead of sending. Callers are unchanged. [INFERRED: safe because no caller depends on the return value — EV :88–96]
- Push: `QuietHoursService` is the documented hook EX-18 must call; nothing else is built for push here (§1).

**P-2 — What bypasses quiet hours** [DDP → OQ-5]
- Recommended default: templates with `message_type = 'authentication'` (OTP, email verification) are **never held** — a held OTP is useless. [INFERRED from §2]
- Whether `meeting_reminder`, `chat_message`, ticket / escalation-type templates bypass, or are held/dropped, is a product call (OQ-5, OQ-8).

**P-3 — What "low-priority" means and how it is batched** [DDP → OQ-4, OQ-6]
- Candidate classifier with zero new data: `whatsapp_templates.message_type = 'marketing'` → low priority [EV §2]. Alternative: an explicit code-side list of `WhatsappTemplateCode` values (e.g. `cron_incomplete_profile`, `cron_milestone_update_reminder`, `invitation_to_join`, recommendations), or a new per-template column editable in admin.
- "Batched rather than sent one at a time" has two readings [NOT SPECIFIED]:
  - **(a) Release batching:** low-priority messages are always held and released together at one daily time (e.g. 08:00 or a later slot), each still its own template message.
  - **(b) Aggregation:** N low-priority items for one user become **one** summary message. This needs a **new Meta-approved WhatsApp template** (unapproved templates are silently dropped, EV `whatsapp.service.ts:46–47`) and per-type summary copy.
- Recommendation: (a) for this phase, (b) deferred. Decision: OQ-6.

**P-4 — Held-message storage** [technical, dev lead → OQ-12]
- No existing table fits (§3). Proposed new tenant-DB table `whatsapp_held_messages` (name TBD), modelled on `ses_email_queue`: `id`, `template_code`, `receiver` (one row per receiver: `whatsapp_number`, `user_id` nullable, `data` JSON), `reason` (`quiet_hours` | `low_priority_batch`), `release_at` (UTC), `status` (`held` | `in_process` | `sent` | `expired` | `skipped`), `attempted_at`, `created_at`, `expires_at` nullable.
- Created by TypeORM `synchronize: true` [EV per SAN-1472 spec `core/database/database.module.ts:32`]. Admin does not read or write it unless OQ-11.

**P-5 — Release job**
- New `CronJobName` (e.g. `WHATSAPP_HELD_RELEASE`), seeded `*/5 * * * *`, **inactive** (house rule, `cron-job.repository.ts`), registered via `runCronJob()` like SAN-1472/1475.
- Each run, outside the quiet window: select `status = 'held' AND release_at <= now`, bounded (`LIMIT`), **atomic claim** (`UPDATE … SET status='in_process' WHERE id=:id AND status='held'`, act only on `affectedRows = 1`, SAN-1472 P-4 pattern), then call the WATI sender **bypassing the gate**, mark `sent`.
- **Re-check at release** (not just at hold time): `WA_SEND_MESSAGES` still on, user still exists/not deleted, `shouldSendWhatsappNotification`/consent still allows (a user who withdrew consent overnight must not get the message) → else `skipped`. [INFERRED requirement from SAN-1479]
- Stale messages: `expires_at` passed → `expired`, not sent (e.g. a meeting reminder for a meeting that already started). Which templates get an expiry: OQ-8.
- Because `sendMessages` swallows errors (§2), "sent" means "handed to WATI"; a failed POST is not retried. [INFERRED; matches today's behaviour]

**P-6 — Gate / flag** [DDP → OQ-3]
- Options: (i) always on for all tenants (no flag); (ii) reuse `notification_centre_enabled`; (iii) a NEW tenant flag owned by tenants (`tenant_users` column) → backend `Feature` enum → frontend `IFeatures` only if a UI needs it → admin `config.php` only if admin reads it — a full invariant #1 change with `/trace-flag`.
- Independent of the choice: the release cron row must be active, or held messages would never go out. Recommendation [INFERRED]: when the feature is on but the cron row is inactive / `cron_enabled` off, **do not hold** — send immediately (fail open) and log a warning, so messages are never silently stranded.

## Acceptance criteria

(Written against the recommended defaults; the bracketed items change with the linked OQ.)

**Quiet window**
- [ ] With the feature on and the release cron active, a non-exempt WhatsApp message triggered at 21:00:00 IST, 23:30 IST or 07:59:59 IST is **not** POSTed to WATI; one held row per receiver is written with `release_at` = 08:00 IST next occurrence (stored UTC).
- [ ] A message triggered at 08:00:00 IST or 20:59:59 IST is sent immediately (window is `[21:00, 08:00)` IST) [OQ-1].
- [ ] Results are identical regardless of server/Node/MySQL time zone (jest with mocked clock at UTC and at a non-UTC zone).
- [ ] OTP / email-verification (`message_type = 'authentication'`) messages are sent immediately at any hour [OQ-5].

**Release**
- [ ] Held rows are sent on the first run at or after `release_at` outside the window, each exactly once even with two concurrent runs (claim `affectedRows` test).
- [ ] A held row whose recipient has since withdrawn WhatsApp consent, been deleted, or whose tenant has turned `wa_send_messages` off is marked `skipped` and not sent.
- [ ] A held row past `expires_at` is marked `expired` and not sent [OQ-8].
- [ ] With the release cron inactive or `cron_enabled` off, nothing is held; messages send immediately and a warning is logged [OQ-3 / P-6].

**Batching** [OQ-4, OQ-6]
- [ ] Low-priority templates triggered at any time are held and released together at the agreed release time, not at trigger time.
- [ ] No low-priority message is sent inside the quiet window.

**Unchanged behaviour**
- [ ] With the feature off: `WhatsappService.sendMessages` behaviour is byte-identical to today (same POST, same timing).
- [ ] Email, in-app rows, socket `fetch-count` and toasts are unaffected [OQ-7].
- [ ] All 85 existing `sendMessages` call sites compile and behave unchanged apart from timing; no call-site edits required.

**Isolation**
- [ ] Held rows live only in this deployment's tenant DB; the release job only reads/sends its own rows; no host/tenant hard-coded. `/check-isolation` passes.

## Per-repo plan

### backend (`sc-saas-backend`) — certain, first

1. `core/services/quiet-hours.service.ts`: `isQuietNow()`, `nextReleaseAt()`, `isExempt(templateMessageType, templateCode)`, `isLowPriority(...)` — all in Asia/Kolkata via `EVENT_SCHEDULE_TIMEZONE` (`core/constants/enum.ts:29`). Window source per OQ-1/OQ-3 (constant, `saasSettings`, or `spa_settings`).
2. `core/services/whatsapp.service.ts`: load `messageType` with the template (:42–45); before the POST (:88) call the gate; split into `sendMessages()` (gated) and an internal `postToWati()` (ungated, used by the release job). Keep the public signature.
3. New entity + repository for held messages (P-4), e.g. `core/entities/whatsapp-held-message.entity.ts`; enums for status/reason in `core/constants/enum.ts`.
4. `modules/cron/whatsapp-held-release.service.ts` (P-5); `CronJobName` entry; seed inactive `*/5 * * * *` in `modules/cron/repository/cron-job.repository.ts`; `case` in `cron.service.ts` via `runCronJob()`; register in `cron.module.ts`.
5. Re-check helpers at release reuse `shouldSendWhatsappNotification` / SAN-1479 consent where the original call was user-scoped [INFERRED: not every call site passes a user id today — the held row only has a phone number for some; see OQ-12].
6. Jest: window edges (20:59:59, 21:00, 07:59:59, 08:00) in two server time zones; exempt vs held; low-priority hold; claim race; consent withdrawn overnight → skipped; expiry; flag off → identical POST; cron inactive → fail open.
7. Update `modules/cron/module.spec.md` (new job) and the `core/services` notes / backend `CLAUDE.md` service list.

### tenants (`sanchiconnect-saas-tenants`) — only if OQ-3 picks a new flag or a cockpit-owned window setting
- New `tenant_users` boolean column (default `false`) and exposure in `global.service.ts` tenant-settings selects (:227 / :552 / :864 pattern), then `/trace-flag`. Would move to the **front** of `repos`.

### frontend (`sc-saas-frontend`) — only if OQ-9 adds a user-facing setting
- Extend `/account/edit/notification` (SAN-1478 page) with the setting; `profile.model.ts` key. Backend DTO gets an optional key (additive, merge-on-save already in place per SAN-1478 A-2).

### admin (`sc-saas-admin`) — only if OQ-3 (tenant-configurable window via `spa_settings`) or OQ-11 (held-message log page)
- Seed/edit `spa_settings` keys; optionally list the held table via the generic table engine. Enabling the release cron row needs no admin code (generic `cron_jobs` page, per SAN-1472 §3).

### sc-saas-3rdparty-webservices / ai-startups-analyzer / sanchiconnect-saas-tenants-admin
- No change. WhatsApp does not go through the gateway (§2); push does not exist (§1).

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| Flag names (#1) | None under options (i)/(ii). Option (iii) adds a flag owned by tenants `TenantUsersEntity` → backend `Feature` → frontend `IFeatures` (if UI) → admin `config.php` (if read) | `/trace-flag wa_send_messages`; `/trace-flag <new flag>` if (iii) |
| API contract (#2) | None under defaults. OQ-9 → additive optional key on `PATCH users/profile/notification-settings` | `/audit-contract` vs frontend `core/service/profile.service.ts` |
| Verification shape (#3) | Only if a cockpit-owned flag/setting is added (additive field in tenant-settings) | `/trace-flag` |
| Auth (#4) | Unchanged. No new route; cron is in-process with no HTTP surface | — |
| Tenant scoping (#5) | New held-message table in this deployment's DB only; one deployment = one tenant | `/check-isolation` |
| PowerPitch (#6) | Not touched | — |
| WATI (external, not a SanchiSaaS contract) | Same endpoint and payload; only the send time moves | review |
| `notification_settings` JSON (shared with admin writers) | Only if OQ-9; additive key, missing = default | review |

## Test plan

No "guardian" skill exists in this workspace; state in the PR where automated coverage can't be added.

- **backend:** jest per plan step 6; `npm run build`; `npm run lint`. Manual on a dev tenant with a WATI sandbox: trigger a connection-request WhatsApp at 21:05 IST (or with the clock mocked) → held row, no WATI call; OTP at 21:05 → sent; activate the release cron, move the clock to 08:00 → sent once; withdraw consent before release → skipped.
- **tenants / frontend / admin:** only if their conditional work is approved — `npm run build` / `ng build` + karma / `php -l`.
- **cross-repo:** feature off → identical WATI traffic; tenant A on, tenant B off → B unaffected.

## Rollout

1. (If OQ-3 iii) **tenants**: flag column default `false`.
2. **backend**: gate, held table (additive, via synchronize), release service, cron seeded **inactive**. Inert until enabled.
3. Per tenant: activate the release cron row → enable the feature/flag (in that order, so nothing is held without a releaser) → re-arm via `PATCH saas/settings` or restart.
4. Internal tenant first; watch held-row counts and the 08:00 release burst against WATI rate limits [NOT SPECIFIED — WATI limits unknown].

## Out of scope

- Building any push channel (FCM/web-push/OneSignal) — that is EX-18 (Phase 3). This spec only provides the gate it must call.
- Per-user aggregated "summary" WhatsApp messages (P-3 reading (b)) unless OQ-6 picks it.
- The user-side "What you missed" email digest (EX-17).
- Retrying WATI failures; changing `sendMessages`' swallow-errors behaviour.
- Changing `meeting-reminder.service.ts` timing logic (its IST/UTC date observation is recorded in SAN-1472 §1).
- SMS (excluded by the BRD per SAN-1381 Out of scope) and email quiet hours unless OQ-7 says otherwise.
- The dead `oneSignalPlayerId` select in `conversations.repository.ts:254–259` (candidate `/bug-fix`).

## Open questions

None. All resolved 2026-10-13 (see below).

## Resolved decisions (2026-10-13, Mahima Sharma)

- **OQ-1** Fixed IST window `[21:00, 08:00)` for every user (21:00 quiet, 08:00 sendable). No per-user time zone. *(default)*
- **OQ-2** WhatsApp only this phase. Push gets the `QuietHoursService` hook for EX-18. *(user)*
- **OQ-3** Always on, no new flag. Window is a code constant, not tenant-configurable. *(user)* The release cron row's `active` is the per-tenant switch (OQ-13).
- **OQ-4** Low-priority = `whatsapp_templates.message_type = 'marketing'`. *(user)*
- **OQ-5** Bypass quiet hours: `authentication` templates (OTP, email verification) and `meeting_reminder`. Chat, tickets/escalations and approvals/rejections are held. *(user)*
- **OQ-6** Release as individual template messages (no summary template). Low-priority messages are batched **all day** to the next full IST hour (08:00 if that hour is quiet). Quiet-hour holds release at 08:00 IST. Each release run sends one WATI call per template carrying all due receivers. *(user: "individually at 08:00 IST, low-priority batched to the next release slot"; the hourly slot is the implementation's reading of "release slot")*
- **OQ-7** Email, in-app rows, socket toasts and SMS are untouched. *(default)*
- **OQ-8** Meeting reminders bypass, so no per-template expiry. Generic guard: a row more than 24 h past its `release_at` (e.g. the job was off) is `expired`, not sent. *(user + default)*
- **OQ-9** No user control this phase. *(default)* frontend not in scope.
- **OQ-10** 08:00 burst accepted; one WATI call per template per 5-min run, at most 500 rows per run. *(default)*
- **OQ-11** No admin log page this phase. *(default)* admin not in scope.
- **OQ-12** New table `whatsapp_held_messages`, one row per receiver. Release-time re-check matches the stored number against live users (`CONCAT(country_code, COALESCE(NULLIF(whatsapp_number,''), mobile_number))`, same as `getCombinedUserWhatsappNumber`). If a live user matches and `consent.whatsapp.activity === false`, the row is `skipped`. Numbers matching no live user (invitees, or deleted users) are still sent. No call sites edited. *(default)*
- **OQ-13** Fail-open: nothing is held unless `cron_enabled` is on and the `whatsappHeldRelease` row is active. A failed hold write also sends immediately. *(default)*

## Implementation (sc-saas-backend, uncommitted on `ai_native_setup_mahima`)

- `src/core/services/quiet-hours.service.ts`: window, `nextQuietHoursEnd`, `nextBatchSlot`, `isExempt`, `isLowPriority`, `holdDecision`. Plain UTC+05:30 math, so it does not depend on the server time zone.
- `src/core/entities/whatsapp-held-message.entity.ts`: `whatsapp_held_messages` table, registered in `CronModule` `forFeature`, created by `synchronize`.
- `src/core/services/whatsapp.service.ts`: `sendMessages()` gates and holds. `sendHeldMessages()` sends without the gate. `postToWati()` holds the unchanged WATI POST. The empty constructor is kept, because the service is provided in ~20 modules.
- `src/modules/cron/whatsapp-held-release.service.ts` + `cron.service.ts` case + inactive seed in `cron-job.repository.ts` + `CronJobName.WHATSAPP_HELD_RELEASE`, `WhatsappHeldReason`, `WhatsappHeldStatus` in `enum.ts`.
- Tests: `quiet-hours.service.spec.ts` (18), `whatsapp.service.quiet-hours.spec.ts` (9), `whatsapp-held-release.service.spec.ts` (7), all passing. `tsc --noEmit` clean. `src/modules/cron` + `src/core/services` suites: 300 passed, 5 skipped. Lint: no new errors (the pre-existing empty-constructor error in whatsapp.service.ts is unchanged).
- Contract gates: no API/DTO change (no `/audit-contract` needed). No flag added or renamed; `wa_send_messages` / `cron_enabled` are only read (no `/trace-flag` needed). Tenant isolation: the new table and job live only in this deployment's DB, and no host or tenant is referenced.
- Not done: manual run against a WATI sandbox.

## Linear tracking

- **Tracking issue (single):** SAN-1480, already in project **Enhancement** (assignee Mahima Sharma, status Backlog, priority Low, label Feature). Per user instruction (2026-10-13), **all work is tracked on this one existing issue**. No new Linear project and no per-repo sub-issues. Move SAN-1480 Todo → In Progress → In Review → Done as work happens.
- **Repos covered by SAN-1480:** sc-saas-backend (always). sanchiconnect-saas-tenants (only if OQ-3 = new flag or cockpit-owned window), sc-saas-frontend (only if OQ-9 = user-facing setting), sc-saas-admin (only if OQ-3 = `spa_settings` window or OQ-11 = log page). If any of these conditional repos joins, add its `Repo: *` badge label to SAN-1480.
