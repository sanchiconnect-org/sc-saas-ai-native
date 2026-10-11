---
id: SAN-845
title: "Add tenant-level switch to enable Tripura certificate theme"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-845
repos: [tenants]
commit: sanchiconnect-saas-tenants@4b9b9a2
created: 2026-09-18
updated: 2026-09-18
---

# SAN-845 — tenant-level switch for the Tripura certificate theme

## Request

The Tripura certificate theme itself (SAN-747/748/749, under the "New Certificates Theme for Tripura" milestone) is
already built and selectable from every tenant's own Certificate Builder theme dropdown in `sc-saas-admin`. This
request adds a tenant-level flag in the cockpit (`sanchiconnect-saas-tenants`) to control that at the tenant level,
rather than it being open to every tenant by default.

## Design decisions (resolved with the user before implementation, not invented)

- **Gates visibility only, does not force-select.** When on, "Tripura" is eligible to appear as a theme option in that
  tenant's Certificate Builder dropdown; the admin still picks it manually. When off, the option should not be
  offered at all (wiring that gate into `sc-saas-admin` is an explicit follow-up, not built here — see Scope below).
- **Flag name:** `tripura_certificate_theme_enabled`.

## Scope (single-repo, per this issue's own labeling)

Only `sanchiconnect-saas-tenants`. Whether/how `sc-saas-admin`'s Certificate Builder actually reads this flag to
filter its theme dropdown is a separate follow-up issue — not in scope here, per the bug-fix skill's single-repo
enforcement (this issue is labeled `Repo: Tenants` only).

## Fix

- `TenantUsersEntity` (`src/modules/tenants/entities/tenant-users.entity.ts`) — new column, exact same shape as the
  most recent precedent flag (`startup_grant_release_format_download_enable`):
  ```ts
  @Column({
    type: 'boolean',
    name: 'tripura_certificate_theme_enabled',
    width: 1,
    default: false,
  })
  tripura_certificate_theme_enabled: boolean;
  ```
- `global.service.ts` — added to all three hand-maintained field lists this repo requires for a flag to actually
  reach `verify_tenant`/tenant-settings output (this repo propagates flags via explicit field lists, not generic
  passthrough — a documented, recurring gotcha every prior flag in this file hit too): the query-builder select list
  (~line 337), the manual `features` object (~line 684), and the generic tenant-settings select array (~line 926).

## Blast radius

New column, default `false` for every existing tenant — inert until explicitly enabled. `TypeORM synchronize: true`
is on in all envs for this repo, so the column is created automatically on next boot; no manual migration needed, no
existing behavior changes until an operator sets it.

## Verification

`npx tsc --noEmit` clean. `npx eslint` on both touched files: only two pre-existing prettier errors in
`global.service.ts` (confirmed pre-existing by stashing this change and re-running eslint against unmodified
`ai_native_setup` — same two errors, just at line numbers shifted by this diff) and one pre-existing unused-import
warning in `tenant-users.entity.ts`; nothing introduced by this change. No regression test proposed — this is a
plain data-plumbing addition (column + field-list wiring), not new logic, matching how every prior flag of this
identical shape (e.g. SAN-786's `startup_grant_release_format_download_enable`) was handled.

## Rollout

Committed and pushed to `ai_native_setup`: `4b9b9a2`.

## Open questions

None blocking for this issue's scope. The `sc-saas-admin` half (actually gating the Certificate Builder dropdown on
this flag) needs its own follow-up issue before the flag has any visible effect.
