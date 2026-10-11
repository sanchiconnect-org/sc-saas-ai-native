# SAN-1001 — Startup public profile API: include District/Sub-District

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1001
- **Repo:** sc-saas-backend · **Type:** Improvement · **Priority:** Medium · **Assignee:** Mahima Sharma
- **Blocks:** SAN-1002 (frontend) · **Related spec:** SAN-984
- **Classification:** CODE_ERROR

## Problem
The startup public profile header shows only "State, Country". The public endpoint
`GET api/v1/startups/public/startup-information/:startupUUID` doesn't return the SAN-984
District/Sub-District relations, so the frontend can't show the full location.

## Root cause
`StartupRepository.getSatrtupInformationbyStartupUUID()` joins only Country, State and City. The
reduced (non-connected viewer) DTO in `StartupService.getStartupInformationPublicly()` also
includes only those three.

## Fix
- `src/modules/startup/repositories/startup.repository.ts`: joins `registeredDistrictR`/`registeredSubDistrictR` and selects `id`/`name` for each
- `src/modules/startup/startup.service.ts`: adds both fields to the reduced public DTO

The change only adds fields to the response (`id` + `name` only). Auth is unchanged
(RateLimiter + OptionalJwtAuthGuard).

## Verification
- `npx tsc --noEmit`: clean
- No automated regression test added yet

## Commit
sc-saas-backend@fb7f7dd4 (branch ai_native_setup_mahima)
