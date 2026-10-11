---
id: SAN-552
title: "FormsService.getCustomFormProfileData crashes on stale/mismatched profileUUID"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-552
sentry:
  - SC-SAAS-BACKEND-2E
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-552 — getCustomFormProfileData unguarded profile lookups

## Root cause

`form-management.service.ts`'s `getCustomFormProfileData()` switches on `profileType` and does, for
all 8 branches (startup/investor/corporate/mentor/serviceProvider/individual/partner/programOffice):
`const x = await repo.getXByUUID(profileUUID); profileId = x.id;` — none null-checked the lookup
before reading `.id`. Any stale, deleted, or mismatched `profileUUID` crashed the endpoint with an
unhandled 500 instead of a clean 404.

## Fix

Added a null-check + `NotFoundException` (using each entity's existing `ApiErrors.*_NOT_FOUND`
constant) before assigning `profileId`, for all 8 branches.

## Blast radius

None — only changes behavior for the previously-crashing null case.

## Verification

`tsc --noEmit` clean; existing suite `form-management.service.spec.ts` still passes.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
