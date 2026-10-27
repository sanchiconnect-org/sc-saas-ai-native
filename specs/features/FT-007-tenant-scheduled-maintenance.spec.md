---
id: FT-007
title: Tenant-scoped scheduled maintenance mode (per tenant or all tenants, with advance notice)
type: feature
status: in-review               # draft → approved → in-progress → in-review → done. Open questions resolved by Nirmal 2026-10-27; implemented 2026-10-27 (uncommitted), all four issues In Review.
linear: https://linear.app/sanchiconnect/project/enhancement-7825a8dad14b
linear_milestone: FT-007 — Tenant-scoped scheduled maintenance mode
owner: nirmal.s@sanchiconnect.com
repos:                          # DEPENDENCY ORDER
  - sanchiconnect-saas-tenants          # schema + migration + computed maintenance_mode (SAN-2105)
  - sanchiconnect-saas-tenants-admin    # operator UI that writes the windows (SAN-2106)
  - sc-saas-frontend                    # PWA banner/timer/maintenance page (SAN-2107)
  - sc-saas-admin                       # tenant admin banner + live block (SAN-2108)
contracts:
  api:
    # Response payload change (additive only), no route added/renamed. Owned by sanchiconnect-saas-tenants.
    - "GET api/v1/public/global/verify_tenant/:hostname → data.maintenance_mode (additive keys, now tenant-specific and time-computed)"
    - "GET api/v1/public/global/tenant-settings/:hostname → maintenance_mode (same)"
    - "resolve-domain/:hostname (frontend's first call; same builder as verify_tenant, 30s cache) → maintenance_mode (same)"
    # Shared-DB contract (no API in between): written by sanchiconnect-saas-tenants-admin, read by
    # sanchiconnect-saas-tenants (TypeORM) and sc-saas-admin (Medoo, via $mainDatabase).
    - "tenants DB table tenant_maintenance (extended) + new link table tenant_maintenance_tenants"
  flags: []                     # No TenantUsersEntity column is added. Maintenance is NOT a feature flag (invariant 1 untouched).
  events: []
tenant_scoped: true             # A window now targets specific tenant_users rows; every read must be scoped to the requesting tenant.
depends_on: []
created: 2026-10-27
---

# Tenant-scoped scheduled maintenance mode

## Reference

Originates from a direct user request (no pre-existing Linear issue, no `/from-linear` pull). Requirements
were confirmed by the user before drafting (see Problem). Related, partly superseded spec:
`specs/features/maintenance-mode-page.spec.md` (2026-09-01, draft) — its "Out of scope" explicitly excluded
per-tenant maintenance and time-based activation, and several of its Evidence statements are now stale
(see Contradictions C5).

Linear: project **Enhancement**, milestone **FT-007 — Tenant-scoped scheduled maintenance mode**.

