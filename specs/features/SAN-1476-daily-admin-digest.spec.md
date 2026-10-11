---
id: SAN-1476
title: "Notifications Phase 2 — EX-12 Daily admin digest (9:00 IST email)"
type: feature
status: in-review               # approved 2026-10-08 (all OQs resolved by Mahima); implemented 2026-10-08; manual dev-tenant run pending
linear: https://linear.app/sanchiconnect/issue/SAN-1476/notifications-p2-ex-12-daily-admin-digest-900-ist   # project "Enhancement"
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-12 (W-08 annotation 4), Phase 2"
repos: [backend, admin]         # dependency order (recommended design D-1)
contracts:
  api:
    - "NEW admin endpoint (recommended D-1): POST {adminUrl}/notifications/digest — called by the backend cron only; auth = per-tenant shared secret (OQ-3)"
    - "No backend route changes"
  flags:
    - notification_centre_enabled   # EXISTING — gate
    - cron_enabled                  # EXISTING — master cron switch
  events:
    - "cron_jobs — ONE new CronJobName `ADMIN_DAILY_DIGEST` (seeded INACTIVE, `0 9 * * *` Asia/Kolkata)"
    - "spa_settings — new keys (OQ-2): `admin_digest_enabled`, `admin_digest_opt_out_ids` (and the shared secret per OQ-3)"
    - "spa_email_templates — ONE new template `admin-daily-digest` (rendered and sent by the backend via SES; see Implementation notes)"
tenant_scoped: true
depends_on: [SAN-1381, SAN-1475]   # Phase 1 admin counters; SAN-1475 escalation cron pattern
created: 2026-10-08
---

# Notifications Phase 2 — EX-12 Daily admin digest

## Reference
- **BRD:** EX-12, Phase 2 (W-08 annotation 4). The BRD itself isn't in the workspace. The only source text is Linear SAN-1476:
  > A 9:00 IST email summarising pending queues, new applicants by persona and items at risk, so admins can plan before logging in.
- **Builds on:**
  - `SAN-1381` Phase 1: the admin counters, per-permission queues and SLA keys.
  - `SAN-1475`: the backend cron and email pattern.
  - `sc-saas-admin/modules/command_centre.module.spec.md`.
- **Tags:** [EV] = evidenced in the code; [INFERRED] = drawn from the code but not stated anywhere; [DDP] = design decision pending.

## Problem
Admins learn what's waiting only once they open the admin panel: the bell, the sidebar badges and the command centre. EX-12 asks for a morning email, so they can plan before they log in.

## Current state (checked 2026-10-08)
1. **Everything the digest needs is already computed by admin.** `getAdminNotificationCounters($database, $mainDatabase, $admin, $brandSettings, $menus)` [EV `sc-saas-admin/includes/notification_centre_functions.php:307`] returns, per admin:
   - `queues[]`: outreach, ecosystem, engagements, tasks, support, platform feedbacks. Each queue has `count`, `oldest_age` and `overdue`. Support also has `feedback`, `grievance` and `awaiting_user`.
   - `ecosystem_personas` (pending applicants per persona).
   - `bell`.
   - It already applies **per-admin permissions** (NFR-06).
2. **Those counters depend on the admin's PHP session:**
   - the role code [EV :314, :543, :653]
   - `checkIsDevOrSuperAdminRole()` [EV `includes/core_functions.php:800`]
   - the role's permitted menus from `getMenus()`, which reads `$_SESSION['admin_roles']['menus']` [EV `core_functions.php:2105-2117`]
3. **Admin picks the tenant DB by request hostname** (`admin_domain = hostname`) [EV `sc-saas-admin/config/config.php:97`]. A CLI script would have to be told the host; an HTTP call to the tenant's admin URL selects the right DB automatically. [INFERRED]
4. **Admin has no scheduler of its own.** Its `cli/` scripts are one-off. The scheduler is the backend's in-process cron [EV `sc-saas-backend/src/modules/cron/cron.service.ts`], which knows this tenant's admin URL from `saasSettings[SaaSSettingKey.ADMIN_URL]`.
5. **The backend does not call admin today.** Admin calls the backend (`api_server_url` + adminToken) [EV `core_functions.php:6482…7173`]. A backend → admin call would be a **new direction** of traffic.
6. **Admin can send email itself:** `sendEmail($mail, $mailConnection, $data)` over SMTP [EV `core_functions.php:640`]. So can the backend, via SES (`SESEmailService`).

