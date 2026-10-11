---
id: SAN-1028                    # Linear Project P-SAN-63 (team: Sanchiconnect); anchored to its lowest-numbered
                                 # per-repo issue, SAN-1028 (tenants). Full issue set: SAN-1028 (tenants),
                                 # SAN-1029 (tenants-admin), SAN-1030 (backend), SAN-1031 (admin).
title: ZenxAI Voice Calls for Draft Applications
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/project/zenxai-voice-calls-for-draft-applications-5fbb3554def5
owner: nirmal.s@sanchiconnect.com
repos: [tenants, sanchiconnect-saas-tenants-admin, backend, admin]
contracts:
  api:
    - "NONE on the sc-saas-backend API contract (invariant #2). Backend only gains TypeORM entities (it is the tenant-DB schema owner). No new backend route in v1."
    - "EXTERNAL, consumed (not owned) from sc-saas-admin: POST https://crm.zenxai.io/api/public/v1/assistants/{assistant_id}/calls — start one outbound AI voice call (202 queued) [evidence: ZenxAI docs 'Sanchi Developer: Voice API', generated 2026-09-28, supplied by user]"
    - "EXTERNAL, consumed: GET https://crm.zenxai.io/api/public/v1/calls/{call_id} — poll call state/result [same evidence]"
    - "EXTERNAL, consumed: POST https://crm.zenxai.io/api/public/v1/calls/{call_id}/cancel — cancel while queued/retry_scheduled [same evidence]"
    - "NO inbound endpoint in v1 (polling only). ZenxAI outbound webhooks (X-ZenX-Signature HMAC) are a documented FUTURE phase — see 'Future phase: webhooks'."
  flags:
    - "zenxai_crm_enabled"
  events: []
tenant_scoped: true
depends_on: []
created: 2026-09-28
---

# ZenxAI Voice Calls for Draft Applications

## Problem

Custom-program ("Call for Applications") draft applications — `forms_submissions` rows an
applicant started but never submitted — are dead-ends in `sc-saas-admin`: the Draft Applications
page (`/application_management/draft_applications/{programId}/{slug}`) only offers Update
Percentage, Download CSV and Send Bulk Email. There is no way to follow up with those applicants
by phone. The customer uses ZenxAI, which exposes a **Voice API**: one API request places one
outbound call from a configured AI voice assistant to a phone number, and the call's status,
duration, summary, collected answers and recording can then be read back. This feature lets a
tenant admin place ZenxAI calls to draft applicants and see, per applicant, what happened on the
call (answered / no answer / busy / failed, outcome summary, call time, duration, etc.).

## Requirements (user-confirmed intent, restated against the ZenxAI Voice API docs)

The user's original wording was "send leads to ZenxAI" and "get the lead responses". The ZenxAI
Voice API has no create-lead endpoint: **one request places one AI voice call** to a phone number,
and the call's outcome is read back afterwards. The requirements below express the same intent
in the API's real terms. Each maps to a documented endpoint or field.

| # | Requirement | ZenxAI API basis |
|---|---|---|
| R1 | **"ZenxAI Dashboard"** action in the Draft Applications page header, next to Update Percentage / Download CSV / Send Bulk Email. Visible only when the tenant flag `zenxai_crm_enabled` is on, ZenxAI is configured (`.env`), and the admin has `can_broadcast_messages` (Q6). Shown when the program has current drafts OR past ZenxAI calls (Q5). | — |
| R2 | **Sync = place calls.** Sync places one ZenxAI call per eligible draft applicant, either all eligible drafts or only the selected ones. A confirmation first shows the count and warns that real calls will be placed and the ZenxAI wallet charged. | `POST /assistants/{assistant_id}/calls` → `202 {call_id, status:"queued"}` |
| R3 | **Scope: DRAFT applications of this program only.** These are `forms_submissions` rows with the program's `form_id`, `submitted=0`, `status=1`, `deleted_at IS NULL`. | — |
| R4 | **Data sent: name, email, phone, company_name only.** Phone goes as `phone` in E.164 (`+{country_code}{mobile_number}`). Name, email and company go in `metadata` because the assistant has no Call Data inputs. The submission id goes as `reference`. `inputs` is `{}`. | Request body `phone` (required), `reference`, `metadata` (< 4 KB), `inputs` |
| R5 | **Each applicant is called at most once per Sync, and a retried request never dials twice.** Drafts with a pending (`queued`/`dialing`/`retry_scheduled`) or `completed` call are skipped. Every request carries a deterministic `Idempotency-Key`. | `Idempotency-Key` header; replay → `200`, conflict → `409 idempotency_conflict` |
| R6 | **Dashboard shows the call response for every applicant called.** It shows the latest call per applicant, with earlier calls expandable. | `GET /calls/{call_id}` |
| R6a | Call status, which gives *received / not received*: `queued`, `dialing`, `retry_scheduled` (in progress); `completed` (answered); `no_answer`, `busy`, `failed`, `cancelled` (not connected). | `status` |
| R6b | Call response/outcome: AI `summary`, `collected_data` (Full Name, Email ID, Phone Number, Product Enquiry — each with the value and what was heard), `ended_reason`, `failure_reason`. | `summary`, `collected_data`, `ended_reason`, `failure_reason` |
| R6c | Call timing: called at, ended at, duration, attempts, next retry time. | `created_at`, `ended_at`, `duration_sec`, `attempts`, `next_retry_at` |
| R6d | Recording link. Shown only to admins with `can_broadcast_messages` (Q6). | `recording_url` |
| R6e | ZenxAI lead id, when one exists (currently always null; see Q-A). | `lead_id` |
| R7 | **Refresh** updates call results by polling: per row, plus "Refresh all non-final" for in-progress calls. No webhook in v1. | `GET /calls/{call_id}` |
| R8 | **Cancel** a call that hasn't started yet. | `POST /calls/{call_id}/cancel`, only while `queued`/`retry_scheduled`; else `409 not_cancellable` |
| R9 | **Call again** for an applicant whose last call did not connect. ZenxAI retries are off, so a new call is placed. Allowed only when the latest call is `no_answer`/`busy`/`failed`/`cancelled`, the submission is still a draft, and it has fewer than 3 calls (Q5). | "Retries are off. Start a new call to try again." |
| R10 | **One shared ZenxAI account for all tenants (Q4, v1).** The base URL, assistant id and API key are platform-level values in the `sc-saas-admin` `.env`. There's no per-tenant settings page in v1. The key never appears in any UI, log, DB row or response. Each tenant's access is switched on or off by the `zenxai_crm_enabled` flag. | `Authorization: Bearer zxk_live_…`; one key is bound to one assistant (`403 forbidden`) |
| R11 | **Clear, specific error messages.** 401 → "API key invalid". 402 → "ZenxAI wallet empty". 403 `api_disabled` → "ZenxAI API is turned off". 400 `invalid_phone` → the row is marked invalid phone. 429 → wait for `Retry-After` and continue. On 401, 402 or 403 the whole Sync run stops. | Errors table, `{error:{code,message}}` |
| R12 | **Stay under 60 requests/min** across calls, refreshes and cancels. | Rate limit 60/min |

