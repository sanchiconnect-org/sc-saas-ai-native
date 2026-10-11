---
id: SAN-1475
title: "Notifications Phase 2 — EX-11 Escalation rules (overdue outreach, grievances nearing SLA breach)"
type: feature
status: in-review               # approved + implemented 2026-10-08; manual dev-tenant run + EXPLAIN still pending
linear: https://linear.app/sanchiconnect/issue/SAN-1475/notifications-p2-ex-11-escalation-rules   # project "Enhancement"
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-11 (W-08 annotation 1), Phase 2"
repos: [backend, admin]         # dependency order. admin = one seed line for the new setting (OQ-2) only
contracts:
  api:
    - "No new routes. No changed DTOs. No manual cron-trigger route."
  flags:
    - notification_centre_enabled   # EXISTING (SAN-1401) — gate, consumed unchanged
    - cron_enabled                  # EXISTING master cron switch — consumed unchanged
  events:
    - "cron_jobs — ONE new CronJobName `ESCALATION_RULES` (seeded INACTIVE, like every non-core job)"
    - "spa_email_templates — TWO new template codes (`outreach-escalation`, `grievance-escalation`), seeded by backend"
    - "spa_settings — ONE new key `escalation_admin_ids` (OQ-2), seeded by admin next to the existing SLA keys"
tenant_scoped: true
depends_on: [SAN-1381]          # SLA keys, ticket_category / acknowledged_at, outreach queue all merged in Phase 1
created: 2026-10-08
---

# Notifications Phase 2 — EX-11 Escalation rules

## Reference and evidence tags

- **BRD:** EX-11, Phase 2 (W-08 annotation 1). The BRD itself is not in the workspace. The only source text is Linear SAN-1475 (no comments):
  > Outreach requests past SLA, and grievances nearing breach, escalate automatically to a designated senior admin or the SanchiConnect super admin.
  > Note: needs a scheduled job; the scheduler lives in the backend `modules/cron/`, because sc-saas-admin has no cron.
- **Builds on:** `specs/features/SAN-1381-notifications-action-driven-dashboard.spec.md` (Phase 1: SLA settings, outreach queue, grievance split) and `specs/features/SAN-1472-event-reminders.spec.md` (cron + atomic-claim pattern).
- **Tags:** **[EV]** evidenced with `file:line`; **[INFERRED]** drawn from code, not stated; **[NOT SPECIFIED]** nobody says; **[DDP]** design decision pending (see Open questions).
- Paths without a repo prefix are in `sc-saas-backend/src/`.

## Problem

Phase 1 made overdue outreach requests and grievances *visible* (Overdue chips, SLA columns, bell counts). Visibility depends on someone opening the admin panel. If the admin who owns the queue is away, an outreach request can sit past its 48 h SLA and a grievance can blow through its 24 h acknowledge / 7 day resolve SLA with nobody senior knowing. EX-11 asks for an automatic push to a senior admin before (grievances) or once (outreach) the SLA is missed.

## Current state (checked against code, 2026-10-08)

### 1. SLA definitions already exist — in admin, read from `spa_settings`

