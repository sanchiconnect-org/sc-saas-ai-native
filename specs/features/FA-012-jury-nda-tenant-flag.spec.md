---
id: FA-012                      # next free FA- id (FA-011 is the last in specs/features). Linear: parent SAN-1748 (tenants) with sub-issues SAN-1749, SAN-1750, SAN-1751, SAN-1752.
title: Tenant-level switch to enable Jury NDA Signing (hide the Jury NDA card when off)
type: feature
status: approved                # draft -> approved -> in-progress -> in-review -> done. Approved by Sandeep 2026-10-07: all open questions confirmed (see Open questions).
linear: https://linear.app/sanchiconnect/issue/SAN-1748   # parent issue; the main session replaces this with the Linear Project URL once the project exists
owner: sandeep.k@sanchiconnect.com
repos: [tenants, admin, sanchiconnect-saas-tenants-admin, backend]   # dependency order. admin appears once but carries two issues (SAN-1750 foundation, then SAN-1751 UI). Build order: SAN-1748 -> SAN-1750 -> SAN-1749 and SAN-1751 -> SAN-1752. frontend, 3rdparty-webservices, ai-startups-analyzer deliberately NOT touched.
contracts:
  api: []                       # no route added or changed. SAN-1752 may decide a backend route gate (Open question 5); until decided, none.
  flags:
    - "jury_nda_enabled   (CONFIRMED by Sandeep 2026-10-07 - Open question 1). NEW nullable boolean column on tenant_users (TenantUsersEntity), NULL = off. Owner: tenants. Consumers: sc-saas-admin config.php constant (required), sanchiconnect-saas-tenants-admin operator toggle (required), backend Feature enum (undecided, SAN-1752), frontend IFeatures (not needed)"
  events: []
tenant_scoped: true             # the flag is read from the per-request tenant_users row; it gates tenant data (NDA rounds, acceptances, signed PDFs)
depends_on: [FA-010]            # the NDA feature this switch gates. FA-010 is status approved and its admin build is in the working tree; FA-010 must be built before this can be tested end to end.
created: 2026-10-07
---

# Tenant-level switch to enable Jury NDA Signing (hide the Jury NDA card when off)

## Source & evidence status

- **Requirement source:** Linear SAN-1748 and sub-issues SAN-1749..SAN-1752, as relayed by the main session (the Linear issue body itself was not read by this drafting pass). Behaviour and build order below were decided by the user and are not re-litigated here.
- **Evidence tags:** `[VERIFIED]` = read in code at the cited `file:line` on 2026-10-07. `[INFERRED]` = reasoned from code but not executed or not fully read. `[PENDING]` = unresolved design decision, listed under Open questions, with a proposal that is a proposal only.
- **Repos checked:** `sanchiconnect-saas-tenants`, `sanchiconnect-saas-tenants-admin`, `sc-saas-admin`, `sc-saas-backend` (all present under `SanchiSaaS/`). No code was edited.

## Problem

FA-010 shipped Jury NDA Signing with **no tenant flag**: the per-round `nda_required` default is the only switch (FA-010 D-Flag, `specs/features/FA-010-jury-nda-signing.spec.md:61`, restated :209). In practice every tenant whose backend has created the NDA schema sees the "Require jury to sign NDA" card in Round Settings and the rest of the NDA surface, whether or not they want it. [VERIFIED: `sc-saas-admin/includes/jury_nda_functions.php:81-100` shows the only availability test is whether the schema exists; no flag is read.] Operators need a per-tenant switch that makes the whole feature unavailable for tenants that have not bought or asked for it, and costs existing NDA users nothing once switched on. FA-010 anticipated exactly this: "If product later wants a tenant switch: `jury_nda_enabled` ... `tenant_users` column in tenants -> backend `Feature` enum -> admin `config.php` with `?? "0"`" (FA-010:209).

## Behaviour (decided by the user)

- **Flag OFF** = Jury NDA fully unavailable for that tenant: no NDA card in Round Settings, no tracker / exports / reminders, no BRL-03 gate, no juror pop-up / badges / My NDA, no NDA emails, and the NDA endpoints answer as unavailable.
- **Flag ON** = exactly as today (FA-010 behaviour, unchanged).
- **NULL or missing = OFF** (fail closed). Only the exact string `"1"` from the tenant row counts as on.