**Not possible with the current ZenxAI configuration (needs the account owner):**
- **Leads created in ZenxAI.** `lead_id` is always null because "Save as Enquiry" is off. Calls are
  placed, but no ZenxAI lead or enquiry exists until it is turned on (Q-A).
- **Addressing the applicant by name or company during the call.** The assistant has no Call Data
  fields, so `inputs` must be `{}` (Q-B).
- **Real-time status updates.** No webhook URL is set on the assistant, so v1 polls. See "Future
  phase: webhooks".

## ZenxAI Voice API facts (evidence-tagged)

All from **[evidence: ZenxAI docs "Sanchi Developer: Voice API", generated 2026-09-28, supplied by
the user]** unless noted.

- **Base URL:** `https://crm.zenxai.io/api/public/v1`.
- **Start call:** `POST /assistants/{assistant_id}/calls`. Assistant id for the requesting account:
  `31ac12eb-b10d-4ca4-b78b-c661d44bd944`. One API key is bound to one assistant (other assistant →
  `403 forbidden`). **One request = one real phone call, and every call costs wallet balance.**
- **Auth:** `Authorization: Bearer zxk_live_…`. Server-side only; rotating the key invalidates the
  old one immediately. The key is **obtained from the ZenxAI account owner** and is never written
  into code, specs, logs, or git.
- **Rate limit:** 60 requests/min → `429 rate_limited` with `Retry-After`.
- **Request body:** `phone` (required; E.164 e.g. `+919876543210`, or a 10-digit Indian number);
  `inputs` (object — this assistant has **no Call Data fields**, so send `{}` or omit);
  `reference` (string, echoed back); `metadata` (object, < 4 KB, echoed back).
  Optional header **`Idempotency-Key`**: replay of the same key → `200` with the original call;
  same key + different phone → `409 idempotency_conflict`.
- **Response `202`:** `{call_id, status:"queued", assistant_id, phone, reference, metadata, inputs,
  attempts, next_retry_at, duration_sec, ended_reason, failure_reason, collected_data, summary,
  recording_url, lead_id, created_at, ended_at}`.
- **`GET /calls/{call_id}`** returns the same shape. **`POST /calls/{call_id}/cancel`** only while
  `queued`/`retry_scheduled`, otherwise `409 not_cancellable`.
- **Statuses:** non-final `queued`, `dialing`, `retry_scheduled`; final `completed`, `no_answer`,
  `busy`, `failed`, `cancelled`.
- **Results:** `collected_data` keyed fields `{label, value, heard}` — for this assistant
  `full_name`, `email`, `phone`, `product_enquiry` (enum); `summary` (text), `duration_sec`,
  `ended_reason`, `failure_reason`, `recording_url`.
- **`lead_id` is always `null`** for this assistant because "Save as Enquiry" is OFF — no ZenxAI
  lead is created unless the account owner turns it on (Q-A).
- **Retries are off** on the ZenxAI side ("start a new call to try again").
- **Calling hours are enforced by ZenxAI** — outside allowed hours a call simply stays `queued`;
  we don't need our own calling-hours logic.
- **Errors:** `{error:{code,message}}` — `400 invalid_phone | invalid_input`, `401 invalid_api_key`,
  `402 insufficient_balance` (wallet empty), `403 api_disabled | forbidden`, `404 not_found`,
  `409 idempotency_conflict | not_cancellable`, `429 rate_limited`. If the API is turned off,
  queued calls are cancelled.
- **Webhooks:** none configured for this assistant. Available if the owner sets a URL (events
  `call.queued/dialing/retry_scheduled/completed/no_answer/busy/failed/cancelled/analysis_ready`,
  `X-ZenX-Signature` HMAC). **Not used in v1** — see "Future phase: webhooks".
- **[unverified]** Whether `GET /calls/{id}` and `/cancel` count against the same 60/min limit.
  The design assumes they do.

## Code findings (evidence-tagged)

- **[verified: `sc-saas-admin/index.php:58-76`]** Routing is file-based: `action` is split on `/`
  and the first existing `modules/<prefix>.php` is included. A new
  `modules/application_management/zenxai_dashboard.php` is served at
  `/application_management/zenxai_dashboard/{programId}/{slug}` and, like
  `draft_applications.php:22`, reads the program id from `$vars[2]`.
- **[verified: `sc-saas-admin/modules/application_management/draft_applications.php:22,523-526,538-544`]**
  Draft rows = `forms_submissions` where `form_id = application_programs.form_id`,
  `submitted = 0`, `status = 1`, `deleted_at IS NULL`. Columns include `id, name, email, user_id,
  account_type, company_name, country_code, mobile_number`. When `user_id` is set and
  `account_type` is non-empty, `name`/`email` are overridden from `users` (lines 540-544). The
  sync applies the same override so ZenxAI receives what the admin sees.
- **[verified: `sc-saas-backend/src/modules/form-management/entities/form-submissions.entity.ts:55-58`]**
  `country_code` is an **int** column (no `+`), `mobile_number` is varchar → phone is composed as
  `"+" . country_code . mobile_number` and validated as E.164 before sending.
- **[verified: `sc-saas-admin/themes/default/html/application_management/draft_applications.php:66-87`]**
  All header buttons sit inside `if(count($this->records) > 0)` and are each individually gated
  (`checkRole("is_dev")`, `$this->canExportData`, `$this->canbroadCastMessage`).
