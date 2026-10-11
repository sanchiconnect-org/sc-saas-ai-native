---
id: SAN-984                     # Linear Project created (team: Sanchiconnect); anchored to its lowest-numbered
                                 # per-repo issue, SAN-984 (tenants). Full issue set: SAN-984 (tenants),
                                 # SAN-985 (backend), SAN-986 (frontend), SAN-987 (admin).
title: Startup District & Sub-District Selection
type: feature
status: approved
linear: https://linear.app/sanchiconnect/project/startup-district-and-sub-district-selection-fcb5320615d6
owner: nirmal.s@sanchiconnect.com
repos: [tenants, backend, frontend, admin]
contracts:
  api:
    - "GET api/v1/public/global/districts/:stateId (sc-saas-backend, NEW — mirrors /states/:countryId and /cities/:stateId exactly; feature-guarded)"
    - "GET api/v1/public/global/sub_districts/:districtId (sc-saas-backend, NEW — mirrors /cities/:stateId; feature-guarded)"
    - "PATCH api/v1/startups/startup-information (sc-saas-backend, EXTENDED — StartupInformationDto gains registeredDistrictId/registeredSubDistrictId, both @IsInt() @IsOptional(), same convention as registeredCityId)"
    - "GET api/v1/startups/startup-information (sc-saas-backend, EXTENDED — response now includes the new columns + their relations, e.g. registeredDistrictR/registeredSubDistrictR, matching the existing registeredCountryR/registeredStateR/registeredCityR shape)"
  flags:
    - "startup_district_subdistrict_enabled"
  events: []
tenant_scoped: true
depends_on: []
created: 2026-09-24
---

# Startup District & Sub-District Selection

## Problem

`sc-saas-frontend`'s Edit Startup/MSME "Basic Information" → "Headquartered in" section
(`startup-information.component.ts`, `/startups/edit/startup-information`) only collects
Country/State/City. Real India district/sub-district master data already exists
(`districts`/`sub_districts` tables, populated by `sc-saas-admin`'s Location Master Import,
SAN-314) but is currently consumed only internally by the Startup Recognition ID module
(SAN-253) via a **city-derived** lookup (`startups.registered_city_id` → `cities.district_id`/
`sub_district_id` → `districts`/`sub_districts.code`) — the startup itself never gets to state
its own District/Sub-District. This is imprecise (a city can map ambiguously, or not at all, to
a district/sub-district) and there is no way for a startup to correct it. This feature lets a
startup pick its own District/Sub-District directly in Edit Profile, flag-gated per tenant, and
makes that choice the preferred source for Startup Recognition ID generation
(`sc-saas-admin`/`sc-saas-backend`) and every other place a startup's district/sub-district is
read (`startup-detail.php`, the startups-list District filter, CSV export) — while never putting
an already-issued Recognition ID at risk.

## Resolved scope decisions (2026-09-24, confirmed with the user, not invented)

1. **Backfill/migration strategy — derive, don't leave empty.** Already-recognized startups'
   new `registeredDistrictId`/`registeredSubDistrictId` are backfilled via the **exact same**
   lookup path Recognition ID generation already uses today (`registered_city_id` →
   `cities.district_id`/`sub_district_id`). This guarantees the backfilled value matches what
   was already used to build the startup's live Recognition ID, so a future regenerate-all
   reproduces an identical code — zero risk of silently changing an already-issued ID.
2. **Recognition ID generation source — switch with fallback, not a hard cutover.**
   `StartupRecognitionIdGenerationService.resolveCityDistrictContext()` (backend) and
   `srIdResolveCityDistrictContext()` (admin) both switch to reading the startup's own
   `registeredDistrictId`/`registeredSubDistrictId` (`registered_district_id`/
   `registered_sub_district_id`) as the **preferred** source, falling back to today's
   city-derived lookup when a startup hasn't set them yet (flag-off tenant, or a startup that
   hasn't re-edited its profile since this shipped). Both hand-duplicated copies (no shared
   code between the two repos, confirmed via `startup_recognition_id_functions.php`'s own
   header comment) must change together or the two generation paths will silently diverge on
   which startups get old vs. new resolution behavior.
3. **Admin's other district/sub-district read paths — update, don't leave stale.**
   `sc-saas-admin/modules/startup-detail.php` (read-only display),
   `sc-saas-admin/modules/table.php` (startups-list "District" filter column), and
   `sc-saas-admin/modules/csv/export.php` (district/sub_district export columns) all prefer the
   startup's own new fields once set, for consistency with what the startup actually chose,
   instead of silently disagreeing with a stale city-derived value.

