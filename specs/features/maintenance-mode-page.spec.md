---
id: maintenance-mode-page       # PENDING — Linear Project not yet created (no Linear connector tool
                                 # available in the session that drafted this spec, and the assignee
                                 # question below is still unanswered — both required before Linear
                                 # creation, per the workspace's standing process). Once the project is
                                 # created, rename this file to `SAN-<n>-maintenance-mode-page.spec.md`
                                 # and set `id`/`linear` below to match, per this repo's existing
                                 # convention (see SAN-539's spec for the pattern).
title: Platform-wide maintenance mode — admin switch + branded frontend page
type: feature
status: draft
linear: PENDING                 # set once the Linear Project is created (step 7/8 of the standing process)
owner: nirmal.s@sanchiconnect.com
repos: [sanchiconnect-saas-tenants-admin, frontend]
                                 # Dependency order is soft, not hard, here (see Rollout) — no schema or
                                 # API contract changes either side, so there is no strict build-order
                                 # requirement the way SAN-539 had. Listed admin-first because the admin
                                 # switch is what makes the frontend change meaningfully testable
                                 # end-to-end (today the only way to flip `maintenance_on` is a direct
                                 # DB edit).
contracts:
  api: []                       # No new/changed endpoints. Both repos consume the EXISTING
                                 # `GET /public/global/verify_tenant/:hostname` and
                                 # `GET /public/global/tenant-settings/:hostname` (sanchiconnect-saas-tenants,
                                 # global.controller.ts → global.service.ts), which already serialize the
                                 # full `TenantMaintenanceEntity` row verbatim as `maintenance_mode` on
                                 # every response. This spec adds a writer (admin) and a better reader
                                 # (frontend) for data that already flows end-to-end today — no contract
                                 # shape change on either endpoint.
  flags: []                     # `maintenance_on` is a column on `tenant_maintenance`
                                 # (sanchiconnect-saas-tenants), NOT a `TenantUsersEntity` boolean column
                                 # — it is not one of the workspace's `Feature`/`IFeatures`-style flags and
                                 # is not subject to invariant #1's four-consumer propagation rule. Noted
                                 # explicitly to avoid confusion with that pattern.
  events: []
tenant_scoped: false            # `tenant_maintenance` is a single GLOBAL row by design (no `domain`
                                 # column) — it is explicitly NOT tenant-scoped data. The admin write in
                                 # `sanchiconnect-saas-tenants-admin` is a platform-level cockpit write
                                 # (matching that module's own documented "no tenant-scoping rule here...
                                 # platform-level tool operating on global cockpit data" convention, see
                                 # `modules/tenant_management/module.spec.md`), not a per-tenant query.
                                 # The frontend read is the same global blob every tenant hostname already
                                 # receives identically. Invariant #5 does not apply to this feature.
depends_on: []
created: 2026-09-01
---

# Platform-wide maintenance mode — admin switch + branded frontend page

> **Superseded in part by [FT-007](FT-007-tenant-scheduled-maintenance.spec.md) (2026-10-27, SAN-2105..2108).**
> Read FT-007 first. The following points here are no longer true (FT-007 contradiction C5):
> - Evidence #6 ("`sc-saas-admin` has zero references to `maintenance_mode`"): it already read `tenant_maintenance`
>   (`modules/index.php`), and since FT-007 it shows the notice banner and **blocks the panel with a 503 while
>   maintenance is live** (developers / super admins can still sign in and work).
> - Evidence #7 ("tenants-admin has no UI for `tenant_maintenance`"): `modules/maintenance_mode.php` exists (59c91ea)
>   and since FT-007 schedules windows for all or selected tenants.
> - Out of scope "admins and partner staff must keep working during a maintenance window", the related acceptance
>   criterion, and the "global, all-tenants-at-once by design" / "no time-based activation" exclusions: replaced
>   by FT-007 (per-tenant windows, notice / start / end, sc-saas-admin blocked while live).
> The branded frontend maintenance page described here still applies; FT-007 adds inputs to it.