- **[verified: `sc-saas-admin/modules/common.php:527-546`, `includes/core_functions.php:1979-1986`]**
  Per-admin permissions are boolean columns on the tenant-DB `spa_admin_users` row
  (`can_broadcast_messages`, `can_import_data`, `can_export_data`, `moderate_meeting_settings`).
  Partners (`$_SESSION["partner_id"]`) get import/export automatically, but NOT
  `can_broadcast_messages`, so partner admins don't get ZenxAI access (Q6).
- **[verified: grep across all 7 repos, 2026-09-28]** `spa_admin_users` has no schema owner: there's
  no TypeORM entity and no migration. Admin reads it with `get("spa_admin_users", "*")`
  (`core_functions.php:1983`). A new permission column would need an unowned manual `ALTER` on every
  tenant DB. This is why Q6 reuses an existing column.
- **[verified: `sc-saas-admin/config/config.php:66-72,139-141`]** Admin reads the whole
  `tenant_users` row (`"*"`) directly from the main DB by `admin_domain`/`admin_custom_domain`,
  then `define('zoho_service_enabled', ...)`. A new flag therefore reaches admin with NO change to
  the tenants API field lists. `$brandSettings` (`common.php:481`) also exposes it.
- **[verified: `sanchiconnect-saas-tenants/src/modules/global/global.service.ts:726-803`]**
  `getTenantSettings()` uses a hand-maintained `select` list. Because v1 has no backend route or
  frontend UI gated on this flag, it is **deliberately NOT added** to `getTenantSettings()` /
  `verify_tenant()`. That also follows the tenants guardrail against widening the public
  `verify_tenant` response.
- **[verified: `sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-users.entity.ts:627-632`]**
  Pattern flag: `zoho_service_enabled` boolean, default false.
- **[verified: `sanchiconnect-saas-tenants-admin/modules/tenant_management/_switch_sections.php:22-188`]**
  Operators toggle tenant flags through the hand-maintained `getTenantSwitchSections()` list used
  by `create.php:19-22`/`edit.php:34-37`/`detail.php:40`. `zoho_service_enabled` is in
  "Integrations & Advanced" (line 185). A new flag must be listed here to be toggleable.
- **[verified: `sc-saas-backend/src/core/database/database.module.ts:25-32`, `core/zoho/zoho.module.ts:28-34`]**
  Tenant-DB schemas are owned by backend TypeORM entities with `synchronize: true`
  unconditionally (prod included), `autoLoadEntities: true` + `TypeOrmModule.forFeature([...])`.
  New admin-used tables need backend entities (pattern: `ZohoSettingsEntity`, extends
  `AbstractEntityWithoutUUID`).
- **[verified: `sc-saas-admin/includes/core_functions.php:66-79`, `config/config.php:350`]**
  `encrypt($data)` / `decrypt($data)` — AES-256-CBC with `data_encrypt_key` from env. **Not needed in
  v1** (credentials are in `.env`, not the DB). It is the helper to use if a per-tenant settings
  table is added later. The plaintext pattern of `payment_gateways` / `zoho_settings`
  (`modules/zoho/settings.php:48`) must NOT be followed then.
- **[verified: `sc-saas-admin/modules/zoho/settings.php:1-9`]** Page-gating pattern to mirror for the dashboard:
  `checkLoggedIn()`, include `common.php` + `includes/<x>_functions.php`, redirect home if
  `constant("<flag>") == "0"`, `submitAction` POST handlers.
- **[verified: grep across workspace]** No existing ZenxAI code, config, or spec.

## Design (v1)

- **Sync = place calls.** The dashboard's primary action is labelled **"Call applicants via
  ZenxAI"** (tooltip "Sync"). Clicking it first computes the eligible count and shows a
  confirmation modal: *"This will place N real phone calls to applicants via ZenxAI. Each call is
  charged to the ZenxAI wallet. Continue?"* "Call selected" uses the same modal with the selected
  count.
- **Polling only.** No inbound endpoint. Results come from `GET /calls/{call_id}` via a per-row
  **Refresh** and a dashboard-level **"Refresh all non-final"**, batched and throttled like Sync.
  A cron poller is a possible later addition (out of scope for v1).
- **Eligibility / duplicate-call guard.** Sync (all or selected) skips any submission that already
  has a call that is non-final (`queued|dialing|retry_scheduled`) or `completed`. A row with only
  `no_answer|busy|failed|cancelled` calls is skipped by bulk Sync and can be re-called only through the row's
  **"Call again"**, with its own single-call confirmation. That requires the submission to still
  be a draft and to have fewer than **3** `zenxai_calls` rows, where `invalid_phone` rows (no call
  placed) don't count (Q5). "Call again" is never offered while a non-final call exists. There's
  no cooldown in v1.
- **Dashboard rows (Q5).** Current drafts of the program, UNION submissions of this program that
  have `zenxai_calls` rows but are no longer drafts (submitted or deleted). Those non-draft rows
  get a "Submitted" / "Removed" badge, their call history stays visible, and all call actions are
  disabled, though Refresh stays allowed for a non-final call.
- **Shared account (Q4 — decided 2026-09-28: single account now, business model later).** All
  tenants call through one ZenxAI account and assistant, so these are shared:
  - **Idempotency-Key namespace.** Program and submission ids are only unique within one tenant
    DB. Keys and references must therefore include the tenant id
    (`$getDatabaseSettingsFromMainTable["id"]`, the `tenant_users.id`). Otherwise tenant B's call
    could replay tenant A's call (200) or hit `409 idempotency_conflict`.
  - **Wallet.** One tenant's calls can empty it for everyone, and `402` stops Sync for all tenants.
  - **60/min rate limit.** Concurrent Syncs from different tenants share it, so the Retry-After
    handling must tolerate 429s caused by other tenants.
  - **Read access.** With the shared key, `GET /calls/{id}` could read any tenant's call. Isolation
    rule: admin only ever polls or cancels `call_id`s stored in the current tenant's own
    `zenxai_calls` table. No "list all calls" feature, ever.
  - **Attribution.** Every call carries `tenant_id` and `tenant_domain` in `metadata`, so usage can
    be split per tenant when billing is decided.
  - **Forward-compatible.** Credentials are read through one helper (`zenxaiConfig()`), so a later
    per-tenant settings table can override `.env` without touching call logic.