**Flag name:** `startup_district_subdistrict_enabled` — confirmed with the user, 2026-09-24.

**Backfill entry point (admin):** confirmed with the user, 2026-09-24 — a self-contained
one-off script re-implementing the city-derived lookup locally in this repo's own Medoo
connection (`modules/startup_recognition_management/backfill_district_subdistrict.php`,
mirroring `company_name_migration.php`), not a call into a new backend endpoint.

## Acceptance criteria

- [ ] A new `startup_district_subdistrict_enabled` flag exists on `TenantUsersEntity`
      (`sanchiconnect-saas-tenants`), defaulting `false`, following `hub_spoke_domain_enabled`'s
      exact column shape.
- [ ] The flag propagates end-to-end: cockpit column → backend `Feature` enum entry +
      `FeatureGuard` on the two new endpoints → frontend `IFeatures` → admin read via
      `$brandSettings['startup_district_subdistrict_enabled']` (no new `config.php` constant —
      mirrors `hubSpokeDomainEnabled()`'s pattern).
- [ ] With the flag off, the Edit Profile "Headquartered in" section is byte-identical to today
      (no District/Sub-District fields rendered); the two new backend endpoints 403/404 per
      `FeatureGuard`'s standard behavior.
- [ ] With the flag on, a startup can select District (scoped to their chosen State) and then
      Sub-District (scoped to their chosen District) in Edit Profile, following the exact same
      cascade UX as State→City today (clearing the child field and re-fetching on parent change).
- [ ] The existing `geographySynced` one-shot guard (SAN-730) also covers the new District/
      Sub-District fields — an autosave round-trip patching stale server data over a live user
      edit must not reintroduce that bug for the new fields either.
- [ ] Saving Edit Profile persists `registeredDistrictId`/`registeredSubDistrictId` on
      `StartupEntity` via the existing `PATCH startup-information` endpoint.
- [ ] `StartupRecognitionIdGenerationService.resolveCityDistrictContext()` (backend) and
      `srIdResolveCityDistrictContext()` (admin) both prefer the startup's own
      `registeredDistrictId`/`registeredSubDistrictId` when set, falling back to the existing
      city-derived lookup when not — and produce **identical** results to each other for the
      same startup (parity, not just each individually correct).
  - [ ] The existing "no district/sub-district mapping → omit segment, sub-district falls back
      to city code" behavior in `resolveSegmentValues()`/`srIdResolveSegmentValues()` is
      preserved as the final fallback tier under the new logic.
- [ ] A backfill migration/script sets `registeredDistrictId`/`registeredSubDistrictId` on every
      already-recognized startup (`recognized = true` or `recognitionId` not null) whose new
      columns are still null, via the same city-derived lookup — run once per tenant, idempotent
      (a second run is a no-op for already-backfilled rows).
  - [ ] Running `srIdRegenerateAll()`/the TS regenerate-all path for a backfilled tenant produces
        byte-identical Recognition IDs to what existed before this feature shipped (proves the
        backfill is safe).
- [ ] `startup-detail.php`'s read-only District/Sub-District display, `table.php`'s "District"
      filter column, and `csv/export.php`'s district/sub_district columns all prefer a startup's
      own `registered_district_id`/`registered_sub_district_id` once set, falling back to the
      existing city-derived resolution when not set.
- [ ] No existing flow (Country/State/City selection, Recognition ID generation/regeneration for
      a startup that hasn't set the new fields, admin's existing city-derived reads) is broken
      for any startup that never touches the new fields.

## Per-repo plan

### tenants

- Add `startup_district_subdistrict_enabled` boolean column to `TenantUsersEntity`
  (`sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-users.entity.ts`),
  `@Column({ type: 'boolean', name: 'startup_district_subdistrict_enabled', width: 1, default: false })`
  — exact shape of the most recently added flag, `hub_spoke_domain_enabled`. Cockpit-owned per
  invariant #1; no other tenants-side change needed (this flag flows through `verify_tenant`/
  `tenant-settings`'s existing generic passthrough the same way `hub_spoke_domain_enabled` does —
  confirm against the "explicit field-list edits" landmine noted for older flags before assuming
  passthrough is automatic here too).

### backend