## Proposed design (recommended defaults; every [DDP] needs a decision)

**D-1. Where the digest is built** [DDP → OQ-1, dev lead]
- **Recommended:** the backend cron triggers it, and admin builds and sends it.
  - The backend cron `ADMIN_DAILY_DIGEST` (`0 9 * * *`, Asia/Kolkata, seeded inactive, gated on `notification_centre_enabled`) makes one `POST {adminUrl}/notifications/digest` to **this tenant's own** admin URL.
  - Admin then, for each eligible admin user, builds that admin's role context: the role row plus `getMenus` for that role, without a login session.
  - It calls the **same** `getAdminNotificationCounters()` and emails the digest.
  - So the digest equals the bell / command centre by construction.
- **Alternative B:** port every admin counter query and permission rule to the backend (TypeScript) and send via SES. That means no new endpoint, but there would be two copies of the counter and permission logic, which is exactly the drift NFR-03 / SAN-1460 just fixed.
- **Alternative C:** an admin CLI script run by a server crontab with `--host`. It needs an infra-level cron on the admin servers, which doesn't exist today.

**D-2. Who receives it and opt-out** [DDP → OQ-2]
- Every active admin user who has at least one permitted queue with a non-zero count.
- Partner and jury sessions are excluded, the same as the bell.
- New `spa_settings`:
  - `admin_digest_enabled` (default `1` once the cron row is active)
  - `admin_digest_opt_out_ids` (comma-separated admin ids)
- If every count is 0, **no email is sent**.