- **Idempotency-Key** = `sc-t{tenant_id}-p{program_id}-s{submission_id}-{n}`, where `n` = (count of existing
  `zenxai_calls` rows for that submission+program) + 1. A local `zenxai_calls` row with this key
  and `status='pending_send'` is inserted **before** the HTTP call (UNIQUE key = row-level claim).
  A retried or double-clicked request therefore reuses the same key, and ZenxAI returns the
  original call (200) instead of dialling twice.
- **Payload:**
  - `phone` = `"+" . country_code . mobile_number`, validated against E.164
    (`^\+[1-9]\d{7,14}$`) before sending. An invalid phone is recorded as a `zenxai_calls` row with
    `status='failed'`, `error_code='invalid_phone'` and no call placed.
  - `reference` = `"t{tenant_id}-s{submission_id}"`, which is unique across the shared account.
  - `metadata` = `{tenant_id, tenant_domain, program_id, submission_id, name, email, company_name}`. The four confirmed
    fields go here because the assistant has no Call Data inputs; must stay < 4 KB, so truncate
    long values.
  - `inputs` = `{}` (until Q-B).
- **Throttling:** client-driven AJAX batches of ≤ 20 requests, paced so total traffic (calls +
  polls + cancels) stays under 60/min. On `429`, honour `Retry-After` and resume. On
  `401 invalid_api_key`, `402 insufficient_balance`, or `403 api_disabled|forbidden`, **stop the
  whole run** and show the error ("API key invalid", "ZenxAI wallet empty", "API disabled"). Rows
  already claimed but not sent are released (row deleted or marked `failed` with that code).
- **Cancel:** per-row, only when `status in (queued, retry_scheduled)`; a `409 not_cancellable`
  triggers a refresh of that row.

## Acceptance criteria

- [ ] A new `zenxai_crm_enabled` boolean column (default `false`) exists on `TenantUsersEntity`,
      same shape as `zoho_service_enabled`.
