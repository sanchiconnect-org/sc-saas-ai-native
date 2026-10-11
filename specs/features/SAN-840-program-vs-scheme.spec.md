---
id: SAN-840                     # Linear Project created (team: Sanchiconnect); anchored to its lowest-numbered
                                 # per-repo issue, SAN-840 (backend). Full issue set: SAN-840 (backend),
                                 # SAN-841 (frontend), SAN-842 (admin).
title: Program vs Scheme classification
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/project/startup-programs-vs-schemes-dc2f991b0ca8
owner: nirmal.s@sanchiconnect.com
repos: [backend, frontend, admin]
                                 # No tenants-side change — this is a plain admin-editable column on
                                 # ApplicationProgramsEntity, not a cockpit-owned feature flag.
contracts:
  api:
    - "GET api/v1/application-programs-management (sc-saas-backend, EXTENDED — accepts an optional ?schemesOnly=true query param; default behavior unchanged, still excludes schemes)"
    - "GET api/v1/public/application-programs-management (sc-saas-backend, EXTENDED — same ?schemesOnly=true param on the public/unauthenticated variant)"
  flags: []
  events: []
tenant_scoped: true
depends_on: []
created: 2026-09-17
---

# Program vs Scheme classification

## Problem

`sc-saas-admin`'s Program Management edits every row of `application_programs` the same way, and `sc-saas-frontend`'s public "Programs" listing shows every active row indiscriminately. The product wants a way to mark a subset of programs as **Schemes** (e.g. Tri-Seed Fund, the same kind of program the Startup Grant Release Letter feature — SAN-786/787 — already generates letters for) so they can be listed separately from the general Programs catalogue, surfaced instead on the Operational Cost Reimbursement page's new **Schemes** tab.

## Resolved scope decisions

- **Classification only, no new workflow.** `is_scheme` is a plain boolean on `ApplicationProgramsEntity` — a Scheme is still a full `application_programs` row (same apply flow, same round/form machinery), just excluded from the default Programs listing.
- **No new API endpoint for writing it.** `sc-saas-admin` writes `is_scheme` directly via Medoo in the same POST handler that already writes every other admin-only toggle on this entity (e.g. `restrictToRecognitionIdHolders`) — consistent with this entity's established pattern.
- **Gated on `operational_cost_reimbursement_enabled`, not a new flag.** The admin toggle is only meaningful for a tenant that has OCR/Schemes enabled at all; reusing that existing flag avoids introducing a second, overlapping one.
- **Existing general listing methods extended, not duplicated.** `getAllPrograms()`/`getAllPublicPrograms()` already had a hardcoded `isScheme=false` filter (added defensively when the column was introduced, so schemes never leaked into the general listing by default); this spec just parameterizes that filter (`schemesOnly`, default `false`) so the same query logic serves the new Schemes tab too.
  **Superseded 2026-09-22 (SAN-907):** the general listing's exclusion of Schemes was explicitly reversed — a
  Scheme is still a full program and now shows on BOTH the general Programs listing and its own Schemes tab.
  Only the dedicated `schemesOnly=true` call (Schemes tab) still filters to schemes-only; the default call now
  applies no `isScheme` constraint at all. See `specs/bug-fixes/SAN-907-programs-listing-includes-schemes.md`.

## Acceptance criteria