| Repo | Issue | Labels | Priority |
|---|---|---|---|
| sanchiconnect-saas-tenants | [SAN-2105](https://linear.app/sanchiconnect/issue/SAN-2105/tenants-tenant-scoped-scheduled-maintenance-windows-schema-migration) | Feature, Repo: Tenants | 1 Urgent |
| sanchiconnect-saas-tenants-admin | [SAN-2106](https://linear.app/sanchiconnect/issue/SAN-2106/tenants-admin-scheduled-maintenance-windows-ui-allselected-tenants) | Improvement, Repo: Tenants-Admin | 2 High |
| sc-saas-frontend | [SAN-2107](https://linear.app/sanchiconnect/issue/SAN-2107/frontend-scheduled-maintenance-auto-switch-at-startend-and-show-end) | Improvement, Repo: Frontend | 2 High |
| sc-saas-admin | [SAN-2108](https://linear.app/sanchiconnect/issue/SAN-2108/admin-tenant-scoped-maintenance-banner-block-admin-pages-while) | Feature, Repo: Admin | 1 Urgent |

SAN-2106/2107/2108 are `blockedBy` SAN-2105. All assigned to Nirmal Singh.

Evidence tags (spec-authoring practice 3): **[E]** = evidenced at the cited file:line, **[INFERRED — requires
validation]**, **[NOT SPECIFIED IN SOURCE]**, **[DESIGN DECISION PENDING]**.

## Problem

Maintenance mode today is one platform-wide ON/OFF checkbox in tenants-admin (`/maintenance_mode`). It
cannot target one client, it cannot be scheduled, and the advance-notice banner has no way to be set from any
UI. The user wants:

1. Maintenance per tenant/client, and still for all tenants at once.
2. A scheduler: an operator sets start/end ahead of time; clients see advance notice of when it starts.
3. Both **sc-saas-frontend (PWA)** and **sc-saas-admin (tenant admin panel)** show the upcoming-maintenance
   banner, and both are blocked while maintenance is live.

## Evidence — current code state (verified 2026-10-27)

1. **Entity** [E] `sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-maintenance.entity.ts:3-43`:
   table `tenant_maintenance`; `title` varchar NOT NULL, `message` text null, `date` date NOT NULL,
   `start_time`/`end_time` **varchar** NOT NULL (TS props `startTime`/`endTime`, which is the JSON key name
   clients receive), `active` bool default false, `maintenance_on` bool default false, `maintenance_on_title`
   varchar NOT NULL, `maintenance_on_message` text null, `actual_start_time`/`actual_end_time` timestamp null,
   `notes` text null. **No tenant column.** Baseline: `src/core/database/migrations/1792394003573-Baseline.ts:188`.
   Registered in `tenants.module.ts:10` (`forFeature`).
2. **Migrations rule** [E] `src/core/database/migrations/README.md:17-18` — every entity change needs a
   migration; the `migrations` CI job fails if entities differ. `synchronize: true` is still on in every env
   (tenants `CLAUDE.md` Guardrails; SAN-1630 phase 4 pending).
3. **Selector** [E] `tenants.service.ts:12-20` — `TenantMaintenanceEntity.findOne({ where: { active: true },
   order: { id: 'DESC' } })`. No tenant filter, no time check. A row with `maintenance_on = 1, active = 0` is
   invisible.
4. **Callers** [E] `global.service.ts:716-720` (verify_tenant builder; `tenant.id` is in scope, used at
   `:722-724` for the subscription lookup) and `global.service.ts:1010-1014` (tenant-settings; `tenant.id` in
   scope at `:1016-1018`). Both assign the raw entity to `maintenance_mode`. **Maintenance is fetched
   separately from the hand-maintained tenant field lists** (memory rule "tenant flags need explicit field-list
   edits") — no `select:` list edit is needed for this feature, because no `tenant_users` column is added. [E]
5. **Cache** [E] `global/services/domain-resolver.service.ts:85-95` — resolve-domain results are cached for
   `CACHE_TTL_MS = 30 * 1000`; the comment names `maintenance_mode` as a field that can lag up to 30s.
6. **Frozen contract** [E] `contracts/tenant-verification.schema.json:34,281` require the `maintenance_mode`
   key; generated TS `contracts/generated/tenant-verification.ts:259,474` types it `unknown`. The same
   generated copy sits in `sc-saas-frontend/src/app/core/contracts/tenant-verification.ts:259,474` and
   `sc-saas-backend/src/core/contracts/tenant-verification.ts:259,474`. So the compile-time drift check does
   **not** cover anything inside `maintenance_mode` today.
7. **Jest mocks** [E] `getTenantsMaintenance: jest.fn().mockResolvedValue(null)` in
   `global.service.notification-centre-flag.spec.ts:49`, `tenant-verification.contract.spec.ts:272,374`,
   `global.service.hostname-match.spec.ts:41`.
8. **Tenants-admin switch** [E] `sanchiconnect-saas-tenants-admin/modules/maintenance_mode.php:16-85` —
   `checkLoggedIn()`, super_admin/developer role gate (`:19-23`), reads latest row with no filter (`:25-27`),
   POST `toggleMaintenance` with `verifyCSRFToken()` (`:38`), writes `active = maintenance_on = $wantOn`
   (`:46-49`), first save inserts placeholders `title "Maintenance"`, `date today`, `start_time "00:00"`,
   `end_time "23:59"`, `maintenance_on_title "Under Maintenance"` (`:57-63`). Template
   `themes/default/html/maintenance_mode.php` (single checkbox; copy at `:41` says "Staff and partner admin
   panels stay accessible regardless of this setting"). Menu entry `includes/core_functions.php:163-173`
   (`"link" => "../maintenance_mode"`, Developer zone dropdown). This is the **only** tenants-admin file that
   touches `tenant_maintenance`. [E]
9. **Tenant list available to tenants-admin** [E] `modules/client_stats/list.php:74-75` selects
   `tenant_users` `id, name, domain, …` — the same read pattern the tenant picker can use.
10. **Frontend** [E]
    - `core/domain/brand.model.ts:14` `maintenance_mode: IMaintenance`; `:237-252` `IMaintenance` (id, title,
      message, date, startTime, endTime, active, maintenance_on, actual_*, notes, maintenance_on_message,
      maintenance_on_title).
    - `app.component.ts:210-220` — on `getBrandDetails`, `if (maintenance_mode?.maintenance_on)
      maintainanceMode = true`. It is **never set back to false**.
    - `app.component.html:21-22` — `<app-maintenance-page>` when `maintainanceMode`; `:44-57` banner when
      `maintenance_mode?.active && maintenanceClosed && !maintainanceMode`, showing `title`, `message`,
      `formatMaintenanceTime(startTime) - formatMaintenanceTime(endTime)`; `:65` router-outlet gated on
      `!maintainanceMode`.
    - `app.component.ts:619-631` — dismissal key `'maintainance_' + maintenance_mode.id`;
      `formatMaintenanceTime` = `moment.utc(time).local().format('DD MMMM, YYYY hh:mm a')`.
    - `shared/common-components/maintenance-page/maintenance-page.component.ts:8-13` — no inputs, only
      `handleRetry()` → `window.location.reload()`; template `.html:9-18` is static copy ("Scheduled
      maintenance", "We'll be right back").
    - Fixtures referencing the shape: `app.component.spec.ts:21`, `core/service/tenant.service.spec.ts:37`.
11. **sc-saas-admin** [E]
    - Tenant row: `config/config.php:96-103` — `$getDatabaseSettingsFromMainTable = $mainDatabase->get("tenant_users",
      "*", …admin_domain/admin_custom_domain…, active = 1)`. Its `id` is this tenant's `tenant_users.id`
      (already used that way at `modules/index.php:205` for `subscriptions.tenant_id`).
    - Banner read: `modules/index.php:200-202` — `$mainDatabase->get("tenant_maintenance","*",
      array("active" => "1", "ORDER" => array("id" => "DESC")))`, no tenant filter.
    - Banner render: `themes/default/html/index.php:147-165` — gated on `isset($this->maintenanceMessage['id'])`;
      times via `convertToKolkataTime($this->database, …)` (`includes/core_functions.php:6819-6828`, which
      actually converts to the tenant's `spa_settings.timezone`, not hardcoded Kolkata).
    - Central enforcement point: root `index.php:45` includes `config/config.php`, then `:71-87` already runs a
      pre-routing gate (`enforceJuryNdaGate`) before any module file loads; `:113-137` routes every module,
      including `auth/login` and `ajax/*`. A 503 page pattern already exists: `config/config.php:140-143`
      (`http_response_code(503)`, `Retry-After`, `modules/database-connectivity-error.php`).
    - Other web entry points [E] `tests/auth-gates.json:386-403` `rootEntryPoints`: `db_admin.php`,
      `easebuzz_callback.php`, `health.php`, `index.php`. `cli/` scripts do not pass through `index.php`.
12. **sc-saas-backend** [E] — zero references to `maintenance_mode` beyond the generated contract copy
    (`src/core/contracts/tenant-verification.ts:259,474`). No enforcement.
13. **sc-saas-e2e** [E] `config/tenant-contract.ts:35,43` lists `maintenance_mode` among required response
    keys (black-box contract test `tests/api/tenant-contracts.spec.ts`, per `knowledge.md:18`). No test drives
    the maintenance page or banner (grep). Key stays present → that test keeps passing. A live window that
    covers the QA tenant will turn every UI test red (expected; see Rollout).

## Contradictions with the proposed design (found in code)

- **C1 — start/end are varchar holding `"00:00"`/`"23:59"`, not datetimes.** Changing `start_time`/`end_time`
  to DATETIME in place under `synchronize: true` makes TypeORM issue an `ALTER … MODIFY` on app boot; MySQL
  strict mode rejects `"00:00"` → DATETIME, which can fail the boot or (non-strict) zero the value. And
  `moment.utc("00:00")` on the frontend is already an invalid date today. → The design must **not** alter
  those two columns in place. Recommended: add new `starts_at`/`ends_at` DATETIME columns (UTC), have the
  migration backfill legacy rows (NULL — they are manual-switch rows), and keep emitting `startTime`/`endTime`
  in the payload as ISO-8601 UTC strings derived from the new columns (both consumers already parse UTC).
  **Decided (Q6): new `starts_at`/`ends_at` DATETIME columns.**
- **C2 — `active` is the stored filter today, not a computed field.** Under the new design `active` and
  `maintenance_on` in the payload become computed. The stored columns need a defined meaning: proposed
  stored `maintenance_on` = manual override set by "Start now"; stored `active` = legacy, kept in sync for old
  readers until all consumers ship, then ignored. [INFERRED — requires validation]
- **C3 — sc-saas-admin's dashboard banner most likely never renders today.** `themes/default/html/index.php:147`
  uses `isset($this->maintenanceMessage['id'])`; `sc-saas-admin/core/template.php` defines only `__set`
  (`:44`) and `__get` (`:52`), no `__isset`, so `isset()` on the magic property is always false (same root
  cause as SAN-1164). So "both show the banner today" is not true for sc-saas-admin; this spec fixes it.
- **C4 — the PWA never leaves maintenance mode without a reload.** `app.component.ts:214-216` only ever sets
  `maintainanceMode = true`. A timer that flips back after `end` must also set it to false.
- **C5 — the older spec and the tenants-admin copy say the admin panel must stay usable.**
  `maintenance-mode-page.spec.md` Evidence 6/7 say sc-saas-admin has zero `maintenance_mode` references and
  tenants-admin has no UI; both are stale (`modules/index.php:201` reads the table; `maintenance_mode.php`
  exists since 59c91ea). Its Out of scope also states "admins and partner staff must keep working during a
  maintenance window", and the tenants-admin template (`maintenance_mode.php:41`) says the same. The confirmed
  requirement now blocks sc-saas-admin too. The old spec should be marked superseded for these points.
- **C6 — tenants module spec says the table is unscoped by design.** `src/modules/tenants/module.spec.md:259,279,323`
  ("Maintenance windows apply to the entire platform", "There is no per-tenant maintenance scheduling") must be
  updated with this change.
- **C7 — the 30s resolve-domain cache freezes the computed flags.** A response computed 10s before
  `start` says `maintenance_on: false` and can be served for up to 30s after `start`. The design needs the
  client-side timer (frontend) and must not rely solely on the computed boolean. sc-saas-admin reads the DB
  directly and is not affected. [E] `domain-resolver.service.ts:95`

Everything else in the brief matched the code.

## Design

### Data model (tenants DB)

`tenant_maintenance` (extended, all additions nullable or defaulted so existing rows stay valid):

| Column | Type | Notes |
|---|---|---|
| `scope` | varchar(16) NOT NULL default `'all'` | `'all'` \| `'selected'`. Existing rows → `'all'`. |
| `notice_from` | datetime NULL (UTC) | When the banner starts. NULL → no advance banner. |
| `starts_at` / `ends_at` | datetime NULL (UTC) | The schedule (see C1). `ends_at` NULL only for a manual "Start now" with no planned end. |
| `cancelled` | tinyint(1) NOT NULL default 0 | Cancelled windows are never returned. |
| `title`, `date`, `maintenance_on_title` | made NULLable | Legacy placeholders no longer required. |
| `start_time` / `end_time` | unchanged varchar (made NULLable) | Not altered in type (C1). Payload keys `startTime`/`endTime` are filled from `starts_at`/`ends_at`. |

New `tenant_maintenance_tenants`: `id` PK, `maintenance_id` → `tenant_maintenance.id` (ON DELETE CASCADE),
`tenant_id` → `tenant_users.id`, unique (`maintenance_id`, `tenant_id`), index on `tenant_id`.
**Decided (Q1): link table — one window can cover several selected tenants.**

### Selection and computed state (single source of truth: the cockpit)

For tenant T at time `now` (UTC):

- Candidates = rows where `cancelled = 0` AND (`scope = 'all'` OR a link row with `tenant_id = T.id` exists)
  AND NOT ended (`ends_at IS NULL OR ends_at > now`) AND (manual override on OR `notice_from <= now` OR
  `starts_at <= now`). Legacy rows (no `starts_at`) qualify only via the manual override.
- `maintenance_on` (live) = manual override OR (`starts_at <= now < ends_at`).
- `active` (notice) = NOT live AND `notice_from <= now < starts_at`.
- Precedence: any live candidate beats any notice-only candidate; among equals, earliest `starts_at`, then
  highest id.
- None → `maintenance_mode: null` (exactly as today).

Payload: the existing `TenantMaintenanceEntity` keys (backward compatible, with `active`/`maintenance_on`
replaced by the computed values and `startTime`/`endTime` as ISO-8601 UTC) plus additive keys `scope`,
`notice_from`, `starts_at`, `ends_at`, `server_time` (lets clients correct clock skew for the timer).
`scope` exposes nothing sensitive; the list of linked tenant ids is **never** included. [INFERRED — requires
validation: `server_time` is a proposal]

sc-saas-admin re-implements the same rules in PHP against the same tables (no API call to the cockpit exists
from sc-saas-admin today, and adding one is out of scope). The rules above are the shared definition; both
implementations get the same test matrix (Test plan).

## Acceptance criteria

Tenants (SAN-2105)
- [ ] AC-1 A migration under `src/core/database/migrations/` adds the columns/table above; on a DB holding the
      legacy placeholder row (`start_time "00:00"`) it runs without error, and the `migrations` CI job passes.
      `start_time`/`end_time` keep their varchar type.
- [ ] AC-2 Existing rows end up `scope = 'all'`, `cancelled = 0`. A legacy row with `active = 1,
      maintenance_on = 1` before the migration is still live for every tenant after it.
- [ ] AC-3 `verify_tenant`, `tenant-settings` and `resolve-domain` for tenant A return a window with
      `scope = 'selected'` linked only to tenant B as `maintenance_mode: null` for A and as the window for B.
- [ ] AC-4 For a window with `notice_from = now-1h, starts_at = now+1h, ends_at = now+2h`: `active = true,
      maintenance_on = false`. Once `now >= starts_at`: `maintenance_on = true, active = false`. Once
      `now >= ends_at`: `maintenance_mode = null` (subject only to the 30s cache).
- [ ] AC-5 A cancelled window is never returned. A live window beats a notice-only one; two notice windows →
      the earlier `starts_at` wins.
- [ ] AC-6 Every key present in today's payload is still present (backward compatible);
      `tenant-verification.contract.spec.ts` passes without regenerating the schema (or, if Q5 decides to type
      it, after a deliberate regenerate + `scripts/sync-shared-types.sh`).
- [ ] AC-7 The payload never includes other tenants' ids or names.
- [ ] AC-8 `npm run gates` green; new unit tests cover AC-3..AC-5 (time injected, not wall-clock).

Tenants-admin (SAN-2106)
- [ ] AC-9 `/maintenance_mode` lists windows with a computed status (Scheduled / Notice showing / Live /
      Ended / Cancelled) matching the cockpit rules.
- [ ] AC-10 Create/edit: scope all or picked tenants (active `tenant_users`), start/end entered in IST and
      stored as UTC, notice lead time, banner title/message, live-page title/message. Rejected server-side:
      end ≤ start, notice after start, `selected` with zero tenants.
- [ ] AC-11 Start now / End now / Cancel work and take effect within the 30s cache window on the PWA and on
      the next page load in sc-saas-admin.
- [ ] AC-12 Non super_admin/developer → `/403`; every POST checks the CSRF token; `composer gates` green; no
      `//` comments (PHP or `<script>`).

Frontend (SAN-2107)
- [ ] AC-13 During notice, the dismissible banner shows title, message and start–end in the user's local time;
      dismissal is remembered per window id.
- [ ] AC-14 A user who has the app open when `starts_at` passes is switched to the maintenance page without a
      reload (± a few seconds); after `ends_at` the page returns to the app (or a reload succeeds) without
      manual cache clearing.
- [ ] AC-15 The maintenance page shows the operator's live title/message and the expected end time (local),
      falling back to today's static copy when empty or when `ends_at` is NULL.
- [ ] AC-16 `npm run gates` green (production build, Karma, floors); new spec covers the timer flip both ways.

sc-saas-admin (SAN-2108)
- [ ] AC-17 The banner query is scoped to this tenant (`scope = 'all'` OR linked to
      `$getDatabaseSettingsFromMainTable['id']`) and uses the same notice/live rules; a window for another
      tenant never appears. `/check-isolation` passes.
- [ ] AC-18 The dashboard banner actually renders during notice (C3 fixed: no `isset($this->…)`).
- [ ] AC-19 While live, every route through `index.php` (module pages, `auth/login`, partner portal) returns
      HTTP 503 with a maintenance page showing message and expected end; `ajax/*` and other XHR requests get a
      JSON 503 instead of HTML. `health.php` and `easebuzz_callback.php` keep working. Bypass (Q4): `auth/login` stays reachable for
      everyone; after login, users passing `checkIsDevOrSuperAdminRole()` (`includes/core_functions.php:984`)
      get through with a visible "maintenance is live" notice, everyone else is logged-in-blocked with the 503
      page. Non-bypass users who try to log in see the 503 page after authentication.
- [ ] AC-20 After `ends_at` (or End now / Cancel), the admin works again on the next request with no deploy.
- [ ] AC-21 `composer gates` green, `php -l` on each changed file, no new unguarded module file.

Cross-repo
- [ ] AC-22 sc-saas-backend is unchanged and builds; sc-saas-e2e `tenant-contracts` test still passes.

## Per-repo plan

### sanchiconnect-saas-tenants (SAN-2105)
1. Entity: extend `TenantMaintenanceEntity`; add `TenantMaintenanceTenantEntity`
   (`src/modules/tenants/entities/tenant-maintenance-tenant.entity.ts`); register both in
   `tenants.module.ts:10` `forFeature`.
2. Migration: generate under `src/core/database/migrations/` (README commands); hand-edit to set `scope = 'all'`
   on existing rows and to NOT touch `start_time`/`end_time` types.
3. `TenantsService.getTenantsMaintenance(tenantId: number, now = new Date())` implementing the selection
   rules (filter by `tenantId` from the domain-resolved tenant row — the tenant-scoping rule for this repo).
   Map to the payload described in Design.
4. `global.service.ts:719` and `:1013` → pass `tenant.id`.
5. Update the 4 jest mocks (Evidence 7); add `tenants.service.spec.ts` with the AC-3..AC-5 matrix.
6. Update `src/modules/tenants/module.spec.md` (C6) and `src/modules/global/module.spec.md` (`maintenance_mode`
   is now tenant-specific and computed).
7. Gates: `npm run gates`, `/check-isolation`, and confirm `dist/main.js` boots (memory: verify Nest start
   path).

### sanchiconnect-saas-tenants-admin (SAN-2106)
1. Rework `modules/maintenance_mode.php` into list + form (or `modules/maintenance_mode/{list,edit}.php`; if
   the file moves, update the menu `link` at `includes/core_functions.php:170`). Keep `checkLoggedIn()` first,
   the role gate (`:19-23`) and `verifyCSRFToken()` on every POST action (`save`, `startNow`, `endNow`,
   `cancel`).
2. Tenant picker from `tenant_users` (`id, name, domain`, `active = 1`), same read as `client_stats/list.php:74`.
3. IST ↔ UTC conversion server-side (`DateTime` with `Asia/Kolkata` → `UTC`); render list times in IST.
4. Writes to `tenant_maintenance_tenants` replace the link set on save (delete + insert in a transaction).
5. Status column computed with the same rules as the cockpit.
6. Remove the copy at `themes/default/html/maintenance_mode.php:41` (C5).
7. Conventions: `/* */` only (incl. `<script>`), `count($x) > 0`, no `isset($this->x)` in templates, inline
   scripts deferred with `window.addEventListener('load', …)`. `composer gates`, `php -l`.

### sc-saas-frontend (SAN-2107)
1. `brand.model.ts:237` `IMaintenance`: add `scope`, `notice_from`, `starts_at`, `ends_at`, `server_time`
   (only if the cockpit sends them — SAN-2105 first).
2. `app.component.ts:210-220`: compute live/notice from the timestamps (with `server_time` skew correction),
   set `maintainanceMode` true **and false** (C4), and schedule one `setTimeout` to the next boundary
   (`starts_at` or `ends_at`); clear it on destroy and on every new brandDetails emission. Also re-fetch
   tenant config at the boundary so the cockpit's state wins.
3. `maintenance-page.component`: add `@Input()`s (title, message, endsAt); keep `handleRetry()`; keep it
   presentational (no store injection).
4. `app.component.html:21-22` pass the inputs; banner block `:44-57` unchanged apart from field source.
5. Fixtures: `app.component.spec.ts:21`, `core/service/tenant.service.spec.ts:37`; new timer spec with
   `fakeAsync`. `npm run gates`. Remember PWA service-worker caching when verifying.

### sc-saas-admin (SAN-2108)
1. New helper (e.g. `getTenantMaintenanceWindow($mainDatabase, $tenantId)` in `includes/core_functions.php`)
   implementing the selection rules with Medoo against `$mainDatabase`, scoped by
   `$getDatabaseSettingsFromMainTable['id']`.
2. `modules/index.php:200-202` → use the helper; expose only the notice window to the template.
3. `themes/default/html/index.php:147` → `$maintenance = $this->maintenanceMessage;` then test the local
   (C3). Times through `convertToKolkataTime()`.
4. Root `index.php`, right after `config/config.php` / before the jury NDA gate (`:71`): if live, let
   `auth/login` (and logout) through; for every other route, unless `checkIsDevOrSuperAdminRole()` is true
   (Q4) → `http_response_code(503)`, `Retry-After`, then JSON for XHR/`modules/ajax/*` requests or a new
   `modules/maintenance-live.php` page (self-contained like `database-connectivity-error.php`, added to
   `tests/auth-gates.json` `allowList` as `public` with reason/owner). Bypassing users see a top notice
   that maintenance is live.
5. Do not touch `health.php`, `easebuzz_callback.php`, `db_admin.php` (already `is_dev`-only, so it is
   covered by the bypass), `cli/`.
6. `/* */` only, `count() > 0`; `composer gates`, `php -l`, `/check-isolation`.

### sc-saas-backend
No change in phase 1 (Q2). Its generated contract copy is only touched if Q5 decides to type
`maintenance_mode`, in which case a separate backend issue is needed (one-repo-per-issue rule).

## Cross-Repo Contract Impact

- **Tenant-verification payload (invariant 3).** Current: `maintenance_mode` = raw `TenantMaintenanceEntity`
  row or null, same for every tenant, `active`/`maintenance_on` as stored. Change: tenant-specific, time-
  computed, additive keys only; no key removed or renamed. The frozen schema only requires the key to exist
  (`unknown` inner type), so no regeneration is required unless Q5 says to type it. Consumers:
  sc-saas-frontend (`brand.model.ts`, `app.component.*`), sc-saas-backend (generated copy only, no reader),
  sc-saas-e2e (`config/tenant-contract.ts` key presence). Gate: `tenant-verification.contract.spec.ts` +
  `/audit-contract`-style review of the payload diff before In Review.
- **Shared tenants DB (no API).** `tenant_maintenance` + `tenant_maintenance_tenants` are written by
  tenants-admin and read by the cockpit (TypeORM) and sc-saas-admin (Medoo). Column names in this spec are
  the contract between the three; any rename after SAN-2105 lands must be checked in all three repos. The
  migration must land before tenants-admin or sc-saas-admin read/write the new columns.
- **Tenant scoping (invariant 5).** Cockpit: filter by the domain-resolved tenant's `id`. sc-saas-admin:
  filter by this deployment's `tenant_users.id` (`$getDatabaseSettingsFromMainTable['id']`); reading the main
  DB is already the existing pattern (`subscriptions` at `modules/index.php:205`). tenants-admin is a
  platform-level tool (no scoping rule) but must never leak a window's tenant list into the public payload.
- **Auth (invariant 4).** No auth change. The new sc-saas-admin block runs before login and denies login while
  live; no new endpoint is added anywhere (the cockpit endpoints stay public as today).
- **Flags (invariant 1) / API contract owned by backend (invariant 2) / PowerPitch (invariant 6):** untouched.

## Test plan

- tenants: jest unit matrix for selection/precedence with injected `now` (AC-3..AC-5, AC-7); contract test;
  `npm run gates`; migration run on an empty MySQL 8.4 (CI `migrations` job) **and** on a copy holding the
  legacy placeholder row (AC-1/AC-2); boot `dist/main.js` after build.
- tenants-admin: `composer gates`; `php -l`; manual: create all-tenants window, selected-tenant window,
  validation errors, Start now / End now / Cancel; non-privileged role → 403.
- frontend: Karma `fakeAsync` spec for the timer both directions and the page inputs; `npm run gates`;
  manual on the dev tenant with a window 2 minutes ahead (hard-refresh for the service worker).
- admin: `composer gates`; `php -l`; manual: banner during notice, 503 page on a module page, on
  `auth/login`, JSON 503 on an ajax call, `health.php` still 200, other tenant unaffected.
- cross-repo smoke (dev, `ai_native_setup`): one `selected` window for the dev QA tenant only → PWA and
  admin show banner, then block at start, recover at end; a second tenant on the same cockpit sees nothing;
  sc-saas-backend untouched and serving.
- e2e: `sc-saas-e2e` `tenant-contracts` test passes; schedule no live window over the QA tenant during a
  suite run.

## Rollout

1. **SAN-2105 (tenants) first.** Migration via `npm run migration:deploy`, then app restart. Backward
   compatible: with no new-style windows the payload is identical to today, and a legacy manual row keeps
   working (AC-2). Because `synchronize: true` is still on, ship the entity and migration together and never
   rename/drop a column in this change.
2. **SAN-2106 (tenants-admin)** after the migration has run in that environment (it writes the new columns).
3. **SAN-2107 (frontend)** and **SAN-2108 (admin)** in either order after step 1. Until they ship, old
   clients keep reading `active`/`maintenance_on`, which the cockpit now computes, so scheduled windows already
   show/block on page load (the frontend without the in-session timer; sc-saas-admin keeps its own unscoped
   query until SAN-2108 — see Q5/Rollout risk below).
4. No feature flag: nothing changes until an operator creates a window.

Risk during the gap between steps 1 and 4: the old sc-saas-admin query (`active = 1`, unscoped) reads the
stored `active` column. If tenants-admin writes stored `active` only for legacy semantics (C2), a
`selected` window would show its banner to **every** tenant's admins until SAN-2108 ships. Mitigation: the
new tenants-admin must leave stored `active = 0` on new-style windows (the cockpit computes it), so the old
admin query ignores them. [INFERRED — requires validation]

Known limitation (unchanged): if `sanchiconnect-saas-tenants` itself is down, the PWA cannot learn about
maintenance at all; sc-saas-admin reads the shared DB directly and is unaffected by a cockpit restart.

## Out of scope

- sc-saas-backend API enforcement (503 during live maintenance) — phase 2 unless Q2 decides otherwise.
- Email/SMS/push notifications to tenant admins or users ahead of a window (Q3 recommendation).
- Recurring windows.
- Changing the existing `verify_tenant` secrets exposure or any other part of the payload.
- An audit log of who scheduled/started/ended a window beyond the existing `actual_start_time`,
  `actual_end_time`, `notes` columns. [NOT SPECIFIED IN SOURCE]

## Open questions

None — all resolved by Nirmal on 2026-10-27 (see Decisions).

## Decisions (2026-10-27, Nirmal)

1. **Link table.** One window can cover several selected tenants (`tenant_maintenance_tenants`).
2. **sc-saas-backend 503 enforcement → phase 2.** No backend change in this spec.
3. **No advance email/notification in v1.** The banner (PWA + sc-saas-admin) is the notice.
4. **Bypass.** sc-saas-admin: developer + super admin (`checkIsDevOrSuperAdminRole()`) can use the panel
   while live; `auth/login` stays reachable for everyone so they can sign in; everyone else gets the 503 page.
   `db_admin.php` is untouched (already `is_dev`-only). PWA: **no bypass** — every user sees the
   maintenance page.
5. **Legacy global-switch rows** stay as `scope = 'all'` manual-override rows (AC-2). The `maintenance_mode`
   inner shape stays `unknown` in the frozen contract for phase 1 (no regeneration, no backend issue).
6. **New `starts_at`/`ends_at` DATETIME (UTC) columns**; `start_time`/`end_time` keep their varchar type and
   are only made NULLable.

## Implementation notes (2026-10-27, spec-implementer)

Nothing committed yet; every change is uncommitted on `ai_native_setup` in its repo, awaiting the user's review.

- **Migration** `sanchiconnect-saas-tenants/src/core/database/migrations/1793113560684-TenantScopedMaintenance.ts`.
  Hand-written (no DB access to generate against); constraint names are explicit in the entities
  (`UQ_tenant_maintenance_tenants_window_tenant`, `IDX_tenant_maintenance_tenants_tenant`,
  `FK_tenant_maintenance_tenants_window`, `FK_tenant_maintenance_tenants_tenant`). Verified on local MySQL 5.7
  (deploy → no drift → revert → legacy row → run → no drift); the CI `migrations` job on MySQL 8.4 has not run yet.
- **Rule refinement, both readers:** a window can also be live with `starts_at` set and `ends_at` NULL (live until
  ended manually). Cockpit and sc-saas-admin both treat a NULL `starts_at` as the earliest when breaking ties.
- **Payload:** `startTime`/`endTime` carry the ISO-8601 UTC schedule when the window has one, and the stored legacy
  varchar otherwise (so a legacy manual row's payload is unchanged). `server_time` is included (the proposal is adopted).
- **PWA:** besides the boundary timer, the app re-fetches the tenant config once a minute **while live**, so
  End now / Cancel reach an open tab (AC-11). It does not poll during the notice period.
- **sc-saas-admin open routes while live** (Q4 says `auth/login` + logout): also `auth/callback-microsoft` (SSO
  completion of the same sign-in), `auth/backdoor_login` (one-time-token sign-in) and `partners/auth/logout`. Each
  lands on a gated page afterwards. Needs a nod in review.
- **tenants-admin:** the one-click global ON switch is gone. Immediate maintenance = a window starting now, or
  Start now on a scheduled one. Legacy manual rows are listed as "manual switch" and can be ended or cancelled.
- **Deploy order is a hard requirement:** SAN-2105 migration first. Before it, tenants-admin writes fail, and
  sc-saas-admin's helper returns null but reports the missing-column SQL error on every request.

