# SAN-1919 — Typed response for GET /api/v1/users/profile in the OpenAPI contract (follow-up of SAN-1624)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1919 · **Parent finding:** SAN-1624 (dashboard-v2 undefined cluster)
- **Repos:** sc-saas-backend (contract), sc-saas-frontend (regenerated types only)

## Why
SAN-1624 asked for the response the dashboard relies on to be in the API contract test. `GET /api/v1/users/profile`
(the PWA's `IProfileDetails`: `accountType`, `profileUUID`, `connectionMatrix`, …) had no response schema in
`contracts/openapi.json`, only `200: { description }`, so a renamed or removed field was invisible to the
API-contract check (SAN-1593) and to the frontend's generated types (SAN-1911).

SAN-1624's own crashes were not caused by this (they were render-before-load races, fixed in August, still
reported only by stale cached builds). This closes the gap so a future backend change to the profile shape fails CI.

## Change
**sc-saas-backend**
- `src/modules/user/dto/user-profile-response.dto.ts` (new): `UserProfileResponseDto` + `ProfileConnectionMatrixDto`,
  documentation-only classes describing what `UserService.getUserProfile()` returns (44 fields, 21 required: the
  columns that are never null plus `connectionMatrix`). Connection-matrix rows document both shapes (per-user rows have
  `otherProfileType`, global rows `profileType2`).
- `user.controller.ts`: `@ApiOkResponse({ description })` → `@ApiEnvelopeResponse(UserProfileResponseDto, { description })`.
  No runtime change; nothing validates or serialises with the class.
- `contracts/openapi.json`: refreshed (additive only); `contracts/openapi-floors.json`: typed responses 3 → 4.
- `src/modules/user/module.spec.md`: note under Public surface.

**sc-saas-frontend**
- `src/app/core/contracts/api.generated.ts`: regenerated with `node scripts/sync-openapi.js`. Adds the two schemas and
  types the profile response; it also picks up the three auth responses typed by SAN-1915, whose regeneration had
  not been committed. No code uses the new types yet.

## Verification
- Backend: `tsc --noEmit` clean; eslint on the changed files 0 errors (as CI sees them, LF; the Windows working copy
  is CRLF through `core.autocrlf`, the index is LF); `jest src/modules/user` 14/14; `npm run build` OK;
  `openapi-floors` gate passes at 4.
- OpenAPI generated locally (XAMPP MariaDB, throwaway database and user, started with
  `--explicit-defaults-for-timestamp`, all removed afterwards): 780 paths, 839 operations;
  `check-openapi.js --snapshot` → **0 breaking, 2 additive** (the two new schemas).
- Frontend: `sync-openapi.js --check` matches; `tsc -p tsconfig.app.json --noEmit` clean.
- No automated test added (none exists for documentation-only DTOs); the contract check itself is the guard.