## Prior art (reuse, do not invent)

| Need | Existing mechanism | Decision |
|---|---|---|
| Nullable flag column, NULL = off | `ai_voice_agent_enabled`: `@Column({ name, width: 1, type: 'boolean', nullable: true, default: null })`, TS type `boolean \| null` (`sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-users.entity.ts:634-643`) [VERIFIED] | **REUSE** exact pattern |
| Non-null jury flag, default false | `limit_jury_access_enabled` (FA-011) `default: false` (`tenant-users.entity.ts:2451-2463`) [VERIFIED] | Reference only; user chose nullable |
| Flag -> admin PHP constant | `define('ai_voice_agent_enabled', $getDatabaseSettingsFromMainTable["ai_voice_agent_enabled"] ?? "0")` guarded by `if(!defined(...))` (`sc-saas-admin/config/config.php:149-152`) and the FA-011 equivalent (`config.php:126-130`) [VERIFIED]. The row is `tenant_users` selected by `admin_domain` / `admin_custom_domain` = request hostname (`config.php:66-69`) [VERIFIED] | **REUSE** |
| Admin-side flag helper | `limitJuryAccessEnabled()` reads `defined('limit_jury_access_enabled') && (string) constant(...) === "1"` (`sc-saas-admin/includes/jury_visibility_functions.php:25-29`), plus a developer-role bypass (:19-23, :30-33) [VERIFIED] | **REUSE the `=== "1"` test**; the dev bypass is an open question (Open question 6) |
| Operator toggle | tenants-admin Tenant Management edit page renders boolean switches from `getTenantSwitchSections()` (`sanchiconnect-saas-tenants-admin/modules/tenant_management/_switch_sections.php:23-189`), read in `edit.php:35-39` and `edit.php:58-60` [VERIFIED]. `ai_voice_agent_enabled` is listed at `_switch_sections.php:186` [VERIFIED] | **EXTEND**: add the new field to a section |
| Round-settings card availability | `$tpl->juryNdaAvailable = juryNdaSchemaReady($database) ? "1" : "0"` (`sc-saas-admin/modules/application_management/edit_program_round.php:2759`); template wraps the card in `<?php if ($juryNdaAvailable === "1") { ?>` (`themes/default/html/application_management/edit_program_round.php:454,460`) [VERIFIED] | **REUSE**: gating `juryNdaSchemaReady()` hides the card |

## Evidence: what the flag has to turn off in sc-saas-admin

All [VERIFIED] unless tagged.