- Keys and defaults [EV `sc-saas-admin/includes/notification_centre_functions.php:52–58`]: `sla_outreach_decision_hours` = 48, `sla_grievance_ack_hours` = 24, `sla_grievance_resolve_days` = 7. Seeded on admin page load by `ensureNotificationCentreSettings()` [EV :121].
- **Outreach overdue** [EV :328–363]: `partner_broadcast_requests` `status='pending' AND target_scope='hub'` and `created_at < NOW() − sla_outreach_decision_hours`; plus `program_promotions` (main DB) with the same age rule.
- **Grievance overdue** [EV :549–558]: `ticket_status='open'` and (`created_at < NOW() − sla_grievance_resolve_days` OR (`ticket_category='grievance' AND acknowledged_at IS NULL AND created_at < NOW() − sla_grievance_ack_hours`)). `awaiting_user` tickets are excluded (the next move is the user's).
- The backend can read `spa_settings` [EV `modules/global/admin/spa_settings.entity.ts`] but nothing reads these keys there today.

### 2. Data the backend can already reach (tenant DB)

| Table | Backend entity | Relevant columns |
|---|---|---|
| `partner_broadcast_requests` | [EV `modules/global/broadcast_messages/partner-broadcast-requests.entity.ts:62`] — schema only, admin writes it | `status` (`pending/approved/rejected/sent`), `target_scope` (`self/hub`), `partner_id`, `title`, `created_at`, `deleted_at` |
| `tickets` | [EV `modules/tickets/entities/tickets.entity.ts`] | `ticket_category` (`feedback/grievance`), `ticket_status` (`open/closed/awaiting_user`), `acknowledged_at`, `assigned_to_ids` (json), `severity`, `ticket_number`, `created_at` |
| `spa_admin_users` / `spa_admin_roles` | [EV `modules/global/admin/spa_admin_users.entity.ts`, `spa_admin_roles.entity.ts:12`] | `name`, `email`, `role`; role `code` |
| `spa_email_templates` | [EV `modules/global/admin/spa_email_templates.repository.ts`] | `template_code` lookup; backend already seeds templates (FA-010 jury NDA) |

- **`program_promotions` is NOT reachable.** It lives in the tenants (main) DB [EV `sanchiconnect-saas-tenants/src/modules/global/entities/program-promotions.entity.ts`]; the backend only POSTs tracking to the tenants API [EV `modules/application-management/application-program.service.ts:2020`] and has no read endpoint. Including promotions needs a new tenants API (invariant #2/#3 territory) → OQ-1.

### 3. "Super admin" in a tenant deployment

- Admin compares `$_SESSION['admin_roles']['code']` with env `super_admin_role_id` [EV `sc-saas-admin/config/config.php:268–269`], whose value is `"super_admin"` [EV `sc-saas-admin/.env:36`]. So a tenant super admin = `spa_admin_users.role → spa_admin_roles.code = 'super_admin'`. The backend has no such env; it would query the role code directly. [INFERRED]
- There is no "designated senior admin" concept anywhere [EV grep: no `escalat` match in admin or backend].
- "SanchiConnect super admin" (a platform operator outside the tenant) has no address the tenant backend knows. → OQ-2.

### 4. Admin has no stored notifications

The admin bell is computed on page load from live queries [EV `notification_centre_functions.php:305`]; there is no admin-notifications table. The only push channel to an admin today is **email** — e.g. `sendTicketAllotmentEmail()` [EV `core/services/ses-email.service.ts:4584`], template `TICKET_ALLOTMENT` from `spa_email_templates`.

### 5. Cron

Same in-process pattern as SAN-1472 §3: `CronJobName` + seed in `modules/cron/repository/cron-job.repository.ts` (inactive by default) + `case` in `CronService.setCronJobs()` wrapped by `runCronJob()` [EV `modules/cron/cron.service.ts:732` for `EVENT_REMINDER`]. Master switch `cron_enabled`. Schema via `synchronize: true` [EV `core/database/database.module.ts:32`].

## Proposed design (every **[DDP]** was decided as written — see Open questions, resolved 2026-10-08)

**P-1 — Rules** [DDP → OQ-1, OQ-3]

| Rule | Selects | Fires when |
|---|---|---|
| `outreach_overdue` | `partner_broadcast_requests` `status='pending'`, `target_scope='hub'`, `deleted_at IS NULL` | `created_at ≤ NOW() − sla_outreach_decision_hours` (past SLA, same as admin's Overdue chip) |
| `grievance_ack` | `tickets` `ticket_category='grievance'`, `ticket_status='open'`, `acknowledged_at IS NULL` | age ≥ **80 %** of `sla_grievance_ack_hours` (24 h → 19 h 12 m) |
| `grievance_resolve` | `tickets` `ticket_category='grievance'`, `ticket_status='open'` | age ≥ **80 %** of `sla_grievance_resolve_days` (7 d → 5 d 14 h 24 m) |

- SLA values are read from `spa_settings` each run; missing/invalid → the admin defaults (48 / 24 / 7), floor 1 — same as `notifCentreSetting()` + `max(1, …)` in admin.
- `awaiting_user` and `closed` tickets never escalate. Feedback tickets never escalate (EX-11 names grievances only).
- `program_promotions` excluded (OQ-1).

**P-2 — Recipients** [DDP → OQ-2]
- New `spa_settings` key `escalation_admin_ids` (comma-separated `spa_admin_users.id`, default empty), seeded by admin's `notifCentreSettingDefaults()` so it appears on the existing settings page — the "designated senior admin(s)".
- Empty or no valid ids → fall back to every admin user whose role `code = 'super_admin'`.
- Nobody resolvable → log `warn`, claim nothing (retry next run).
- Platform-level SanchiConnect operators are out of scope (no address in a tenant deployment).

**P-3 — Channel: email** [DDP → OQ-4]
- One **digest** email per recipient per rule-group per run (outreach / grievance), listing every item escalated in that run: title, ticket number or requesting partner, age, SLA, assigned admins (tickets), link to the admin page. Avoids one email per item when a backlog first trips.
- Two new `EmailTemplateCode`s `OUTREACH_ESCALATION = 'outreach-escalation'`, `GRIEVANCE_ESCALATION = 'grievance-escalation'`, seeded into `spa_email_templates` by the backend if absent (FA-010 precedent), editable by admins afterwards.
- No in-app, WhatsApp or admin-bell change.

**P-4 — Exactly once per item per rule** [technical → OQ-5, dev lead]
- Nullable `datetime` markers: `partner_broadcast_requests.escalated_at`; `tickets.ack_escalated_at`, `tickets.resolve_escalated_for` (see Implementation notes). Precedent: SAN-1472 `reminder_*_sent_for`.
- Claim before send: `UPDATE … SET <marker> = NOW() WHERE id = :id AND <marker> IS NULL` → send only when `affected = 1`. Safe under overlapping runs / multiple processes.
- **Reopen re-arms:** when a grievance is reopened (`reopened_at` > marker), the resolve rule is measured from `reopened_at` and fires again. [DDP → OQ-3]
- Email failure after claim → that escalation is lost (at-most-once), logged `error`. Same trade-off as SAN-1472 OQ-10.
- Admin's Medoo inserts/updates don't name the new columns → stay NULL. Backend must deploy before the cron row is switched on.

**P-5 — Cron job**
- `CronJobName.ESCALATION_RULES = 'escalationRules'`, seeded `*/15 * * * *`, **inactive**; `case` in `setCronJobs()` via `runCronJob()`.
- `modules/cron/escalation-rules.service.ts` → `EscalationRulesService.runEscalations()`:
  1. Return unless `saasFeatures[Feature.NOTIFICATION_CENTRE_ENABLED] === true`.
  2. Resolve recipients (P-2); none → warn + return.
  3. Per rule: select due rows (bounded `LIMIT 200`), claim each (P-4), collect claimed items.
  4. One digest per recipient per group (P-3). Each step isolated in try/catch.

## Acceptance criteria

- [ ] With the flag on and the cron row active, a hub `partner_broadcast_requests` row pending longer than `sla_outreach_decision_hours` triggers exactly one outreach escalation email per recipient; a second run sends nothing for it.
- [ ] `self`-scope, approved, rejected, sent or soft-deleted broadcast requests never escalate.
- [ ] An open, unacknowledged grievance escalates once at ≥ 80 % of the ack SLA; acknowledging it before that point prevents it.
- [ ] An open grievance escalates once at ≥ 80 % of the resolve SLA, whether or not acknowledged; closed / awaiting_user / feedback tickets never escalate.
- [ ] A reopened grievance can escalate on the resolve rule again, timed from `reopened_at`.
- [ ] Changing an SLA key in `spa_settings` takes effect on the next run with no deploy.
- [ ] Recipients = `escalation_admin_ids` when set, else every `super_admin`-role admin; nobody resolvable → nothing claimed, `warn` logged.
- [ ] Flag `notification_centre_enabled` off, `cron_enabled` off, or the cron row inactive → nothing happens.
- [ ] Two concurrent runs never send the same escalation twice.
- [ ] The new `escalation_admin_ids` key appears on the admin settings page with the other notification-centre keys.

## Per-repo plan

### backend (`sc-saas-backend`)

- `core/constants/enum.ts`: `CronJobName.ESCALATION_RULES`; `EmailTemplateCode.OUTREACH_ESCALATION`, `GRIEVANCE_ESCALATION`; `EscalationRule` enum.
- Entities: `escalatedAt` on `PartnerBroadcastRequestsEntity`; `ackEscalatedAt`, `resolveEscalatedFor` on `TicketsEntity`.
- `modules/cron/escalation-rules.service.ts` (+ repository with the three due-row queries and the claim UPDATE); register in `cron.module.ts`, seed in `cron-job.repository.ts`, `case` in `cron.service.ts`.
- `core/services/ses-email.service.ts`: `sendOutreachEscalationEmail()`, `sendGrievanceEscalationEmail()`; template seeding in `spa_email_templates.repository.ts`.
- Module specs: `modules/cron/module.spec.md`, `modules/tickets/module.spec.md`.
- Jest: rule thresholds at the edges, every exclusion filter, SLA parsing fallbacks, recipient resolution (ids, fallback, none), claim race, reopen re-arm, flag off, digest grouping, failure isolation.

### admin (`sc-saas-admin`)

- `includes/notification_centre_functions.php` `notifCentreSettingDefaults()`: add `escalation_admin_ids` (textfield, empty, info "Admin user IDs (comma-separated) who receive SLA escalations; empty = all super admins"). No other admin change; the cron row is enabled through the existing generic `cron_jobs` page.

### tenants / frontend / tenants-admin / 3rdparty-webservices / ai-startups-analyzer

No change under the recommended defaults. tenants only if OQ-1 includes `program_promotions`. 3rdparty-webservices is reached through the existing generic email path.

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| Flags (#1) | None; consumes `notification_centre_enabled`, `cron_enabled` | `/trace-flag notification_centre_enabled` |
| Backend API (#2) | No route / DTO change | `/audit-contract` (expect clean) |
| Shared tenant DB with admin | 3 additive nullable columns on `partner_broadcast_requests` / `tickets`; 1 new `spa_settings` row; 2 new `spa_email_templates` rows | deploy backend first |
| Tenant scoping (#5) | One deployment = one tenant; every query on its own DB; no cross-tenant host | `/check-isolation` |
| Auth (#4), verification (#3), PowerPitch (#6) | Not touched | — |

## Test plan

No "guardian" skill exists in this workspace — say so in the commit. Backend jest as above + `npm run build` + `npm run lint`. Admin: `php -l`. Manual on a dev tenant: back-date a hub broadcast request and two grievances, enable the row, observe one digest each, rerun → silence; acknowledge / close → silence; reopen → resolve rule fires again.

## Rollout

1. backend (columns, templates, cron seeded inactive) → 2. admin (setting seed) → 3. per tenant: set `escalation_admin_ids` (optional), `cron_jobs.active = 1` for `escalationRules`, re-arm via `PATCH saas/settings` or restart.

## Out of scope

- `program_promotions` escalation (unless OQ-1), platform-level operator escalation, multi-level escalation chains, in-app/WhatsApp escalation, an "Escalated" chip in admin lists, escalating feedback tickets or other queues.

## Open questions

None. All six were resolved by Mahima on 2026-10-08 by accepting every recommended default:

| OQ | Decision |
|---|---|
| OQ-1 Outreach scope | Hub `partner_broadcast_requests` only; `program_promotions` not escalated |
| OQ-2 Recipients | New `escalation_admin_ids` setting; empty → every tenant `super_admin` admin |
| OQ-3 Nearing breach | 80 % of both ack and resolve SLAs, fixed; reopen re-arms the resolve rule |
| OQ-4 Channel | Email digest per recipient per run; no in-app |
| OQ-5 Idempotency | Nullable marker columns + atomic conditional UPDATE |
| OQ-6 Cadence | `*/15 * * * *` |

## Implementation notes (2026-10-08)

Built on `ai_native_setup_mahima` in `sc-saas-backend` and `sc-saas-admin` (the branch both repos were already on; SAN-1472 was built there too). Nothing is committed. Every OQ decision was implemented as written. Deviations and additions:

- **Reopen re-arm (P-4).** The design said "resolve measured from `reopened_at`". Admin writes `reopened_at` with PHP `date()` in the app timezone [EV `sc-saas-admin/modules/tickets/detail.php:206`, `includes/core_functions.php:60`], while `NOW()` is MySQL's session clock, so comparing them could be hours off. Instead:
  - the resolve marker is `tickets.resolve_escalated_for` (`datetime(6)`). It stores the cycle start it escalated, `COALESCE(reopened_at, created_at)`;
  - it re-arms when that value changes, which is a value match, not a time comparison;
  - age is always measured from `created_at`, the same base as admin's Overdue flag.

  Effect: a reopened grievance that is already past 80 % of the resolve SLA escalates again on the next run.
- **Claims re-check eligibility.** Each claim UPDATE repeats the rule's filters (still pending / open / unacknowledged), so an item acted on between select and claim is not escalated. It also sets `modified_at = modified_at`.
- **Encrypted settings.** The backend does not decrypt `spa_settings` (nor does `getBrandDetails()`). SLA values must be whole digits; anything else (e.g. ciphertext under admin `encrypt_settings`) falls back to the default, and `escalation_admin_ids` falls back to super admins.
- **Templates.** Each list is one `{{#each items}}` inside a single `<td>` (the admin template editor strips block helpers placed between table rows; see `modules/global/module.spec.md`). Seeded only when missing, like every other template. Rendered with Handlebars, so values are HTML-escaped.
- **Admin seeding.** `ensureNotificationCentreSettings()` runs once per admin session, so `escalation_admin_ids` appears after an admin's next login.
- **Verification.**
  - Backend: `tsc --noEmit` clean, `npm run build` passes, 42 new jest tests pass (`modules/cron/escalation-rules.service.spec.ts`, `modules/global/admin/spa_email_templates.repository.escalation.spec.ts`). The cron / global / notifications / tickets suites pass, apart from 2 failures in `global-onboarding-design.spec.ts` that also fail without these changes. ESLint is clean on changed lines; 4 prettier errors in `ses-email.service.ts` predate this change.
  - Admin: `php -l` clean.
  - No "guardian" skill exists, so the jest suite is the automated coverage.
  - The SQL has not been run against MySQL (no local DB). Still pending: the manual dev-tenant run from the Test plan and an `EXPLAIN` of the due-row queries. No index was added.
- **Gates (checked inline).**
  - `/check-isolation`: no hardcoded host and no cross-tenant state; every query runs on this deployment's DB. The `partners` join is in the same tenant DB.
  - `/audit-contract`: no route or DTO change.
  - `/trace-flag`: `notification_centre_enabled` and `cron_enabled` are consumed unchanged.
- **Auth model.** No route was added. The job runs in-process, with no HTTP surface.

## Linear tracking

- **Issue:** SAN-1475 (project "Enhancement", assignee Mahima Sharma, Done 2026-10-08; summary comment added). No sub-issues: backend + a one-line admin seed.