- [ ] Operators can toggle it per tenant on tenants-admin Create/Edit Tenant ("Integrations &
      Advanced") and see it on Tenant Detail.
- [ ] `sc-saas-admin` defines `zenxai_crm_enabled` in `config/config.php`. With the flag off, the
      Draft Applications page is byte-identical to today, and every new ZenxAI page/AJAX action
      redirects home (pages) or returns a JSON error (AJAX).
- [ ] A backend entity creates `zenxai_calls` in each tenant DB on deploy; no existing table is
      altered. There is no `zenxai_settings` table in v1 (shared account, Q4).
- [ ] ZenxAI credentials are read only from the `sc-saas-admin` `.env` (`ZENXAI_BASE_URL`,
      default `https://crm.zenxai.io/api/public/v1`; `ZENXAI_ASSISTANT_ID`; `ZENXAI_API_KEY`)
      through `zenxaiConfig()`. If any is missing, the dashboard shows "ZenxAI is not configured"
      and every call action refuses. Key names are documented. The real key is never committed.
- [ ] Every Idempotency-Key and `reference` includes the tenant id, and `metadata` carries
      `tenant_id` + `tenant_domain`. Two tenants with identical program/submission ids never
      collide.
- [ ] With the flag on and ZenxAI configured, the Draft Applications header shows "ZenxAI
      Dashboard" (subject to `can_broadcast_messages`, Q6) linking to
      `/application_management/zenxai_dashboard/{programId}/{slug}`.
- [ ] The dashboard lists this program's draft applicants with: applicant, phone, email, company,
      call status badge, attempts, duration, ended_reason/failure_reason, summary, collected_data
      (expandable), recording link, called at / ended at, last refreshed. It shows the latest call
      per submission, with earlier calls expandable. Paginated.
- [ ] Sync / Call selected show the eligible count and the "real calls, wallet charged" warning
      before doing anything. Only drafts of this program (`submitted = 0, status = 1,
      deleted_at IS NULL`, program's `form_id`) are called, with the `users` override applied as
      in `draft_applications.php:540-544`.
- [ ] The duplicate-call guard holds: a submission with a non-final or `completed` call is never
      re-dialled by Sync. Double-clicking Sync or retrying a timed-out request places no second
      call (deterministic `Idempotency-Key` + pre-insert claim).
- [ ] An invalid phone is recorded as `failed/invalid_phone` without any HTTP call.
- [ ] Batches never exceed 60 req/min. `429` is retried after `Retry-After`. `401/402/403` stop the
      run with a clear message.
- [ ] Refresh / Refresh all non-final update rows from `GET /calls/{call_id}` (status, attempts,
      next_retry_at, duration, reasons, summary, collected_data, recording_url, lead_id, ended_at,
      last_polled_at). Final rows are not re-polled by "Refresh all".
- [ ] Cancel appears only for `queued`/`retry_scheduled` and works. "Call again" creates a new
      `zenxai_calls` row with `n+1` in the key.
- [ ] `recording_url`, `summary`, and `collected_data` are shown only to admins with
      `can_broadcast_messages` (Q6), and are not added to any CSV export.
- [ ] ZenxAI errors never leak PHP warnings into JSON responses (output-buffer flush pattern). The
      API key never appears in any response, log, DB column, or stored `request_payload`.
- [ ] No inbound/public endpoint is added in v1.
- [ ] No test or QA step dials a real applicant (see Test plan).
- [ ] New `sc-saas-admin` code uses `/* */` comments only (PHP and `<script>`), `count() > 0`
      array checks, deferred inline scripts; `php -l` clean on every touched file.

## Per-repo plan

### tenants (`sanchiconnect-saas-tenants`) — SAN-1028

- `src/modules/tenants/entities/tenant-users.entity.ts`: add
  `@Column({ type: 'boolean', name: 'zenxai_crm_enabled', width: 1, default: false }) zenxai_crm_enabled: boolean;`
  next to `zoho_service_enabled` (~line 627).
- No edit to `global.service.ts` `getTenantSettings()` / `verify_tenant()` field lists, because
  admin reads `tenant_users` directly and v1 has no backend/frontend gate.
- Update `src/modules/tenants/module.spec.md` flag list. Gate: `/trace-flag zenxai_crm_enabled`.

### sanchiconnect-saas-tenants-admin — SAN-1029

- `modules/tenant_management/_switch_sections.php:185`: add `"zenxai_crm_enabled"` after
  `"zoho_service_enabled"` in "Integrations & Advanced", and update the header comment counts
  (222/221 → 223/222).
- Update `modules/tenant_management/module.spec.md`. No schema change here.

### backend (`sc-saas-backend`) — SAN-1030

Schema owner only; no controller/DTO/route.

- New `src/core/zenxai/` (mirrors `src/core/zoho/`): `zenxai.module.ts` with
  `TypeOrmModule.forFeature([ZenxaiCallsEntity])`, imported in `app.module.ts`, plus
  `module.spec.md`.
- **No `zenxai_settings` entity in v1.** One shared account means credentials live in the admin
  `.env` (Q4). A per-tenant settings table is added only when the business model moves to
  per-tenant accounts.
- `entities/zenxai-calls.entity.ts` → `zenxai_calls`:
  - `id`, `submission_id` int (→ `forms_submissions.id`), `program_id` int
    (→ `application_programs.id`)
  - `call_id` varchar nullable **UNIQUE** (null until ZenxAI responds; invalid-phone rows stay
    null), `idempotency_key` varchar **UNIQUE**
  - `phone` varchar, `status` varchar (ZenxAI statuses + local `pending_send`)
  - `attempts` int, `next_retry_at` datetime nullable, `duration_sec` int nullable
  - `ended_reason` varchar nullable, `failure_reason` text nullable, `summary` TEXT nullable,
    `collected_data` JSON nullable, `recording_url` text nullable, `lead_id` varchar nullable
  - `request_payload` JSON (no auth header), `response_payload` JSON nullable
  - `error_code` varchar nullable, `error_message` text nullable
  - `zenx_created_at` datetime nullable, `zenx_ended_at` datetime nullable,
    `last_polled_at` datetime nullable
  - `created_by_admin_id` int nullable, `created_at` / `updated_at`
  - Index on (`program_id`, `submission_id`). Many rows per submission are allowed (re-calls).
  - These are brand-new tables, so no dedupe is needed before the UNIQUE constraints.
- Verification: `tsc --noEmit` / `npm run build`; on a dev tenant DB confirm the table and its
  indexes are created and nothing else changes.

### admin (`sc-saas-admin`) — SAN-1031

- `config/config.php`: add
  `if(!defined('zenxai_crm_enabled')){ define('zenxai_crm_enabled', $getDatabaseSettingsFromMainTable["zenxai_crm_enabled"]); }`
  next to line 139.
- `includes/zenxai_functions.php` (new):
  - `zenxaiConfig()` reads `$_ENV['ZENXAI_BASE_URL']` (default
    `https://crm.zenxai.io/api/public/v1`), `$_ENV['ZENXAI_ASSISTANT_ID']`, and
    `$_ENV['ZENXAI_API_KEY']` (loaded by Dotenv in `index.php:9`, same as the DB credentials).
    It returns null when any is missing. This is the single seam where a future per-tenant
    override plugs in.
  - `zenxaiTenantContext()` returns `tenant_id` (`$getDatabaseSettingsFromMainTable["id"]`) and
    `tenant_domain` (`hostname`), used in keys, references, and metadata.
  - `zenxaiBuildPhone($row)` (compose + E.164 validate), `zenxaiBuildCallPayload($row, $program)`
    (reference/metadata/inputs + `users` override)
  - `zenxaiNextIdempotencyKey($database, $tenantId, $programId, $submissionId)`
  - `zenxaiRequest($config, $method, $path, $body, $idempotencyKey)` (cURL with Bearer header,
    connect/total timeouts; returns HTTP code, parsed body, `Retry-After`)
  - `zenxaiStartCall(...)`, `zenxaiRefreshCall(...)`, `zenxaiCancelCall(...)` — each persists
    results to `zenxai_calls`
  - Uses only the per-tenant `$database`. Refresh and cancel only accept a `call_id` loaded
    from this tenant's `zenxai_calls`, never one taken from request input.
- **[verified: `git ls-files` in sc-saas-admin]** The repo tracks no `.env.example`. The three
  keys are added by hand to each deployment's `.env`, and documented (names only) in the
  `application_management` module spec and the admin CLAUDE.md env section. No settings page in v1.
- `modules/application_management/zenxai_dashboard.php` + template
  `themes/default/html/application_management/zenxai_dashboard.php`:
  - Loads the program by `$vars[2]` (404 like `draft_applications.php:22-26`); flag + permission
    gate.
  - Lists current drafts left-joined to the latest `zenxai_calls` row per submission for this
    program; earlier calls load on expand.
  - AJAX `submitAction`s:
    - `zenxaiCountEligible` — powers the confirmation modal
    - `zenxaiCallBatch` — ≤ 20 per request; the client loops, paces, and shows progress; stops on
      401/402/403
    - `zenxaiCallAgain`, `zenxaiRefresh`, `zenxaiRefreshNonFinalBatch`, `zenxaiCancel`
  - JSON responses flush output buffers first.
  - The whole page, and every AJAX action, requires `$canbroadCastMessage` (from `common.php`,
    which is `can_broadcast_messages`). Without it, pages redirect home and AJAX returns a JSON error.
- `themes/default/html/application_management/draft_applications.php:66-87`: add the "ZenxAI
  Dashboard" button next to the existing header buttons, gated on
  `constant("zenxai_crm_enabled") == "1"` + `$this->canbroadCastMessage`. It sits OUTSIDE the `count($this->records) > 0` block, rendered
  when there are drafts OR `zenxai_calls` rows exist for the program. The controller sets
  `$tpl->zenxaiHasCalls`.
- Module spec: update `modules/application_management/module.spec.md` (owns: ZenxAI pages;
  consumes: flag `zenxai_crm_enabled`, ZenxAI Voice API; tenant_scoping: per-tenant Medoo
  `$database`).
- Style: `/* */` only, `count() > 0`, deferred inline JS, `php -l` each file.

## Implementation notes (2026-09-28, spec-implementer)

All four repos implemented on `ai_native_setup`, uncommitted (user reviews diffs first). Gates run:
flag trace (consumers = tenants entity, tenants-admin switch list, sc-saas-admin config.php + ZenxAI
pages only; not in `verify_tenant`/`getTenantSettings()`, backend `Feature`, or frontend `IFeatures`),
contract audit (backend: `app.module.ts` import + schema-only `src/core/zenxai/`; no controller/DTO/route),
isolation review (admin: per-tenant `$database` only, no `$mainDatabase`, `call_id` never read from input).
No real ZenxAI request was made; verification was `php -l`, `tsc --noEmit` / `npm run build`, and a
scratch-only harness (SQLite + local mock of the 3 endpoints), not committed.

Choices made where the spec was silent or slightly off (none change a contract):
- `zenxai_calls` extends `AbstractEntityWithoutUUID`, so the timestamps are `created_at` /
  **`modified_at`** (not `updated_at`) plus a `deleted_at` soft-delete column.
- A claim released after 401/402/403 is **soft-deleted** (`deleted_at` set, `status=failed`, error code
  kept). `n` in the Idempotency-Key counts soft-deleted rows too, so a released key is never reused.
- Ambiguous outcomes (network error, 5xx) and 429 keep the `pending_send` claim. The next Sync, or the
  row's "Retry sending", re-sends it with the **same** key, so ZenxAI replays the original call rather
  than dialling again. Such rows count toward the 3-call cap; `invalid_phone` and other no-call rows don't.
- Every ZenxAI AJAX action also requires the session CSRF token (`verifyCSRFToken()`). That's defence
  in depth for actions that spend money; the existing Draft Applications actions don't check it.
- A per-session sliding window (55 requests/min) backs up the client-side pacing. The client sends
  batches of 10 (the server accepts at most 20).
- `config.php` defines the flag with `?? "0"`, so admin still works if it's deployed before the tenants column.
- The tenants-admin switch label is generated from the column name ("Zenxai Crm Enabled"). The shared
  render partial has no label map, so SAN-1029's suggested label "ZenxAI Voice Calls" wasn't applied.
- Earlier calls are rendered into a hidden, expandable row on page load instead of an extra AJAX call.

## Follow-ups shipped after v1 (2026-09-29 → 2026-10-01)

- **SAN-1136..1139 — billing via AI Credits.** Governing spec `SAN-1136-zenxai-voice-call-billing.spec.md`: one shared
  wallet, the `ai_voice_call` Task Rate in credits/min, a hold per call, and charging per connected minute.
- **SAN-1150 — finance-grade ledger trail.** New voice rows are append-only: HOLD → DEBIT → RELEASED. The AI Credits
  overview and history labels became HOLD / RELEASED (no "+"/"−" on holds). View ledger is available on the dashboard,
  in the History `task_type` filter and per call in the details modal. Page loads never wait on ZenxAI: the overview
  makes 0 polls and the dashboard at most 3. Details are in the SAN-1136 spec, "SAN-1150 ledger trail" section.
- **UI pass (SAN-1031 follow-ups):**
  - A summary strip styled like the AI Credits page, with Buy credits / View ledger.
  - Top-aligned table rows, a pinned Actions column, and a details modal with an audio player and expandable history.
  - A progress modal with counter tiles.
  - A dev-only "why is the button hidden" hint on Draft Applications. With `zenxai_crm_enabled` off there's no button
    and no hint at all; the button uses the theme primary colour.
  - CSS cache-busting (`?v=<mtime>`) for the shared stylesheets in `elements/header.php`.
- **SAN-1164 — call-date filter.**
  - GET `from`/`to` (validated `Y-m-d`, swapped if reversed), with presets Today / Last 7 / Last 30 / This month.
  - Filters on `zenxai_calls.created_at`. When active, only applicants with a call in range are shown, and the
    summary stats are scoped to the range.
  - Search, pagination and per-page keep the filter. "Clear filters" is always visible and disabled when no filter is
    set. Sync / Call applicants is never affected by the view filter.
  - Template gotcha: `sparkAdminTpl` has no `__isset`, so read template vars with `??` or directly, never `isset()`.
- **SAN-1356 — Re-call answered applicants.** `zenxaiRecallableStatuses()` gains `completed`, and the row button reads
  "Re-call" with its own confirmation. **Call selected** now also re-calls selected applicants whose row allows it,
  using the same `zenxaiCallState()` rule, re-checked server-side. The confirmation breaks down first calls, re-calls
  and skip reasons. Bulk Call applicants still only calls never-called drafts. The 3-call cap and drafts-only rule are
  unchanged (see the Q5 amendment).
- **SAN-1492 — dynamic Call Data.** `zenxaiBuildCallInputs()` fills ZenxAI `inputs` with only the keys whitelisted in
  `.env` `ZENXAI_INPUT_FIELDS`. Unset means `inputs: {}`, the pre-change behaviour.
  - Known keys: applicant_name, company_name, organisation_name, program_name, program_summary, completion_percent,
    missing_sections, deadline, application_link, support_email.
  - Completion uses the Update Percentage mandatory-field rule on the raw draft data.
  - **Pending on ZenxAI:** the owner adds the same Call Data keys and a Dynamic Flow to the assistant before
    `ZENXAI_INPUT_FIELDS` is set.
- **Parked by the product owner (2026-10-01):** client/program usage visibility, i.e. labels inside ZenxAI Call Logs
  and our own cross-tenant "AI Voice usage" report. To be discussed later.

## Future phase: webhooks (NOT v1)

Documented only so a later phase doesn't reinvent it.

- **Setup:** the ZenxAI owner configures a webhook URL. Events: `call.queued`, `call.dialing`,
  `call.retry_scheduled`, `call.completed`, `call.no_answer`, `call.busy`, `call.failed`,
  `call.cancelled`, `call.analysis_ready`.
- **Signature verification** (mandatory, before any DB read or write):
  - Header format: `X-ZenX-Signature: t=<unix>,v1=<hex>`.
  - Expected `v1` = `HMAC-SHA256("<t>.<raw body>", whsec_… secret)`, compared in constant time.
  - Reject if `t` is more than 5 minutes old.
  - Reply 2xx within 10 s.
- **Delivery behaviour:** ZenxAI retries at 1m, 5m, 30m, 2h, 6h, and 12h. Dedupe on the event id,
  and tolerate out-of-order delivery (never let an older non-final event overwrite a final status).
- **Secret storage:** `.env` (`ZENXAI_WEBHOOK_SECRET`) while the account is shared. It moves to a
  per-tenant settings table if accounts become per-tenant.
- **Tenant resolution:** with a shared account, the owner sets ONE webhook URL for all tenants, so
  the tenant can't come from the host. It must come from the signed payload's echoed
  `metadata.tenant_id`, which is trusted only after the HMAC check passes. The handler then
  opens that tenant's DB, and the `call_id` must exist in that DB's `zenxai_calls`, or the event
  is dropped. This needs its own `/check-isolation` review in that phase.
- **Decision needed at that point:** host in admin vs backend (the old Q7). Backend would add a
  public route to the API contract, plus the flag in the backend `Feature` enum and tenants
  `getTenantSettings()`.

## Contracts & invariants

- **Flags:** `zenxai_crm_enabled` — new, tenants-owned, default false. Consumers are the
  tenants-admin switch list and the `sc-saas-admin` `config.php` constant. It is not added to the
  backend `Feature` enum or the frontend `IFeatures`: invariant #1 means propagating to every layer
  that consumes the flag, and in v1 neither backend nor frontend gates anything on it.
  Gate: `/trace-flag`.
- **API:** no change to the sc-saas-backend contract. The external ZenxAI Voice API is consumed
  from admin (3 endpoints, listed above).
- **Events:** none.
- **Invariants at risk:**
  - **#1 flag names:** new flag; spell it identically in tenants, tenants-admin, and admin.
  - **#5 tenant scoping:** all reads/writes use the per-request tenant `$database`. The ZenxAI
    account is shared (Q4), so isolation comes from three rules:
    (a) calls are only polled or cancelled by `call_id`s read from this tenant's `zenxai_calls`;
    (b) Idempotency-Key and `reference` include the tenant id;
    (c) `metadata` tags the tenant.
    With no inbound endpoint in v1, no external caller can pick a tenant. Gate: `/check-isolation`.
  - **#4 auth:** no new unauthenticated surface in v1. All ZenxAI actions sit behind
    `checkLoggedIn()` plus the flag plus `can_broadcast_messages`.
  - **#2 API contract, #3 verification shape, #6 PowerPitch:** untouched.
- **Cost & harm:** every call dials a real person and spends wallet money. Hence the count +
  confirmation modal, the duplicate guard, the deterministic idempotency, and stop-on-402.
- **Data protection:** applicant PII (name, email, phone, company in metadata) goes to a third
  party, and ZenxAI returns call recordings, summaries, and collected answers (also PII). Access
  is restricted to permitted roles and excluded from CSV. Consent/disclosure (Q8) is a go-live gate; see Rollout.

## Test plan

**SAFETY RULE: never dial a real applicant from dev/QA.** Every ZenxAI call rings a real phone and
costs wallet balance.

- **Default:** a local mock HTTP server (scratch PHP/Node) that implements
  `POST /assistants/{id}/calls`, `GET /calls/{id}`, and `POST /calls/{id}/cancel` with canned
  responses: 202, 200 replay, 400 invalid_phone, 401, 402, 403, 409 (idempotency_conflict and
  not_cancellable), 429 + Retry-After, timeouts, and status progressions through every status.
  Point the dev `.env` `ZENXAI_BASE_URL` at it.
- **Live smoke (only if Q-C allows):** exactly one call to a single internal team phone number,
  on a synthetic draft, with the account owner's agreement.
- Dev/staging `.env` files must never hold the production API key.

Per repo:

- **tenants:** `npm run build`; confirm the column on a dev DB; `/trace-flag zenxai_crm_enabled`.
- **sanchiconnect-saas-tenants-admin:** `php -l`; toggle the flag on/off on Edit Tenant, confirm it
  persists and shows on Detail.
- **backend:** `tsc --noEmit` / `npm run build`; boot against a dev tenant DB and confirm the two
  `zenxai_calls` table, its UNIQUE indexes, and no diff on other tables.
- **admin:** `php -l` every touched file. Manual checks against the mock:
  - flag off → no button, pages redirect; flag on with ZENXAI_* unset → "ZenxAI is not
    configured", no call possible
  - confirmation modal shows the right count
  - batch pacing stays under 60/min; a 429 resumes after Retry-After
  - 401/402/403 stop the run with the right message
  - double-click and retried requests → the same Idempotency-Key and no second call
  - invalid phone → `failed/invalid_phone`, no HTTP call
  - rows with a non-final or completed call are skipped; Call again → key `n+1`
  - Refresh / Refresh-all update the fields, and final rows aren't re-polled
  - Cancel works only in allowed states
  - `users` override applied; submitted/deleted drafts and other programs excluded
  - API key absent from the DB, `request_payload`, responses, and logs
  - PII columns hidden without the permission
- **cross-tenant (shared account):** two dev tenants against the SAME mock, with deliberately
  identical program/submission ids. Their Idempotency-Keys and references differ (tenant id). The
  mock never returns tenant A's call to tenant B. Each dashboard shows only its own calls.
  Tampering a `call_id` in a Refresh/Cancel request is rejected. `/check-isolation`.
- **Automated tests:** the Developer Guide's "guardian" skill doesn't exist here and `sc-saas-admin`
  has no test framework, so no automated coverage is added. Verification is `php -l`, `tsc`, and
  manual repro against the mock. State this in the Linear issues.

## Rollout

1. Deploy tenants (column default false everywhere), then the tenants-admin switch entry.
2. Deploy backend (inert tables in each tenant DB).
3. Deploy sc-saas-admin (everything behind `zenxai_crm_enabled`).
4. Put `ZENXAI_BASE_URL`, `ZENXAI_ASSISTANT_ID`, and `ZENXAI_API_KEY` (from the ZenxAI account
   owner) into the production sc-saas-admin `.env` — one shared account for all tenants.
5. Confirm the wallet balance and the Q-A/Q-B assistant settings with the owner.
6. **Go-live gate (Q8):** confirm with the ZenxAI owner that the assistant's opening line
   discloses it is an AI assistant calling on behalf of the program, and that the call may be
   recorded. Don't enable the flag in production until that's confirmed.
   Enable the flag for the requesting tenant only. Run one controlled call to an internal team
   number (Q-C), then open it to admins.
7. Other tenants: enable the flag per tenant on request. They all draw on the same wallet until
   the business model is decided.

## Out of scope

- Submitted applications, program rounds, and stakeholder profiles — drafts only.
- Fields beyond name, email, phone, and company_name.
- Inbound webhooks (future phase above) and any cron-driven polling or auto-calling in v1.
- Writing ZenxAI results back into `forms_submissions`.
- Adding recording/summary/collected_data to CSV exports.
- Changes to the existing Zoho integration, and any `sc-saas-frontend` change.
- Our own calling-hours logic (ZenxAI holds calls as `queued` outside its allowed hours).

## Linear tracking

Project **P-SAN-63 "ZenxAI Voice Calls for Draft Applications"** (team Sanchiconnect, lead Nirmal
Singh): https://linear.app/sanchiconnect/project/zenxai-voice-calls-for-draft-applications-5fbb3554def5

| Issue | Repo label | Priority | State | Assignee | Blocked by |
|---|---|---|---|---|---|
| SAN-1028 — Tenants flag `zenxai_crm_enabled` | `Repo: Tenants` | High | In Review | Nirmal Singh | — |
| SAN-1029 — Tenants-Admin switch list | `Repo: Tenants-Admin` | Low | In Review | Nirmal Singh | SAN-1028 |
| SAN-1030 — Backend entity `zenxai_calls` | `Repo: Backend` | High | In Review | Nirmal Singh | SAN-1028 |
| SAN-1031 — Admin ZenxAI dashboard + calls (env config) | `Repo: Admin` | High | In Review | Nirmal Singh | SAN-1028, SAN-1030 |
| SAN-1136..1139 — Billing via AI Credits (see `SAN-1136-zenxai-voice-call-billing.spec.md`) | Tenants / Tenants-Admin / Backend / Admin | High | In Review | Nirmal Singh | SAN-1028..1031 |
| SAN-1150 — Credit ledger trail + View ledger (in SAN-1136 spec) | `Repo: Admin` | High | In Review | Nirmal Singh | SAN-1139 |
| SAN-1164 — Call-date filter + Clear filters | `Repo: Admin` | Medium | In Review | Nirmal Singh | SAN-1031 |
| SAN-1356 — Re-call answered applicants + Call selected re-calls | `Repo: Admin` | Medium | In Review | Nirmal Singh | SAN-1031 |
| SAN-1492 — Dynamic Call Data (`ZENXAI_INPUT_FIELDS`) | `Repo: Admin` | High | In Review | Nirmal Singh | SAN-1031 |

**Status (2026-10-01):** all code is pushed to `ai_native_setup` in every repo. Issues stay **In Review** until two
things happen: (1) the tables are confirmed on a real deployed DB (deploy order tenants → tenants-admin → backend →
admin), and (2) the go-live gates are met (`.env` keys, the `ai_voice_call` Task Rate, the AI/recording disclosure,
one internal test call).

## Open questions

All product/design questions are resolved; spec **approved 2026-09-28** by Nirmal Singh ("update the
spec then let's start this module"), taking the defaults below.

### Resolved

- **Q0 (Linear tracking):** RESOLVED 2026-09-28. Project P-SAN-63 + SAN-1028..1031 created, all
  assigned to Nirmal Singh (see Linear tracking).
- **Q1 (endpoint/auth):** RESOLVED (evidence: ZenxAI docs "Sanchi Developer: Voice API",
  2026-09-28). `POST https://crm.zenxai.io/api/public/v1/assistants/{assistant_id}/calls`,
  `Authorization: Bearer <API key obtained from the ZenxAI account owner>`, key bound to one assistant.
- **Q2 (payload/response):** RESOLVED (same evidence). Body `{phone, inputs, reference, metadata}`
  + optional `Idempotency-Key`; `202` call object with `call_id`; errors `{error:{code,message}}`;
  60 req/min. "Duplicate" is handled by our own guard + Idempotency-Key, since ZenxAI doesn't
  dedupe calls.
- **Q3 (how results come back):** RESOLVED for v1 (same evidence). Polling `GET /calls/{call_id}`;
  the webhook scheme is known and documented as a future phase.
- **Q4 (account model):** RESOLVED 2026-09-28 by the product owner (Nirmal Singh): *"for now use
  single account, will set up the business model later."* v1 uses ONE shared ZenxAI account.
  Credentials are in the admin `.env`, there's no per-tenant settings table or page, and the tenant
  id goes into every key, reference, and metadata. Per-tenant accounts and billing are deferred.
  `zenxaiConfig()` is the seam for adding them later.
- **Q5 (re-call rules):** RESOLVED 2026-09-28 (defaults accepted):
  - Bulk Sync calls only drafts that have never been called.
  - "Call again" is manual and per row, only after `no_answer`/`busy`/`failed`/`cancelled`, with a
    maximum of 3 placed calls per submission and no cooldown.
  - Submitted or deleted applicants stay on the dashboard read-only (Refresh only).
  - The button shows when there are drafts or past calls.
  - **Amended 2026-10-01 (SAN-1356, product owner):** an *answered* (`completed`) applicant can also be
    re-called manually ("Re-call" button, follow-up call, credits charged again). Still capped at 3 placed
    calls, drafts only, never while a call is in progress; bulk Sync still calls never-called drafts only.
- **Q6 (permissions):** RESOLVED 2026-09-28. The default proposed "a new `can_use_zenxai`
  permission", but `spa_admin_users` has no schema owner in any repo (see Code findings), so it's
  revised to **reuse `can_broadcast_messages`**. That's the gate for "Send Bulk Email" on the same
  page, and the same kind of applicant outreach. It covers viewing the dashboard, placing,
  cancelling, and refreshing calls, and viewing recordings/summaries/collected_data. There's no
  settings page to gate (Q4). Partner admins get no access in v1. A dedicated permission can come
  later, once someone owns that table's schema.
- **Q7 (webhook host):** MOOT for v1 (no webhook). Reopens with the webhook phase.
- **Q8 (consent/disclosure):** RESOLVED as a **go-live gate**, not code: the assistant's script
  must disclose that it's an AI and that the call may be recorded before the flag is enabled in
  production (Rollout step 6). There's no opt-out/do-not-call list in v1; an admin simply doesn't
  call.

### External follow-ups (non-blocking: ask the ZenxAI account owner; the build proceeds without them)

- **Q-A:** turn on "Save as Enquiry" so `lead_id` is populated and leads are created in ZenxAI.
  The code already stores and displays `lead_id`, so nothing changes on our side when it's turned on.
- **Q-B:** add Call Data fields (`customer_name`, `company_name`, `program_name`) so the assistant
  can address the applicant by name. When added, we fill `inputs`, which is a small follow-up change.
- **Q-C:** a sandbox/test assistant or non-billing mode. Until then: mock server only, plus at most
  one live call to an internal team phone.