- **Single availability probe.** `juryNdaSchemaReady($database)` (`includes/jury_nda_functions.php:81-100`) is memoised per database object and checks the two NDA tables plus `application_program_rounds.nda_required` / `nda_requirement_type`. Its docblock: "When it has not, NDA is treated as OFF everywhere (the toggle UI is hidden, the gate allows)" (:76-80).
- **Callers of that probe** (every one becomes flag-aware if the check lives inside it): :165 (`juryNdaState`), :635 (`juryNdaGateDecide`, returns allow `schema_off`), :811 (`juryNdaHasData`, delete protection - see hazard below), :1112 (`juryNdaSaveSettings`), :1527 (`juryNdaUploadVersion`), :1727 (`juryNdaReplaceVersion`), :1993 (`juryNdaJurorAction`), :2588 (`juryNdaPreviewAction`), :3365 (`juryNdaDashboardBadges`), :3409 (`juryNdaDashboardPopup`), :3777 (`juryNdaTrackerAuthorise`, answers `404 "unavailable"`).
- **BRL-03 gate.** `enforceJuryNdaGate()` is called once from `index.php:62` before any module loads; `juryNdaGateDecide()` allows when the schema probe fails (`jury_nda_functions.php:626-637`). A false probe therefore means "no gate", which is the required OFF behaviour.
- **Round Settings card:** module sets `juryNdaAvailable` (`modules/application_management/edit_program_round.php:2759`) and loads versions, signers and history only when it is `"1"` (:2761-2770); template card at `themes/default/html/application_management/edit_program_round.php:460`.
- **Tracker and alerts:** `modules/application_management/edit_program_round.php:2801-2818`, guarded by `$tpl->juryNdaAvailable === "1" && juryNdaCanViewNdas($_SESSION)` (:2803).
- **NDA admin endpoints (POST handlers and routes):** `submitAction` handlers `jury_nda_upload_version` (`edit_program_round.php:269`), `jury_nda_replace_version` (:311), `jury_nda_save_settings` (:364); route `application_management/jury_nda_tracker` (`modules/application_management/jury_nda_tracker.php`, actions via `juryNdaTrackerAction` :16: juror details, signed copy, reminders, retry copy, export); route `application_management/jury_nda_preview` (`jury_nda_preview.php:15-49`); Super Admin retention save `save_jury_nda_retention` (`modules/developer/settings_management.php:243`) and the retention card (`themes/default/html/developer/settings_management.php:179-182`), plus `modules/developer/jury_nda_retention.php` and `jury_nda_retention_delete.php` (files exist; their entry checks were not read - [INFERRED] they need the same gate).
- **Juror-side:** route `jury/nda` (`modules/jury/nda.php:1-21` renders the modal page, :56 runs `juryNdaJurorAction`); dashboard badges (`modules/jury/dashboard.php:212`); round banner, notice, My NDA link and optional popup (`modules/jury/round-applications.php:859-866`).
- **Permission row:** "Can View Jury NDAs?" selects at `themes/default/html/auth/admins.php:517-521` (guarded by `$juryNdaPermissionAvailable === "1"`, set at `modules/auth/admins.php:883` from `juryNdaPermissionColumnReady($database)`) and the second copy at `admins.php` template :1196-1203 [VERIFIED lines; the guard around the second copy was not read, [INFERRED] same guard]. The permission column probe is a different function from `juryNdaSchemaReady()` (`jury_nda_functions.php:858`), so the probe change alone does not hide this row.
- **Delete protection (must stay on).** `juryNdaHasData()` returns "no data, ok" when `juryNdaSchemaReady()` is false (`jury_nda_functions.php:811-813`); it backs `deleteRound` (`submission-application-management.php:404-406`) and `deleteApplicationProgram` (`program.php:1022-1024`) and the partner path (`modules/partners/list.php:620-622`). See Open question 4: a flag check placed inside `juryNdaSchemaReady()` would switch this protection off with the flag.
- **Backend NDA routes.** `POST api/v1/admin-actions/jury-nda-signed-copy-email/:adminMd5` (`sc-saas-backend/src/modules/global/admin-actions/admin-actions.controller.ts:985`) and `jury-nda-notification-email/:adminMd5` (:1012). The controller carries a class-level `@UseGuards(FeatureGuard)` (:64) but neither NDA route has a `@Features(...)`. [VERIFIED] Backend module spec: "no feature flag by design (spec FA-010, D-Flag)" (`sc-saas-backend/src/modules/jury-nda/module.spec.md:17`). Retry cron: `RetryJuryNdaEmailsService` registered in `modules/cron/cron.service.ts:714-727` [VERIFIED].
- **FeatureGuard semantics.** The guard denies only when `saasFeatures[feature] === false` (`sc-saas-backend/src/core/guards/feature-guard.ts:18`) [VERIFIED]: an `undefined` flag passes. NULL-means-off therefore cannot be enforced by `FeatureGuard` alone (Open question 5).

## Evidence: tenants and tenants-admin