**D-3. Content** [DDP → OQ-4]
- Subject: `{brand} — {bell} items need your attention today`.
- Sections, each with a deep link into admin:
  1. **Pending queues:** count and oldest-item age.
  2. **New applicants by persona:** `ecosystem_personas` that are pending, plus how many arrived in the last 24 h.
  3. **Items at risk:** overdue outreach, grievances near or past SLA, and overdue tasks (the counters' `overdue` fields).
- One email per admin per day.
- Rendered from the new `admin-daily-digest` template in `spa_email_templates`, so admins can edit it.

**D-4. Auth model of the new endpoint** [DDP → OQ-3, dev lead; workspace guardrail: state it]
- The endpoint is `POST /notifications/digest` on admin.
- **Recommended auth:** an HMAC over the request time, using a per-tenant secret stored on both sides (backend saas settings + admin `spa_settings`, never in git). Requests are rejected if the signature is wrong or the timestamp is more than 5 minutes old.
- No admin session.
- Idempotent per IST day, through a `last_admin_digest_date` setting claim: a second call on the same day is a no-op.

**D-5. Delivery and failure**
- Each admin's email is isolated, so one failure doesn't stop the rest.
- Failures are logged in `spa_admin_logs`.
- At-most-once per admin per day.

## Acceptance criteria (draft)
- [ ] At 9:00 IST, with the flag on and the cron row active, each eligible admin gets one email showing exactly the queues and counts their bell shows at that moment.
- [ ] An admin without permission for a queue never sees it in the digest (NFR-06).
- [ ] Nothing pending → no email. An admin on the opt-out list → no email.
- [ ] A second trigger on the same IST day sends nothing.
- [ ] The endpoint rejects a missing or bad signature and a stale timestamp.
- [ ] Flag off / cron off / `admin_digest_enabled=0` → nothing is sent.

## Per-repo plan (recommended D-1)
- **backend:**
  - `CronJobName.ADMIN_DAILY_DIGEST` seed (inactive)
  - `modules/cron/admin-daily-digest.service.ts`: flag gate, build the signature, POST to `ADMIN_URL`, log the result
  - the secret in saas settings
  - jest tests
- **admin:**
  - `modules/notifications/digest.php`: signature check, day claim, build the context per admin, `getAdminNotificationCounters`, render the template, send
  - a helper that builds an admin's role/menus context without a session
  - the template seed
  - `spa_settings` defaults
  - the command_centre module spec
- **No change:** tenants, frontend.

## Cross-repo contract impact
- **New backend → admin HTTP call.** This is a new dependency direction, so it has to be recorded in the workspace CLAUDE.md blast-radius graph once approved.
- **New admin endpoint**, with the auth model per D-4.
- No flag changes. No backend API or DTO changes.

## Open questions

None. All four were resolved by Mahima on 2026-10-08, by accepting the recommended defaults:

| OQ | Decision |
|---|---|
| OQ-1 Architecture | A: the backend cron calls this tenant's own admin endpoint, and admin computes the counters with `getAdminNotificationCounters` |
| OQ-2 Recipients | All eligible admins with something pending; skip when empty; opt-out list `admin_digest_opt_out_ids` |
| OQ-3 Endpoint auth | HMAC-SHA256 of the timestamp, a per-tenant secret, and a 5-minute window |
| OQ-4 Content | The three BRD sections with deep links; email only; 09:00 IST daily, including weekends |

## Implementation notes (2026-10-08)

Uncommitted, on `ai_native_setup_mahima`, in sc-saas-backend and sc-saas-admin.

- **Who sends (deviation from D-1/D-3):** admin **computes and returns** each admin's digest data, and the **backend renders and sends** it through SES. Admin does not send it over SMTP. The backend's SES path has the email queue and email logs, and admin SMTP depends on a per-tenant `spa_email_settings` default that may not be configured. Everything else is as designed.
- **Admin side:** `modules/notifications/digest.php`, a POST endpoint with no session and a JSON response.
  - It checks: the flag → the secret is present → ts within 5 minutes → `hash_equals` on the HMAC → `admin_digest_enabled` → the claim on `admin_digest_last_date` (one conditional UPDATE per IST day).
  - It then closes the PHP session (`session_write_close`), so nothing it does can persist into a session.
  - For each admin user (skipping the jury and recruitment-partner roles, opt-outs, and admins with no email), it builds that admin's role context (`admin_roles` + `getMenus`) and calls `getAdminNotificationCounters`.
  - It returns the action queues with a non-zero count, the ecosystem personas (pending, plus new in the last 24 h), and the overdue queues as "at risk". Admins with nothing pending are left out.
- **The secret** lives in **one** place: `spa_settings.admin_digest_secret` in the shared tenant DB.
  - Admin generates it (`bin2hex(random_bytes(32))`) the first time `ensureNotificationCentreSettings` runs, so it is never in git.
  - Both sides key the HMAC with the raw stored value, so it works the same under `encrypt_settings`.
  - Rotate it by deleting the row.
  - Until an admin with the flag on has logged in once, the row doesn't exist and the backend logs a warning and skips.
- **Backend side:** `modules/cron/admin-daily-digest.service.ts`, cron `adminDailyDigest` at `0 9 * * *` (Asia/Kolkata), seeded inactive.
  - It POSTs `{ts, sig}` to `{adminUrl}/notifications/digest` (axios, 120 s timeout).
  - It sends one `admin-daily-digest` email per returned admin, each in its own try/catch.
  - `sendEscalationDigestEmail` (SAN-1475) is reused with the new template code.
- **New `spa_settings` keys:**
  - `admin_digest_enabled` (default 1)
  - `admin_digest_opt_out_ids`
  - `admin_digest_secret` (generated)
  - `admin_digest_last_date` (internal claim)
- **Verification:**
  - Backend jest: cron + global admin suites 289/289, including the new `admin-daily-digest.service.spec.ts` (gate, no secret, signed URL, one email per admin, isolation, already sent / disabled, endpoint error, template render, cron seed and registration). `tsc` is clean.
  - Admin: `php -l` is clean. `digest.php` was run under a PHP CLI harness with a fake DB: bad signature → 401; stale ts → 401; a valid call returns only the eligible admin, with juror, opt-out, empty and orange queues excluded; a second call on the same day → `alreadySent`.
  - Cross-language HMAC check: PHP `hash_hmac` equals Node `createHmac`.
  - Not run: a real dev-tenant run (admin URL reachability from the backend, real SES send).
- **Cross-repo:** a **new backend → admin call direction**. It should be added to the workspace CLAUDE.md blast-radius graph. That is left for the dev lead, because CLAUDE.md is the workspace constitution.

## Linear tracking

- SAN-1476 (project Enhancement, assignee Mahima Sharma).