- `StartupEntity` (`src/modules/startup/entities/startup.entity.ts`) — add
  `registeredDistrictId` (`registered_district_id`, int, nullable) and `registeredSubDistrictId`
  (`registered_sub_district_id`, int, nullable), immediately after the existing
  `registeredCityId`, plus relations to `DistrictsEntity`/`SubDistrictsEntity` mirroring the
  existing `registeredCountryR`/`registeredStateR`/`registeredCityR` relation pattern (verify the
  exact relation-property naming convention at startup.entity.ts:618-628 before naming the new
  ones — likely `registeredDistrictR`/`registeredSubDistrictR`).
- `StartupInformationDto` (`src/modules/startup/dto/startup-information.dto.ts`) — add
  `registeredDistrictId`/`registeredSubDistrictId`, `@IsInt() @IsOptional()`, same shape as
  `registeredCityId`.
- `GlobalController` (`src/modules/global/global.controller.ts`) — two new endpoints:
  `GET public/global/districts/:stateId` and `GET public/global/sub_districts/:districtId`,
  mirroring `getAllStatesOfCountry()`/`getAllCitiesOfState()`'s exact shape (cache-manager
  lookup, same response envelope `{message, data}`). Gate both with
  `@Features([Feature.STARTUP_DISTRICT_SUBDISTRICT_ENABLED])` (class already carries
  `@UseGuards(FeatureGuard)`).
