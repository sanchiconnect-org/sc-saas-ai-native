---
id: SAN-907
title: "Programs listing no longer excludes Schemes"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-907
repos: [backend]
commit: sc-saas-backend@ddcab119
created: 2026-09-22
updated: 2026-09-22
---

# SAN-907 — Programs listing includes Schemes again

## Request

The general "application programs" API (backing `sc-saas-frontend`'s Programs page, `/call-for-applications`)
should stop excluding Schemes — a Scheme should show up on BOTH the general Programs listing and its own
dedicated Schemes tab, not just the latter.

## Context

[[SAN-840]] introduced `is_scheme` and had `getAllPrograms()`/`getAllPublicPrograms()` filter `isScheme = false`
by default, specifically to keep Schemes off the general listing. Confirmed via screenshots that this was
working exactly as originally designed (a program marked as a Scheme correctly did not appear on the Programs
page) before this change — this is a deliberate reversal of that specific design decision, not a bug fix of
broken behavior.

## Fix

`ApplicationProgramsRepository.getAllPrograms()` / `getAllPublicPrograms()` — removed the unconditional
`andWhere('programs.isScheme = :isScheme', { isScheme: schemesOnly })`. Now:
- `schemesOnly = false` (default, general Programs listing): no `isScheme` constraint at all — returns both
  schemes and non-scheme programs together.
- `schemesOnly = true` (Schemes tab): still applies `isScheme = true`, unchanged.

## Verification

`npx tsc --noEmit -p tsconfig.json` clean. `npx eslint` on the touched file: 0 errors, only pre-existing
unused-import warnings. No regression test proposed — a one-condition query change, not new logic.

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-backend@ddcab119`.

## Open questions

None blocking.