- **tenants entity:** pattern at `tenant-users.entity.ts:634-643`. `synchronize: true` is on in all envs, so adding the column is applied on next deploy and removing/renaming auto-drops it (`sanchiconnect-saas-tenants/CLAUDE.md`, Guardrails) [VERIFIED].
- **verify_tenant / tenant-settings:** `global.service.ts` carries three hand-maintained lists. FA-011's flag appears in all three (`:341` select, `:694` verify_tenant mapping, `:942` tenant-settings field list) [VERIFIED]. `ai_voice_agent_enabled` appears in none of them (grep over `sanchiconnect-saas-tenants/src` finds it only in the entity and module specs) [VERIFIED], consistent with it being an admin-only flag. Admin reads the `tenant_users` row directly (`config.php:66`), not these endpoints, so admin does not need the response shape to change.
- **tenants-admin grouping is a closed list.** `_switch_sections.php` states "All 223 boolean tenant_users columns are accounted for" (:12-14), and `tenant_management/module.spec.md:89-95` says the module manages exactly those columns. A new column is **not** shown until it is added to a section [VERIFIED]. `limit_jury_access_enabled` is not in `_switch_sections.php` (grep over `sanchiconnect-saas-tenants-admin` finds only `ai_voice_agent_enabled`), so the "223 accounted for" claim is already stale for FA-011 [VERIFIED by grep]. Section "Jury & Review" currently lists `request_call_jury`, `jury_questions`, `show_documents_to_jury` (:62-67) [VERIFIED] and is the natural home.
- **NULL rendering.** `edit.php:59` coerces a NULL or falsy column to `0` for display; how the save path writes the value (0 vs NULL) was not read past line 97 [INFERRED]. For a nullable column, saving the form probably turns NULL into `0` for every tenant edited, which is harmless (both off) but should be confirmed.
- **Generic engine alternative.** The bespoke Tenant Management module "does not touch modules/edit.php or spa_data_management" (`tenant_management/edit.php:9`); `spa_data_management` metadata only matters for the generic `edit/tenant_users` engine, which this spec does not use [VERIFIED].

## Acceptance criteria

All must pass for `done`.

**Flag in the control plane (SAN-1748)**
- [ ] AC-1 `TenantUsersEntity` has a nullable boolean column named per the confirmed flag name (proposal `jury_nda_enabled`), `default: null`, TS type `boolean | null`, same pattern as `tenant-users.entity.ts:634-643`. A tenant row created without a value reads NULL.
- [ ] AC-2 Existing tenants are handled per the decision in Open question 2; no existing NDA user silently loses the gate.

**Admin foundation (SAN-1750)**
- [ ] AC-3 `sc-saas-admin/config/config.php` defines a constant with the same snake_case name from the tenant row with `?? "0"`, guarded by `if (!defined(...))`, in the pattern of `config.php:149-152`.
- [ ] AC-4 One fail-closed check: NDA is available only when the constant is defined and `(string) constant(...) === "1"`; any other value (NULL, "", "0", undefined) is unavailable. The check lives where it makes every `juryNdaSchemaReady()` caller flag-aware (subject to Open question 4 about delete protection).
- [ ] AC-5 With the flag OFF, `enforceJuryNdaGate()` allows every jury route (no BRL-03 gate, no redirect, no modal) and `juryNdaState()` reports `not_applicable`, never `blocking`.

**Operator toggle (SAN-1749)**
- [ ] AC-6 Platform operators can switch the flag on and off per tenant in tenants-admin Tenant Management Create and Edit (and see it in Detail), in a named section.
- [ ] AC-7 The change is stored in the tenants DB and takes effect in sc-saas-admin on the next request (admin reads the `tenant_users` row per request, `config.php:66`), with no admin redeploy.

**Admin surfaces (SAN-1751)** - with the flag OFF:
- [ ] AC-8 The Jury NDA card is absent from Round Settings -> Jury allotment (`edit_program_round.php` template :460).
- [ ] AC-9 No tracker, tiles, alerts, exports or reminders render, and the tracker route answers unavailable (`jury_nda_tracker.php`, `juryNdaTrackerAuthorise` already answers `404 "unavailable"` when the probe is false, `jury_nda_functions.php:3777-3778`).
- [ ] AC-10 The upload / replace / save-settings handlers and `jury_nda_preview` do not act and answer unavailable (no DB write, no S3 write).
- [ ] AC-11 The Super Admin retention card in settings_management is not rendered, subject to Open question 3 (the user decision is to hide it).
- [ ] AC-12 The "Can View Jury NDAs?" permission row is not shown in `auth/admins.php` add/edit, and a posted `can_view_jury_ndas` is ignored while OFF.
- [ ] AC-13 Juror side: no NDA pop-up, badges, banner, My NDA link or `jury/nda` page for any juror; no round or application route is blocked by an NDA; no NDA email is triggered from admin.
- [ ] AC-14 With the flag ON, behaviour is byte-identical to today (FA-010 acceptance criteria still pass).
- [ ] AC-15 Delete protection (FA-010 AC-24) still refuses deleting a programme or round that holds NDA rows regardless of the flag, per the decision in Open question 4.