- `DistrictsRepository`/`SubDistrictsRepository`
  (`src/modules/global/districts/districts.repository.ts`,
  `src/modules/global/sub_districts/sub-districts.repository.ts`) — add
  `getDistrictsByStateId(stateId)` / `getSubDistrictsByDistrictId(districtId)` list methods
  (today they only have single-row `getDistrictById`/`getSubDistrictById`, added for the
  recognition-id service's internal lookups).
- `Feature` enum (`src/core/constants/enum.ts`) — add
  `STARTUP_DISTRICT_SUBDISTRICT_ENABLED = 'startup_district_subdistrict_enabled'`.
- `StartupRecognitionIdGenerationService.resolveCityDistrictContext()`
  (`src/modules/startup-recognition-id/services/startup-recognition-id-generation.service.ts:154-224`)
  — extend its signature to also accept `registeredDistrictId`/`registeredSubDistrictId` (from
  the startup row, not just `registeredCityId`); when either is set, resolve `district`/
  `subDistrict` directly from `DistrictsRepository.getDistrictById()`/
  `SubDistrictsRepository.getSubDistrictById()` instead of going through `cities`; when unset,
  fall back to the existing city-derived path unchanged. `cityCode` (used by
  `resolveSegmentValues()`'s sub-district fallback tier) still always resolves from
  `registeredCityId` regardless of which path produced district/subDistrict, since it has no
  "own field" equivalent.
- **No backend-side backfill script** (decision #1, confirmed) — `startups` is a single shared
  table (this repo via TypeORM, `sc-saas-admin` via Medoo, same tenant DB); the admin-side
  one-off script (see admin's per-repo plan below) is the ONLY backfill run, and its writes are
  immediately visible to this repo's own reads/generation logic. Nothing to build here beyond
  the schema columns themselves.
- Jest tests: `resolveCityDistrictContext()` prefers the startup's own fields when set; falls
  back to city-derived when unset; produces identical output to the pre-change logic for a
  startup with no district/sub-district fields set at all; `FeatureGuard` refusal on both new
  endpoints when the flag is off; DTO validation for the two new optional int fields.

### frontend

- `core/domain/brand.model.ts` — add `startup_district_subdistrict_enabled: boolean;` to
  `IFeatures`, following `startup_founders_advisory`'s placement/shape.
- `core/service/api-endpoint.service.ts` — add `DISTRICT`/`SUB_DISTRICT` entries under
  `ApiEndpointService.ENDPOINT`, mirroring `STATES`/`CITY`'s exact shape
  (`${ApiEndpointService.GLOBAL}districts/`, `${ApiEndpointService.GLOBAL}sub_districts/`).
- `core/service/global.service.ts` — add `getDistricts(stateId)`/`getSubDistricts(districtId)`,
  mirroring `getStates()`/`getCities()` (same `of([])` short-circuit when the parent id is
  falsy, same `orderBy(..., 'name', 'asc')` for districts if that convention applies — confirm
  against `getStates()`'s exact behavior before copying).
- `startup-information.component.ts`
  (`src/app/modules/startups/pages/edit/startup-information/`):
  - New form controls `registeredDistrictId`/`registeredSubDistrictId` (both optional — no
    `Validators.required`, matching `registeredStateId`/`registeredCityId`'s current optionality
    rather than the required `registeredCountryId`).
  - Cascade wiring identical in shape to lines 261-268's existing pattern: `registeredStateId`
    valueChanges also nulls District+Sub-District and calls `getDistricts(stateId)`;
    `registeredDistrictId` valueChanges nulls Sub-District and calls
    `getSubDistricts(districtId)`.
  - The `geographySynced`-guarded patch block (lines 643-651) — add
    `registeredDistrictId: res.registeredDistrictR?.id || null` and the sub-district equivalent
    inside the SAME `if (!this.geographySynced)` block as Country/State/City, not a separate
    ungated patch, to avoid reintroducing SAN-730.
  - Gate the entire new District/Sub-District block behind
    `features.startup_district_subdistrict_enabled` (via the existing `brandDetails.features`
    subscription already used elsewhere on this component for GST/DPIIT/CIN and
    founders/advisory gating).
- `startup-information.component.html` — new District/Sub-District `<select>`s directly below
  the existing City dropdown, inside the "Headquartered in" section (heading at line 682),
  `*ngIf`-gated on the new flag.
- Karma tests for the new cascade (State clears District+Sub-District; District clears
  Sub-District) and for the `geographySynced` guard correctly covering the new fields; manual QA
  end-to-end (flag on/off, existing Country/State/City flow unaffected).

### admin

- `includes/startup_recognition_id_functions.php`:
  - `srIdResolveCityDistrictContext($database, $registeredCityId)` — extend to also accept
    `$registeredDistrictId`/`$registeredSubDistrictId` (from the startup row); when either is
    set, resolve `district`/`subDistrict` directly (`$database->get("districts", ...)` /
    `$database->get("sub_districts", ...)` by id) instead of going through `cities`; when unset,
    keep today's `registered_city_id` → `cities.district_id`/`sub_district_id` path unchanged.
    `cityCode` still always resolves from `registered_city_id` regardless.
  - Every call site (`srIdGenerateForStartup()` line 406, `srIdRegenerateAll()` line 529) updated
    to pass the startup's `registered_district_id`/`registered_sub_district_id` alongside
    `registered_city_id`.
  - Must produce **identical output** to the TypeScript twin for the same input — implement and
    review both changes together, not independently.
- `modules/startup-detail.php:1413-1425` — read-only district/sub-district display resolves from
  the startup's own `registered_district_id`/`registered_sub_district_id` first (direct
  `districts`/`sub_districts` lookup by id), falling back to today's city-derived resolution
  when unset. Same fallback applied in the rendering template
  (`themes/default/html/startup-detail/startup-detail.php:495-513`).
- `modules/table.php:1515-1836` — startups-list "District" filter column: resolving a selected
  district to matching startups now matches on `registered_district_id = :districtId` directly
  OR (`registered_district_id IS NULL` AND the existing city-derived `registered_city_id IN
  (...)` match) — a startup with its own field set is found by it even if its city's own
  district mapping happens to disagree.
- `modules/csv/export.php:95-282` — district/sub_district export columns: same
  own-field-first, city-derived-fallback resolution as `startup-detail.php`, keeping the
  existing per-request cache.
- `modules/startup_recognition_management/format_builder.php:61-62` — confirm no change needed
  (District/Sub-District here are Format Builder's abstract segment-type palette entries with
  demo/sample codes, not a live data source — sanity-check this remains true after the
  resolution-logic change, don't skip the check just because the task description assumes it).
- **Backfill trigger** (decision #1, confirmed) — a one-off admin-triggered entry point,
  `modules/startup_recognition_management/backfill_district_subdistrict.php`, mirroring
  `modules/application_management/company_name_migration.php`'s "hit the URL once, run inline,
  echo a confirmation, exit" pattern (`checkLoggedIn()` gate, no CLI needed). Re-implements the
  identical city-derived lookup directly against this repo's own Medoo connection (loops
  recognized startups, writes `registered_district_id`/`registered_sub_district_id` via the
  pre-decision-#2 city-derived helper) rather than calling into a new backend endpoint —
  avoids a new cross-repo call from admin into backend for a one-time operational task. `startups`
  is a single shared table (admin via Medoo, backend via TypeORM, same tenant DB) — one backfill
  run from either side writes the columns both repos subsequently read, so this script is the
  ONLY backfill needed; `sc-saas-backend` does not need its own separate backfill pass.
- No new `config/config.php` constant — read
  `$brandSettings['startup_district_subdistrict_enabled']` directly wherever admin needs to
  check the flag (e.g. deciding whether the migration entry point is meaningful for a tenant),
  following `hubSpokeDomainEnabled($brandSettings)`'s helper-function precedent in
  `includes/hub_spoke_functions.php` rather than adding a `define()`.
- `php -l` on every touched/new file.

## Contracts & invariants

- **Flags:** `startup_district_subdistrict_enabled` — new flag, `tenants`-owned, defaulting
  `false`, propagated per `hub_spoke_domain_enabled`'s pattern (cockpit → backend `Feature` enum
  → frontend `IFeatures` → admin read via `$brandSettings`, no new `config.php` constant).
- **API:** two new backend GET endpoints (districts/sub_districts, mirroring the existing
  countries/states/cities shape exactly) + an extension to the existing
  `PATCH/GET startup-information` DTO/response shape (two new optional int fields + their
  relations) — additive, no existing field renamed or removed.
- **Events:** none.
- **Invariants at risk:**
  - **Flag names (#1):** new flag; must propagate to all four layers (cockpit, backend enum,
    frontend `IFeatures`, admin) — `/trace-flag` before implementation.
  - **API contract (#2):** owned by `sc-saas-backend`; the two new endpoints and the DTO/response
    extension must be checked against frontend `core/service/global.service.ts` and any admin
    cURL caller (none expected — admin reads district/sub-district via its own Medoo connection,
    not this API) — `/audit-contract`.
  - **Tenant scoping (#5):** unaffected — every new query is scoped by the same per-request
    tenant DB connection (backend: bootstrap-loaded one-deployment-per-tenant; admin: per-tenant
    Medoo connection) already used for Country/State/City.
  - **The recognition-id-generation resolution logic itself is the highest-risk item in this
    spec**, even though it isn't one of the six named invariants verbatim: `sc-saas-backend`'s
    `resolveCityDistrictContext()` and `sc-saas-admin`'s `srIdResolveCityDistrictContext()` are
    hand-duplicated with zero shared code (confirmed in that PHP file's own header comment) and
    generate values baked into a startup's permanent, government-facing Recognition ID. Both
    must change in lockstep (decision #2) and the backfill (decision #1) must run and be
    verified safe **before** the resolution-logic switch is enabled for any tenant — see Rollout.
  - Auth (#4) and the tenant-verification contract (#3) are unaffected.

## Test plan

- tenants: manual verification the new column appears in `verify_tenant`/`tenant-settings`
  responses (check the field-list landmine noted in project memory — some flags need explicit
  field-list edits, not generic passthrough).
- backend: jest tests for `resolveCityDistrictContext()`'s own-field-preferred/city-derived-
  fallback behavior and parity with pre-change output when no new fields are set; `FeatureGuard`
  refusal on the two new endpoints when the flag is off; DTO validation for the two new fields.
  No backend-side backfill to test (decision #1 — the admin-side script is the only backfill;
  see admin's test plan below). `tsc --noEmit` clean.
- frontend: karma tests for the new cascade (State clears District+Sub-District; District clears
  Sub-District) and for `geographySynced` correctly covering the new fields; manual QA: flag off
  → section unchanged; flag on → full District/Sub-District selection + save + reload round-trip;
  confirm existing Country/State/City flow is unaffected either way. `ng build` clean.
- admin: `php -l` on all touched/new files. Manual QA: generate a Recognition ID for a startup
  with the new fields set (confirm it uses them) and one without (confirm city-derived fallback,
  byte-identical to pre-change behavior); confirm `srIdRegenerateAll()` reproduces identical
  codes for already-recognized startups post-backfill; confirm `startup-detail.php`/`table.php`
  filter/`csv/export.php` all prefer the startup's own fields once set and fall back correctly
  when not. No automated test framework in this repo (per `sc-saas-admin/CLAUDE.md`) — manual QA
  is the only verification available here.
- cross-repo: with the flag off on a control tenant, confirm zero visible change anywhere
  (Edit Profile section, Recognition ID generation, admin reads). With it on: a startup sets
  District/Sub-District in Edit Profile → saves → admin's startup-detail page shows the same
  values → admin generates/regenerates that startup's Recognition ID → confirm it resolves via
  the startup's own fields, not the city-derived path. Separately, for an ALREADY-recognized
  startup that has NOT touched the new fields: confirm the backfill has populated its new
  columns from the city-derived lookup, and confirm a regenerate-all produces the identical code
  it already had.

## Rollout

**Backfill decision revised 2026-09-24 (post-implementation, confirmed with the user):** the
backfill step below is now **optional, deferred, not run by default**. Reasoning: the fallback
logic in `resolveCityDistrictContext()`/`srIdResolveCityDistrictContext()` means an
already-recognized startup with null `registeredDistrictId`/`registeredSubDistrictId` resolves
identically to today (via the city mapping) — nothing is broken by skipping backfill. Its only
purpose was to hedge against one specific future scenario: a later Location Master Import
re-run *correcting* a city's `district_id`/`sub_district_id`, which would otherwise let a
subsequent regenerate-all silently produce a different code for an old startup. The user judged
that risk acceptable to leave unmitigated for now. The script
(`sc-saas-admin/modules/startup_recognition_management/backfill_district_subdistrict.php`) and
its Settings-page entry point remain in place, available to run manually later if desired —
nothing was removed, only the "run it as part of rollout" step below is no longer mandatory.

Sequenced specifically so a startup's Recognition ID is never at risk mid-rollout:

1. Add the flag column in `tenants` first (default `false` for every tenant).
2. Deploy `sc-saas-backend` with: the new `StartupEntity` columns + DTO fields, the two new
   feature-guarded endpoints, and the `Feature` enum entry — but with
   `resolveCityDistrictContext()` still on its OLD (city-derived-only) logic. Inert until the
   flag is set for a tenant, since the new columns start out null everywhere.
3. ~~Run the backfill migration/script~~ — **skipped by default** (see note above); the script
   remains available in admin if you later want to lock in a tenant's existing resolved values
   before enabling the flag there.
4. Deploy `sc-saas-admin`'s updated `srIdResolveCityDistrictContext()`/`srIdResolveSegmentValues()`
   (decision #2) and the read-path updates (`startup-detail.php`, `table.php`, `csv/export.php`)
   together with `sc-saas-backend`'s `resolveCityDistrictContext()` switch (decision #2) — these
   two MUST land together (or backend deployed first, since it's inert without the flag, then
   admin immediately after) since a mismatch between them means the two generation paths
   silently diverge on identical startups.
5. Deploy `sc-saas-frontend`'s flag-gated UI last.
6. Enable `startup_district_subdistrict_enabled` for one target tenant (the tenant that
   requested this — confirm which, since the requesting context implies a specific tenant, e.g.
   Tripura, following this workspace's recent single-tenant-first rollout pattern); verify
   end-to-end (including a live Recognition ID generation/regeneration) before enabling for any
   other tenant.
7. **Prerequisite check per tenant, not automatable:** an admin must have already run Location
   Master Import (SAN-314) for a tenant before this feature is useful there — the District/
   Sub-District dropdowns will be empty (or badly populated) otherwise. Confirm this has been
   run for the target tenant before step 6.

## Out of scope

- Any change to the Location Master Import feature itself (SAN-314) — this spec only consumes
  its already-populated `districts`/`sub_districts` tables.
- A bulk/CLI-driven backfill UI in `sc-saas-admin` beyond the single one-off migration entry
  point — no per-tenant dashboard or progress UI.
- Any change to `program-management`'s own use of `DistrictsRepository`/`SubDistrictsRepository`
  — sanity-checked as unaffected (no shared method signatures change), not modified.
- Any change to `format_builder.php`'s Format Builder segment-type palette itself (District/
  Sub-District remain selectable ID-format segment types; only what backs their *values* changes).
- Any change to the `district`/`City`/`Sub-Division` hierarchy retired in SAN-312/313 — unrelated
  to the SAN-314 hierarchy this spec extends; not revived.

## Open questions

None. Flag name and admin backfill mechanism both confirmed with the user, 2026-09-24 (see
"Resolved scope decisions" above). Assigned to Nirmal Singh on all four Linear issues
(SAN-984/985/986/987), 2026-09-24.

**Rollout note (non-blocking, operational, decide at flag-enable time, not implementation
time):** step 6 of Rollout enables the flag for one target tenant first — confirm which tenant
before flipping it in production (this feature's origin is Tripura Recognition ID work, so
that's the natural first candidate, but not yet explicitly confirmed).