- [x] `is_scheme` boolean column exists on `ApplicationProgramsEntity`, default `false`.
- [x] `GET application-programs-management` and its public variant default to excluding schemes (`isScheme=false`), unchanged from prior behavior; passing `?schemesOnly=true` returns only schemes.
- [x] `sc-saas-admin`'s Program edit page shows an "Is this a Scheme?" toggle, disabled (with a tooltip) when `operational_cost_reimbursement_enabled` is off for the tenant.
- [x] A direct POST with `is_scheme=1` while the flag is off is still coerced to `0` server-side (belt-and-suspenders, same pattern as `restrictToRecognitionIdHolders`'s `startup_recognition_enabled` gate).
- [x] `sc-saas-frontend`'s Operational Cost Reimbursement page has a Schemes/Operational Cost Reimbursement tab bar, **Schemes selected by default**, rendering schemes as a lightweight card grid (logo/initial, title, description, "View Details").
- [x] "View Details" on a scheme card navigates to the same `/programs/apply/:code/:slug` route the main Programs page's own card component uses — no new/duplicated apply-flow code.

## Per-repo plan

### backend

- `ApplicationProgramsEntity` — add `is_scheme: boolean` (`@Column({ type: 'boolean', name: 'is_scheme', width: 1, default: false })`).
- `ApplicationProgramsRepository.getAllPrograms()` / `getAllPublicPrograms()` — replace the hardcoded `.andWhere('programs.isScheme = false')` with `.andWhere('programs.isScheme = :isScheme', { isScheme: schemesOnly })`, `schemesOnly` a new optional param (default `false`).
- `ApplicationProgramService.getAllPrograms()` / `getAllPublicPrograms()` and both controllers (`application-program.controller.ts`, `public-application-program-management.controller.ts`) — thread a new `?schemesOnly=` query param through to the repository call.

### admin

- `themes/default/html/application_management/program.php` — new "Is this a Scheme?" toggle in the Program edit form, alongside the existing "Restrict to Startup Recognition ID Holders Only" toggle; same disabled+tooltip gating pattern, keyed on `operational_cost_reimbursement_enabled` instead of `startup_recognition_enabled`.
- `modules/application_management/program.php`'s `editProgram` POST handler — persist `is_scheme`, coerced to `0` server-side when the flag is off regardless of what was posted.

### frontend

- `operational-cost-reimbursement.component.ts`/`.html` — new `activeTab: 'schemes' | 'ocr'` state (default `'schemes'`), a `schemes: IProgram[]` array fetched via `PublicApiService.fetchApplicationProgramManagement('true', false, undefined, 'true')` on init, and a `viewSchemeDetails(scheme)` method navigating to `/programs/apply/:code/:slug?autoStatusCheck=true`.
- `PublicApiService.fetchApplicationProgramManagement()` — new optional `schemesOnly` param (default `'false'`), appended as an HTTP query param.
- Lightweight card markup + `.ocr-scheme-card`/`.ocr-scheme-logo(-placeholder)` styles added to the component's own SCSS — deliberately NOT a reuse of `app-call-for-applications-card` (declared, not exported, by `CallForApplicationsModule`, and carries a large amount of applied/reapply/expired state this simpler "browse and view" tab doesn't need).

## Contracts & invariants

- **API (#2):** `application-programs-management` and its public variant gain one new optional query param each; existing callers that don't pass it see byte-identical behavior (schemes still excluded by default). No DTO/response-shape change.
- **Flags (#1):** no new flag — reuses `operational_cost_reimbursement_enabled`, which already exists and is fully propagated (tenants → backend `Feature` enum is NOT applicable here since this flag was already established as admin/frontend-consumed only for OCR; see SAN-756's own Contracts section).
- **Tenant scoping (#5):** unaffected — the repository methods already scope by the request's own tenant DB connection/JWT; `schemesOnly` is just an additional WHERE clause on the same already-scoped query.

## Test plan

- backend: manual verification that `GET .../application-programs-management` (both variants) excludes a scheme-marked program by default, and returns ONLY scheme-marked programs with `?schemesOnly=true`. Type-check (`tsc --noEmit`) clean.
- admin: `php -l` on both edited files. Manual QA: with `operational_cost_reimbursement_enabled` off, confirm the toggle is disabled with a tooltip and a direct POST with `is_scheme=1` still persists `0`; with the flag on, confirm the toggle works and persists.
- frontend: full `ng build` clean. Manual QA: Schemes tab is selected by default, scheme cards render with logo/placeholder + title + description, "View Details" navigates correctly, switching to the Operational Cost Reimbursement tab shows the unchanged eligibility/claims content.

## Rollout

1. Deploy backend with the new column + `schemesOnly` param (inert — no tenant has any program marked as a scheme yet, so behavior is unchanged until an admin uses the new toggle).
2. Deploy admin's Program-edit toggle.
3. Deploy frontend's Schemes tab.
4. An admin marks the relevant program(s) (e.g. Tri-Seed Fund) as a Scheme via the new toggle; verify it disappears from the general Programs listing and appears on the Schemes tab.

## Out of scope

- Any change to the actual apply/round/form flow for a scheme — it's the exact same `application_programs` machinery as a program.
- A dedicated "Scheme Management" admin section — schemes are still managed from the existing Program Management pages.
- Bulk/list-level "mark as scheme" action — one program at a time, from its own edit page.

## Open questions

None blocking — already resolved via direct user instruction during implementation (this spec was authored retroactively after the work shipped, documenting the design as-built).