**Backend (SAN-1752)**
- [ ] AC-16 A recorded decision on whether the NDA endpoints, the retry cron and a `Feature` enum entry need the flag, with the reason. If the answer is "no code", the module spec says so and `/trace-flag` shows the backend gap as intentional. If any code is added it must not rely on `FeatureGuard` for NULL-means-off (see evidence above).

**Cross-repo**
- [ ] AC-17 (invariant #1) The flag string is identical in the tenants entity, the tenants-admin section list, and the admin `config.php` constant; `/trace-flag` reports no orphan (backend/frontend gaps, if any, are documented as intentional).
- [ ] AC-18 (invariant #5) The flag is read only from the per-request tenant row; nothing caches it across requests or tenants.

## Per-repo plan

Build order: SAN-1748 -> SAN-1750 -> SAN-1749 and SAN-1751 -> SAN-1752. Each repo is versioned and deployed on its own; nothing assumes an atomic cross-repo change.

### tenants (SAN-1748 - owns the flag column)
- Add the nullable boolean column to `TenantUsersEntity` beside `ai_voice_agent_enabled` or the jury flags (`tenant-users.entity.ts:634-643`, `:2451-2463`), with a block comment explaining NULL = off and the FA-012 / SAN-1748 reference.
- No change to `global.service.ts` unless Open question 5 says the flag must appear in `verify_tenant` / `tenant-settings` (then all three lists, as for FA-011: select, verify mapping, tenant-settings fields).
- Existing-tenant handling per Open question 2 (not decided).
- `module.spec.md` for `modules/tenants` (flag list near :43 and :207, narrative near :291) updated.
- Verify: `npm run build`, `npm run lint`, `npm test` (jest, "no specs present yet" per repo CLAUDE.md). Because `synchronize: true` is on everywhere, confirm the column is nullable with no default before deploying.

### admin (SAN-1750 foundation, then SAN-1751 UI)
- **SAN-1750:** `config/config.php` constant (pattern `config.php:149-152`), and one fail-closed check in `includes/jury_nda_functions.php` (see Open question 4 for the delete-protection caveat before putting it inside `juryNdaSchemaReady()` at :81-100). Add a small helper (for example `juryNdaFlagEnabled()`) next to it with the `=== "1"` test, modelled on `limitJuryAccessEnabled()` (`jury_visibility_functions.php:25-29`).
- **SAN-1751:** with the foundation in place, hide and neutralise: the Round Settings card (`edit_program_round.php` template :460, module :2759), tracker and alerts (module :2801-2818), the three `edit_program_round.php` NDA handlers (:269, :311, :364), `jury_nda_tracker` and `jury_nda_preview` routes, the retention card and `save_jury_nda_retention` (`settings_management.php` module :243, template :179-182) and the retention route files, the "Can View Jury NDAs?" rows and their POST handling (`auth/admins.php` module :60-65, :111-116, :189-190, :883; template :517, :1196), and confirm the juror surfaces (`jury/nda.php`, `dashboard.php:212`, `round-applications.php:859-866`) all fall out through the probe. Handlers that do not call `juryNdaSchemaReady()` today (retention, permission, banner/My NDA helpers) need an explicit check.
- Verify: `php -l` on every edited file (the repo has no test suite or CI), a CLI harness for the new check, and the manual ON/OFF run in the Test plan. Automated test coverage will not be added.

### sanchiconnect-saas-tenants-admin (SAN-1749 - operator toggle)
- Add the field to a section in `modules/tenant_management/_switch_sections.php` (proposal: "Jury & Review", :62-67), which `create.php`, `edit.php` and `detail.php` all read (`edit.php:35-39`). Update the stale "223 / 222" counts in the file header (:12-14) and in `tenant_management/module.spec.md:89-95`.
- Confirm how the Create and Edit save paths write a nullable boolean (0/1 vs NULL) and that Clone Latest Tenant does not copy the flag to a new tenant unintentionally (Open question 2).
- Requires the tenants column to exist first (shared DB, `tenants-admin/CLAUDE.md` "Shared DB warning"): an `UPDATE` on an unknown column fails.
- Verify: `php -l` on edited files, and a manual Create / Edit / Detail run against a DB where the column exists. Automated test coverage will not be added.

### backend (SAN-1752 - decision, likely no code)
- Decide, and write down in `sc-saas-backend/src/modules/jury-nda/module.spec.md` (currently "no feature flag by design", :17) whether the two NDA email routes (`admin-actions.controller.ts:985`, :1012), the retry cron (`cron.service.ts:714-727`) and a `Feature` enum value need the flag. Considerations: the routes are reachable only with an admin path token and are called only from admin, so with the admin gate OFF nothing calls them [INFERRED from FA-010 spec, not re-verified]; the retry cron only acts on existing `jury_nda_acceptances` rows; backend reads flags once at bootstrap into `saasFeatures` (`sc-saas-backend/CLAUDE.md`, Tenancy), so a runtime toggle would need a backend restart to take effect; `FeatureGuard` does not deny on an undefined flag (`feature-guard.ts:18`).
- If the answer is "no code": document it, and add the `Feature` enum entry only if Open question 5 wants invariant-#1 parity (FA-011 precedent: `LIMIT_JURY_ACCESS_ENABLED` in the enum with no guard, `core/constants/enum.ts:1303`, `application-management/module.spec.md:79`).

## Contracts & invariants

- **Flags:** one new `tenant_users` boolean owned by tenants (name proposed `jury_nda_enabled`, NOT confirmed). Required consumers: tenants-admin (writes it), admin `config.php` (reads it). Optional/undecided: backend `Feature` enum, `verify_tenant` / `tenant-settings`, frontend `IFeatures` (not needed - no juror or business UI lives in the frontend, FA-010 "Key code finding"). `/trace-flag <name>` is a blocking gate before `in-review`.
- **API:** none added or changed. FA-010's two backend routes keep their current behaviour unless SAN-1752 decides otherwise. `/audit-contract` not required unless SAN-1752 adds code.
- **Events:** none.
- **Invariants at risk:** #1 flag names (a mismatched string between tenants entity, tenants-admin and admin `config.php` makes the feature silently off or unreachable; the admin side defaults to off so a mismatch fails safe but invisibly). #3 verification shape: only if Open question 5 adds the flag to `verify_tenant` / `tenant-settings`; additive. #5 tenant scoping: the flag is read per request from the tenant's own `tenant_users` row (`config.php:66-69`), never cached across tenants, never hardcoded. #2 API, #4 auth, #6 PowerPitch: untouched.
- **Shared-DB warning:** the new column is created by tenants (`synchronize: true`) and written by tenants-admin directly; deploy order below.

## Test plan

**Automated test coverage will not be added.** `sc-saas-admin` and `sanchiconnect-saas-tenants-admin` are PHP with no test suite and no CI, and the workspace "guardian" test-first skill does not exist (workspace CLAUDE.md, Standing process step 6). The substitute is stated plainly in each Linear issue and PR.
- tenants: `npm run build`, `npm run lint`, `npm test` (no specs exist). Manual: after deploy, confirm `tenant_users.<flag>` exists, is nullable, and existing rows are NULL.
- backend: only if code is added in SAN-1752: `npm run build`, `npm run lint`, `npm test`, and a spec for the changed route or cron. Otherwise nothing to run.
- frontend: not touched.
- admin: `php -l` on every edited file; a CLI harness for the flag check across the value matrix (undefined, NULL -> `?? "0"`, `"0"`, `"1"`, `""`) and for `juryNdaGateDecide()` with the flag off and on; **manual ON/OFF run** on a tenant that has an NDA round: OFF -> no card, no tracker, no retention card, no permission row, a Mandatory round opens for an unsigned juror with no pop-up, direct POSTs to the NDA handlers answer unavailable, and deleting a round or programme that has NDA rows is still refused (AC-15); ON -> every FA-010 behaviour unchanged (`modules/jury/nda-gate-repro-matrix.md`). Use a real jury-role session for the juror checks.
- tenants-admin: `php -l`; manual Create / Edit / Detail of a tenant with the toggle on and off, then confirm the tenant row and the admin behaviour change on the next admin request.
- cross-repo: `/trace-flag <name>`, `/check-isolation` (flag read per request), `/cross-repo-review` before `in-review`; staging smoke in the deploy order below.

## Rollout

1. **tenants first** (SAN-1748): deploy the column. NULL for every existing tenant = OFF. Nothing consumes it yet.
2. **admin second** (SAN-1750, then SAN-1751): until a tenant is switched on, NDA disappears for that tenant. **This is a behaviour change for every tenant that already uses NDA**, so existing users must be switched on in the same release window or before admin deploys (Open question 2). An admin build that reads a column that does not yet exist falls back to `?? "0"` = off (`config.php` pattern), which fails safe.
3. **tenants-admin** (SAN-1749): can ship after tenants; it is the way operators turn the flag on. Because it writes `tenant_users` directly, it must deploy after the column exists.
4. **backend last** (SAN-1752): decision only, likely no deploy.
5. Per-tenant enable is an operator action; there is no global default-on.

## Out of scope

- Any change to FA-010 behaviour when the flag is ON.
- Deleting or migrating existing NDA data (see Open question 3 for what happens on switch-off; this spec only decides how data is protected, not purging it).
- A per-round or per-programme switch (the per-round `nda_required` stays as is).
- Frontend (`sc-saas-frontend`) changes; 3rdparty-webservices; ai-startups-analyzer.
- Backfilling or seeding the flag by querying tenant databases from the tenants service (the tenants service does not read tenant DBs; see Open question 2).

## Amendment 2026-10-07 (Sandeep): column shape

The column is a NON-NULL boolean with `default: false` (shape of `limit_jury_access_enabled`, `tinyint(1)` 0/1 like the other switches in phpMyAdmin), not nullable. Existing tenants therefore read 0 = off. Admin still treats a missing key / NULL / anything but "1" as off (fail closed), so nothing else changes. Deploy note: the dev DB already holds the column as nullable with NULL values (it was created by `synchronize` from the first version), and MySQL refuses `NOT NULL` while NULL rows exist, so run `UPDATE tenant_users SET jury_nda_enabled = 0 WHERE jury_nda_enabled IS NULL;` BEFORE deploying this entity change.

## Open questions

**All eight items were confirmed by Sandeep on 2026-10-07 by approving each proposal as written (asked and answered: "Sab proposals approve"). Product-owner / legal items (Q3, Q6) carry Sandeep's sign-off as the gate holder; if the product owner or legal later disagrees, reopen them. No open question remains, so the spec is approvable.**

1. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] Final flag name.** Who answers: dev lead (naming) with product owner sign-off on the label. Approved decision (was the proposal): `jury_nda_enabled`, consistent with `*_enabled` flags (`ai_voice_agent_enabled`, `limit_jury_access_enabled`) and with FA-010:209. The name is the cross-repo contract and cannot be renamed later without dropping the live column (`synchronize: true`).
2. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] Default for EXISTING tenants.** Who answers: product owner (which tenants are paying for / using NDA) and dev lead (mechanism). Tenants already using NDA must be switched on before admin ships, or their Mandatory rounds lose the gate silently. The tenants service cannot see which tenants have `nda_required=1` rounds because each tenant has its own DB [INFERRED]. Approved decision (was the proposal): leave NULL (off) for everyone, and have an operator produce the list of tenants with `application_program_rounds.nda_required = 1` (a read-only query per tenant DB) and switch exactly those on through tenants-admin before the admin release. Also decide whether Clone Latest Tenant (tenants-admin) copies the flag to a new tenant.
3. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] What happens to existing NDA data and signed rounds when a tenant is switched OFF later.** Who answers: product owner and legal. Cases to settle: (a) rounds with `nda_required=1` and Mandatory: with the flag off, jurors are released and can score without an NDA; is that acceptable, or must switch-off be blocked while any Mandatory round is active? (b) jurors who already signed lose access to "My NDA" / signed copies, and admins lose the tracker and exports; is that acceptable given the FA-010 D-DPDP decision to retain signed NDAs for the retention period? (c) the user decision to hide the retention card when OFF means a Super Admin cannot reach the manual post-retention delete (FA-010 AC-26) after a switch-off. (d) when switched back on, are round settings and acceptances restored as they were? Approved decision (was the proposal): data is never deleted by the switch; delete protection stays on (AC-15); the flag is a visibility switch only; re-enabling restores everything. Reading of the either/or ending, to be confirmed at SAN-1751 review: the FIRST branch applies, i.e. the Super Admin retention card (expired-record deletion only) stays reachable with the flag off; this amends the earlier SAN-1751 wording that hid the retention card. Switch-off is not blocked.
4. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] Delete protection coupling.** Who answers: dev lead. `juryNdaHasData()` returns "no NDA data" whenever `juryNdaSchemaReady()` is false (`jury_nda_functions.php:811-813`). If the single flag check is placed inside `juryNdaSchemaReady()` as planned for SAN-1750, then with the flag OFF a programme or round holding signed NDAs can be deleted, which contradicts FA-010 AC-24 / BRL-10 and the retention decision. Approved decision (was the proposal): keep the flag inside `juryNdaSchemaReady()` for the UI/gate callers but make `juryNdaHasData()` (and `juryNdaProtectedTables()` / `juryNdaProtectedRoute()`, which already do not call the probe, :776-802) use a raw table-existence check with no flag.
5. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] Exposure beyond admin.** Who answers: dev lead. (a) Must the flag appear in `verify_tenant` / `tenant-settings` (`global.service.ts` three lists)? FA-011's flag is exposed, `ai_voice_agent_enabled` is not; admin does not need it because it reads `tenant_users` directly. (b) Does the backend need `Feature.<FLAG>` and a gate on the two NDA email routes and the retry cron (SAN-1752)? Note `FeatureGuard` passes on an undefined flag (`feature-guard.ts:18`), so NULL-off would need an explicit `=== true` check, and the backend only reloads flags at bootstrap. Approved decision (was the proposal): do not expose in `verify_tenant` / `tenant-settings`; add no backend gate; add the enum entry only for invariant-#1 parity if the dev lead wants it.
6. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] Developer-role bypass.** Who answers: product owner. FA-011 lets `is_dev` admins use Limit Access regardless of the flag, for testing and support (`jury_visibility_functions.php:19-23`). Should developer admins see the Jury NDA card with the flag off? Approved decision (was the proposal): no bypass, because "fully unavailable" was the stated behaviour and a half-visible NDA surface would be confusing.
7. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] tenants-admin placement and counts.** Who answers: dev lead. Which section holds the toggle (approved: "Jury & Review"), and whether to fix the stale "223 / 222" counts and add the also-missing `limit_jury_access_enabled` while editing `_switch_sections.php` (the latter stays OUT of FA-012 scope: only the Jury NDA flag is added; fixing the stale counts and adding `limit_jury_access_enabled` is not approved here). Also confirm how Edit writes a NULL nullable boolean (0 vs NULL), `edit.php:59` and the save path after line 97 were not read.
8. **[CONFIRMED - Sandeep, 2026-10-07; proposal approved as written] Admin NDA fields in the allotment email.** Who answers: dev lead. FA-010 planned optional `ndaRequirement` / `ndaNote` on `jury-startup-allotment-email` (backend DTO exists), but a grep of `sc-saas-admin` PHP finds no `ndaRequirement` / `ndaNote`, so it is unverified how admin builds the NDA sentence for the allotment email. "No NDA emails when OFF" cannot be confirmed until that path is read. Approved decision (was the proposal): SAN-1751 traces `sendAllotmentEmailToJury` and gates any NDA wording on the flag.

**Evidence not verified in this pass:** the Linear issue bodies and comments (not read; the main session handles Linear); the entry checks of `modules/developer/jury_nda_retention.php` and `jury_nda_retention_delete.php`; the guard around the second "Can View Jury NDAs?" select in `auth/admins.php` (template ~:1196); `tenant_management/edit.php` save path after line 97 and `create.php`; whether `modules/jury/nda-gate-repro-matrix.md` still matches the code.