## Reference

Rough idea, not sourced from an existing Linear issue — no `/from-linear` pull. Drafted directly from a
product ask plus a prior session's direct code research (treated as ground truth per that research's own
instruction, re-verified this session anyway per spec-authoring practice #1 — see Evidence).

## Evidence — current code state (re-verified this session)

1. **`TenantMaintenanceEntity` confirmed exactly as described** — a single global row, no `domain` column
   (`sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-maintenance.entity.ts`): `title`
   (not null), `message` (nullable), `date`/`startTime`/`endTime` (not null), `active` (bool, default
   false), `maintenance_on` (bool, default false), `maintenance_on_title` (not null), `maintenance_on_message`
   (nullable), `actual_start_time`/`actual_end_time` (nullable timestamps), `notes` (nullable).
2. **A critical, non-obvious coupling found this session, not stated in the originating brief**:
   `TenantsService.getTenantsMaintenance()` (`tenants.service.ts:12-20`) is
   `TenantMaintenanceEntity.findOne({ where: { active: true }, order: { id: 'DESC' } })` — it filters on
   `active = true`, full stop. Because `maintenance_on` lives on that *same* row, **a row with
   `maintenance_on = true` but `active = false` is invisible to this query and is never returned to any
   client** — `maintenance_mode` on `verify_tenant`/`tenant-settings` would simply be `null`, and the
   frontend's hard block would never fire, silently. `active` is therefore not just "drives the dismissible
   banner" as the originating brief characterized it — it is also a hard prerequisite for the kill-switch
   itself to ever be seen. This must be surfaced clearly in the new admin UI (see Decisions #1) or an
   operator can toggle `maintenance_on` on, believe the site is now blocked, and be wrong.
3. **No server-side time enforcement exists.** `date`/`startTime`/`endTime` are pure display fields (already
   rendered as-is by the existing, unmodified dismissible banner in `app.component.html`/`.ts`); nothing in
   `getTenantsMaintenance()` compares them to the current time. `maintenance_on` is a fully manual switch —
   an operator must flip it at the start of a deploy and flip it back off at the end. This is an existing
   behavior, not something this spec changes, but worth stating plainly since the new admin UI is the first
   place an operator will interact with this mechanism directly.
4. **Frontend hard-block wiring confirmed exactly as described** — `app.component.ts:189-199`: on the
   `getBrandDetails` selector subscription, `if (this.brandDetails.maintenance_mode?.maintenance_on) { this.maintainanceMode = true }`. `app.component.html:79`: `<router-outlet>` gated
   `*ngIf="!tenantLoading && !tenantError && !maintainanceMode && subscriptionActive"` — a genuine, already-
   working hard block on all routes. The `*ngIf="maintainanceMode"` block (lines 21-37) is inline markup,
   byte-similar to the `tenantError` (lines 1-19) and `!subscriptionActive` (lines 40-56) blocks — all three
   share the same hardcoded `assets/images/logos/logo-2.svg` and generic "SaaS App" copy, not the tenant's
   actual branding.
5. **The dismissible banner is a separate, already-correct mechanism, confirmed untouched by this spec**:
   `app.component.html:58-77`, gated on `brandDetails?.maintenance_mode?.active && maintenanceClosed &&
   !maintainanceMode`, dismissed via `localStorage.setItem('maintainance_' + maintenance_mode.id, 'true')`
   (`app.component.ts:535-541`). This spec does not modify this block or its logic in any way.
6. **`sc-saas-backend`/`sc-saas-admin` confirmed to have zero references to `maintenance_mode`** — full
   grep, no matches. Consistent with the explicit constraint that admins/partner staff must keep working
   during a maintenance window; this spec does not add any gating to either repo.
7. **`sanchiconnect-saas-tenants-admin` has no existing UI for `tenant_maintenance`** — confirmed via grep,
   zero matches for `tenant_maintenance` anywhere in that repo. Today the row can only be hand-edited
   directly in the DB (or via the generic dynamic-table engine if the table were registered in
   `spa_data_management`, which it currently is not).
8. **Two viable admin implementation patterns exist in this repo; the generic dynamic-CRUD engine is the
   wrong fit here.** Per that repo's own `CLAUDE.md`, `add.php`/`edit.php`/`table.php`/`detail.php` is one
   generic engine, parameterized by table, driven by `spa_data_management` field metadata and an optional
   `spa_form_layouts`/`spa_form_sections` override — with a documented landmine ("Creating a
   `spa_form_layouts` row for a table without fully building out its sections produces a blank add/edit
   form"). `tenant_management/module.spec.md` documents that module deliberately *not* using this generic
   engine for a similarly bespoke, low-cardinality entity ("hand-validates its own POST fields, same pattern
   as `ai_credits`... The generic engine's 'blank form' landmine does not apply to anything in this
   module"), instead following a small, self-contained, hand-built module with a copy-pasted role gate. A
   single-global-row entity like `tenant_maintenance` is an even weaker fit for the generic engine (which is
   built around lists of many independent records with Add/Edit/Table/Detail) than `tenant_management`'s
   case was — see Decisions #1.
9. **Role gate pattern confirmed, copy-pasted identically across `tenant_management`, `ai_credits`, and
   `developer/settings_management.php`**: `if ($_SESSION['admin_roles']['code'] == super_admin_role_id ||
   $_SESSION['admin_roles']['code'] == developer_role_id) { } else { header("Location:" . _admin_url .
   "/403"); exit; }`, with role-id constants defined from ENV in `config/config.php` (`super_admin_role_id`,
   `developer_role_id`, plus `reviewer_role_id`/`recruitmentpartner_role_id`/`jury_role_id`/
   `program_manager_role_id`/`analyst_role_id` — none of the latter five are used to gate
   `tenant_management`/`settings_management`, i.e. this class of platform-operator screen is consistently
   restricted to `super_admin`/`developer` only).
10. **`IMaintenance` (frontend) confirmed as an exact mirror of the entity**
    (`core/domain/brand.model.ts:217-232`), already wired into `IBrandDetails.maintenance_mode`. No frontend
    model change is needed — the existing interface already carries every field the new component needs.
11. **The existing inline maintenance card renders a hardcoded generic logo, not the tenant's own branding**
    — confirmed (`app.component.html:26`, `src="assets/images/logos/logo-2.svg"`). The correct, established
    pattern for rendering the tenant's actual logo elsewhere in this app is `globalSettings.branding.logo`
    piped through the `imagekitUrl` pipe (confirmed in `job-interview.component.ts:174` and
    `meeting.component.ts:242`: `this.imagekitUrl.transform(this.globalSettings.branding.logo)`) —
    `IBranding.logo` (`core/domain/settings.model.ts:41-52`) is the field to use.
12. **`PageNotFoundComponent` precedent re-read carefully; one correction to the originating brief's
    framing.** `page-not-found.module.ts` is a *routed* lazy module (`RouterModule.forChild`) — but the
    maintenance page is not, and cannot be, reached via a route: it is rendered directly inside
    `app.component.html`, gated by a plain component boolean (`maintainanceMode`), specifically so it can
    block the `<router-outlet>` itself (Evidence #4) — wrapping it in its own lazy route module would be
    inapplicable, not just unnecessary. The part of the `page-not-found` precedent that *does* apply is
    different: `PageNotFoundComponent` is declared and exported by `SharedModule`
    (`shared/shared.module.ts`), not by its own routing module (whose `declarations` array has it commented
    out), and `AppModule` already imports `SharedModule` (`app.module.ts:13,69`) — so a new shared component
    declared the same way is directly usable in `app.component.html` with no new module/route needed. This
    spec follows that half of the precedent (`SharedModule`-declared reusable component, no store/service
    dependencies of its own, matching `page-not-found/module.spec.md`'s own stated invariant: "no
    data-fetching or state dependencies").

## Decisions (made this session, with evidence — not left as open questions)

1. **Admin implementation: a small, self-contained, hand-built module — not the generic dynamic-CRUD
   engine.** New directory `modules/maintenance_mode/` in `sanchiconnect-saas-tenants-admin`, mirroring
   `modules/tenant_management/`'s and `modules/ai_credits/`'s established pattern (own PHP files, own
   hand-validated POST handling, copy-pasted `super_admin_role_id`/`developer_role_id` gate on every file —
   see Evidence #8-9), rather than registering `tenant_maintenance` in `spa_data_management` for the generic
   engine. Reasons: (a) it is a genuinely singleton entity (fetch-latest/create-or-update), a poor fit for
   an engine built around lists of many records; (b) it sidesteps the documented `spa_form_layouts` blank-
   form landmine entirely, matching `tenant_management`'s own stated rationale for avoiding the generic
   engine.
2. **Single-screen UI, not list+create+edit+detail.** One file (`edit.php`) that fetches the most recent
   `tenant_maintenance` row (`ORDER BY id DESC LIMIT 1`, no `active` filter — the operator must be able to
   see/edit the row even while it's currently inactive) and renders a form over every column; if no row
   exists yet, renders an empty form (first-time setup, `INSERT`); if a row exists, pre-fills and updates it
   (`UPDATE ... WHERE id = :id`). This matches the originating brief's own framing ("create/update of the
   single row") and Evidence #2's finding that there is exactly one row that matters at a time.
3. **Server-side validation blocks the silent no-op case from Evidence #2**: saving with `maintenance_on =
   true` and `active = false` simultaneously is rejected with an explicit inline error explaining that
   `active` must also be on for the kill-switch to take effect (rather than silently auto-checking `active`
   on the operator's behalf, which could surprise someone who deliberately wants the banner off). This is a
   new, real validation rule with no other rows/records or cross-tenant concern involved.
4. **Frontend: a new `SharedModule`-declared component, not a routed module** — `MaintenancePageComponent`
   in `src/app/shared/common-components/maintenance-page/`, declared + exported by `SharedModule` exactly as
   `PageNotFoundComponent` is (Evidence #12), consumed directly from `app.component.html`. Presentational
   only (inputs in, no store/service dependency of its own), matching the `page-not-found` module's own
   stated invariant against adding data-fetching dependencies to a component reached from arbitrary
   app-bootstrap states.
5. **Tenant branding wired via the established `branding.logo` + `imagekitUrl` pattern** (Evidence #11),
   replacing the hardcoded generic logo — this is the concrete fix for gap #2 in the originating brief
   ("tenant-branded maintenance page").

## Problem

`tenant_maintenance` (`sanchiconnect-saas-tenants`) already has a working, correctly-wired hard kill-switch
(`maintenance_on`) that blocks every route in `sc-saas-frontend` during a deploy — but there is no way to
flip it except a direct hand-edit of the tenants DB, and the page it renders is generic, inline, duplicated
markup shared with two unrelated app-states (`tenantError`, `!subscriptionActive`), not a real branded
maintenance page. This spec closes both gaps: an admin-manageable switch in the tenants control-plane
operator console, and a proper, reusable, tenant-branded maintenance page component in the frontend.

## Acceptance criteria

- [ ] A platform operator with `super_admin` or `developer` role can, from
      `sanchiconnect-saas-tenants-admin`, view the current `tenant_maintenance` row's fields (`title`,
      `message`, `date`, `startTime`, `endTime`, `active`, `maintenance_on`, `maintenance_on_title`,
      `maintenance_on_message`, `actual_start_time`, `actual_end_time`, `notes`) and update them; if no row
      exists yet, they can create the first one.
- [ ] A platform operator without `super_admin`/`developer` role is redirected to `/403` when attempting to
      reach the new module's screen (matching the existing `tenant_management`/`ai_credits`/
      `settings_management` role-gate convention).
- [ ] Saving with `maintenance_on = true` and `active = false` is rejected with a clear inline validation
      error (per Decision #3) instead of silently persisting a row the backend's `getTenantsMaintenance()`
      query (`WHERE active = true`) would never actually select.
- [ ] Setting `maintenance_on = true` together with `active = true` and saving causes
      `GET /public/global/verify_tenant/:hostname` and `GET /public/global/tenant-settings/:hostname`
      (unchanged endpoints) to return the updated `maintenance_mode` object on the very next call — no
      backend deploy needed, since this is a plain row update through the existing, unmodified contract.
- [ ] With that same row live, `sc-saas-frontend` renders the new `MaintenancePageComponent` (not the old
      inline card) showing the tenant's own logo (`branding.logo` via `imagekitUrl`, not the hardcoded
      generic asset), `maintenance_on_title`, and `maintenance_on_message`, and the `<router-outlet>`
      remains fully blocked exactly as it does today (no regression to the existing hard-block gating logic
      in `app.component.ts`/`.html`).
- [ ] Setting `maintenance_on = false` (with the same row still `active = true`) restores normal app access
      immediately on next load — no change to this existing behavior.
- [ ] The pre-existing dismissible banner (`active`-driven, `maintenanceClosed`/`handleCloseNotice()`) is
      verified unchanged — still renders/dismisses exactly as it does today, independent of whether the new
      admin screen or the new frontend component were touched.
- [ ] `sc-saas-backend` and `sc-saas-admin` remain completely unmodified and ungated by `maintenance_mode` —
      admins and partner staff can keep working normally during a maintenance window.
- [ ] `php -l` passes clean on every new/changed admin PHP file; frontend `npm run build` and `npm test`
      (scoped to the new component and `app.component`) pass.

## Per-repo plan

### sanchiconnect-saas-tenants-admin

- New module directory `modules/maintenance_mode/`, following `modules/tenant_management/`'s file-naming
  convention (routed via the front controller's `action=maintenance_mode/<name>` pattern):
  - `setup_menu.php` — idempotent sidebar seeder (title + a known sub-menu `external_link` check, matching
    `tenant_management/setup_menu.php`'s idempotency fix over the older `finance_management` convention),
    adding a single "Maintenance Mode" menu entry.
  - `edit.php` — the only real screen (Decision #2):
    - Role gate at the top of the file: the same four-line `super_admin_role_id`/`developer_role_id` check
      as `tenant_management`/`ai_credits`/`settings_management` (Evidence #9), independently on this file
      (not relying solely on menu visibility).
    - `checkLoggedIn()`, then `include(getcwd() . "/modules/common.php")`.
    - GET: `$row = $database->get("tenant_maintenance", "*", ["ORDER" => ["id" => "DESC"]]);` — render the
      form pre-filled if `$row` exists, empty otherwise.
    - POST (`submitAction == "saveMaintenance"`): `verifyCSRFToken()`, `cleanValues($_POST)`, required-field
      checks on `title`/`maintenance_on_title`/`date`/`startTime`/`endTime` (matching the entity's
      `nullable: false` columns), the `maintenance_on && !active` validation from Decision #3, then
      `$database->update("tenant_maintenance", $data, ["id" => $row['id']])` if a row id was posted, else
      `$database->insert("tenant_maintenance", $data)`.
  - No `spa_data_management`/`spa_form_layouts` registration for this table (Decision #1) — hand-built form
    only, sidestepping the generic-engine landmine entirely.
  - `php -l` on both files before done.

### frontend

- New shared component `MaintenancePageComponent`
  (`src/app/shared/common-components/maintenance-page/maintenance-page.component.{ts,html,scss}`):
  - `@Input() maintenance: IMaintenance` (already-existing interface, Evidence #10 — no model change
    needed), `@Input() branding: IBranding`, `@Input() imgKitUrl: string` — presentational only, no
    store/service injection (Decision #4, matching `page-not-found`'s stated invariant).
  - Template: logo via `[src]="imgKitUrl + branding.logo | ..."` (or the existing `imagekitUrl` pipe used
    identically to `job-interview.component.ts:174`/`meeting.component.ts:242`), `{{ maintenance.maintenance_on_title | titlecase }}`, `{{ maintenance.maintenance_on_message }}` — same copy fields the
    existing inline card already renders, just sourced from real branding instead of a hardcoded asset.
  - Declared **and exported** by `SharedModule` (`shared/shared.module.ts`), exactly as `PageNotFoundComponent`
    is (Evidence #12) — no new Angular module, no route.
- `app.component.html`: replace the `*ngIf="maintainanceMode"` block (lines 21-37) with
  `<app-maintenance-page *ngIf="maintainanceMode" [maintenance]="brandDetails.maintenance_mode" [branding]="globalSettings?.branding" [imgKitUrl]="globalSettings?.imgKitUrl"></app-maintenance-page>`.
- No change to `app.component.ts`'s `maintainanceMode` boolean-setting logic (lines 189-199), the dismissible
  banner block (lines 58-77) or its backing methods (`maintenanceClosed`, `handleCloseNotice`,
  `formatMaintenanceTime`), or the `tenantError`/`!subscriptionActive` inline cards — all explicitly out of
  scope (see Out of scope).
- karma/jasmine: new spec for `MaintenancePageComponent` (renders title/message/logo from inputs); extend
  `app.component.spec.ts` if it exists to assert the new component is rendered (not the old inline markup)
  when `maintainanceMode` is true — else a manual verification note.

## Contracts & invariants

- **API:** No path/method/DTO changes anywhere. Both repos consume the existing
  `GET /public/global/verify_tenant/:hostname` / `GET /public/global/tenant-settings/:hostname` contract
  (owned by `sanchiconnect-saas-tenants`) exactly as it already behaves — `sanchiconnect-saas-tenants-admin`
  writes the same DB row those endpoints already read (no new column, no schema change, `synchronize`
  irrelevant here since no entity changes); `sc-saas-frontend` renders the same `maintenance_mode` payload
  shape it already receives (`IMaintenance`, unchanged). Invariant #2 (API contract) and invariant #3
  (tenant-verification contract) are both touched only in the sense of "a new writer/reader of pre-existing,
  unchanged data" — no `/audit-contract` risk in the DTO-change sense, but still worth a final check before
  `in-review` given `sanchiconnect-saas-tenants-admin` writes directly into the shared DB the NestJS app also
  reads (per that repo's own "Shared DB warning": a TypeORM migration there can break Medoo queries here, and
  vice versa — not applicable in this direction since this spec adds no new column, but flagged per
  standing practice).
- **Flags:** none — see `contracts.flags` note in frontmatter (this is a `tenant_maintenance` column, not a
  `TenantUsersEntity` flag).
- **Events:** none.
- **Tenant scoping (invariant #5):** does not apply — `tenant_maintenance` is a global, non-tenant-scoped
  table by design (no `domain` column); the admin write is a platform-level cockpit write (matching
  `tenant_management`'s own documented "no tenant-scoping rule" convention), not a per-tenant query.
- **Auth (invariant #4):** unaffected — this feature adds no new authenticated endpoint; the admin screen is
  gated by the existing session-based RBAC role check (Evidence #9), and the two consumed cockpit endpoints
  are already public/unauthenticated exactly as they are today (unchanged by this spec).
- **Cross-repo contract impact (spec-authoring practice #4):** none. This is the rare case where a two-repo
  feature introduces zero new contract surface — the mechanism (entity, columns, both endpoints' response
  shape, the frontend's hard-block gating logic) already exists and already works correctly end-to-end;
  this spec only adds a UI on each end of an already-complete pipe. `sc-saas-backend` and `sc-saas-admin` are
  read-only context, confirmed to have zero references to `maintenance_mode` (Evidence #6) and remain
  untouched — no implementation issue is created for either.

## Test plan

- sanchiconnect-saas-tenants-admin: `php -l modules/maintenance_mode/*.php`. Manual walkthrough as
  `super_admin`/`developer`: create the first row, toggle `maintenance_on` with `active` off (expect
  validation error), toggle both on and save (expect `verify_tenant`/`tenant-settings` to reflect it
  immediately), toggle `maintenance_on` off (expect app access restored). Manual walkthrough as a
  non-privileged role: expect `/403`.
- frontend: karma/jasmine for `MaintenancePageComponent` (title/message/logo bind from inputs correctly,
  including a null/undefined `branding` case falling back gracefully); `npm run build`. Manual visual check:
  with a live `maintenance_on = true` row, confirm the branded page renders (correct tenant logo, correct
  title/message) and `<router-outlet>` is fully blocked, on both a fresh load and an in-session NgRx update.
- cross-repo smoke check: flip `maintenance_on` via the new admin screen against a staging tenant, confirm
  the staging frontend blocks within one `verify_tenant`/`tenant-settings` refresh cycle with no frontend or
  backend deploy required (this is intentionally already true today for a direct DB edit — this check simply
  confirms the new admin write path produces the identical effect); confirm `sc-saas-backend`/`sc-saas-admin`
  remain fully usable throughout.

## Rollout

No strict cross-repo ordering constraint (unlike a schema/contract change) — the underlying entity, columns,
and both endpoints' behavior are all pre-existing and unchanged. The admin change and the frontend change are
independently deployable in either order:
- Admin ships alone: operators gain a real UI for a mechanism that already works via direct DB edit today —
  no behavior change for end users until it's actually used.
- Frontend ships alone: the maintenance page becomes properly branded immediately, using whatever data is in
  the row today (including `null`, in which case `maintainanceMode` is simply never `true` and the new
  component never renders — same as today).

No feature flag needed — both changes are additive UI over an existing, already-safe mechanism (the hard
block itself, `maintenance_on`, defaults to `false` and has been live and working prior to this spec).

**Known limitation, explicitly accepted, not solved by this feature:** if `sanchiconnect-saas-tenants` itself
is what's being deployed/restarted, the `verify_tenant`/`tenant-settings` call carrying `maintenance_mode`
will itself fail during that specific window — this mechanism covers `backend`/`frontend`/`admin` deploys
only, where the tenants control plane stays up. Out of scope to solve; documented here so it isn't
rediscovered as a "bug" later.

## Out of scope

- Any change to `sc-saas-backend` or `sc-saas-admin` — both remain fully usable during a maintenance window
  by explicit product decision (Evidence #6).
- Any change to the existing dismissible banner mechanism (`active`-driven, `app.component.html:58-77`) —
  confirmed already correct, referenced only as sibling context (Evidence #5, Decision — untouched).
- Adding a `domain`/tenant-scoping column to `tenant_maintenance`, or making the switch per-tenant — the
  global, all-tenants-at-once behavior is by design and matches the existing entity (Evidence #1).
- Server-side time-based auto-activation from `date`/`startTime`/`endTime` — the switch remains fully manual,
  exactly as it is today (Evidence #3); adding scheduling automation would be a separate, larger feature.
- Covering the case where `sanchiconnect-saas-tenants` itself is the service being deployed (see Rollout's
  Known limitation).
- Any run-history/audit log for who flipped `maintenance_on` and when — the entity already has `notes`,
  `actual_start_time`, `actual_end_time` as free-text/manual fields for this purpose; no new audit table is
  proposed.

## Open questions

None. All product decisions were resolved in the originating brief and confirmed against real code this
session (see Evidence/Decisions); the one non-obvious behavior discovered during verification (the
`active`/`maintenance_on` coupling, Evidence #2) is resolved with a concrete validation rule (Decision #3),
not left as an ambiguity.
