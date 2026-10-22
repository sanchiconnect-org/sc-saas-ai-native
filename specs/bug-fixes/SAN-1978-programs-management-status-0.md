---
id: SAN-1978
title: "programs-management 0 Unknown Error still reported (SC-SAAS-FRONTEND-1); program-code-details had no error callback"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1978
sentry: [SC-SAAS-FRONTEND-1]
repos: [frontend]
related: [SAN-1930, SAN-805, SAN-804, SAN-509, SAN-375, SAN-1971]
commit: frontend@efdc62166 (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1978: programs-management status 0

## Investigation
* **The event itself is deploy lag.**
  * Event: `GET programs-management/: 0 Unknown Error`, release `bcf88383d` (2026-10-02), firstwings, Safari, 2026-10-19 08:40:41.
  * The same trace (`f0750bae…`) also failed `community-wall/posts/me/stats` and `startups/startup-information` in the same second. That points to a network drop, not one bad endpoint.
  * The list caller fix SAN-805 (`8a79d0248`, 2026-10-05) is not in `bcf88383d` (`git merge-base --is-ancestor 8a79d0248 bcf88383d` → no). It is on `origin/main`.
  * SAN-1930's `0a09edb32` is not on `origin/main` at all (only on `ai_native_setup_vishali`).
* **Current code, list callers:** all five `fetchProgramManagement()` subscribers have an error callback: `tracker`, `account-type`, `programs`, `call-for-applications`, `active-programs`.
* **Current code, the caller SAN-1930 did not cover:**
  * `ProgramCodeDetailsComponent.fetchWebinars()` (`modules/programs/program-code-details/program-code-details.component.ts:127`) subscribes to `fetchProgramManagementByCode()` with no error callback.
  * That service method only re-throws, with no toast.
  * Live evidence on the current main release: 2J has `GET programs-management/code/tri1264: 404` on `218edca78` (trise, `/programs/details/tri1264/tri-seed-fund`).
  * When this happens the page stays blank and the error is reported as unhandled.
* The 14-day FRONTEND-1 group is a catch-all for status-0 failures on many endpoints and tenants (news, forms list, dashboards, connections, public events). All of them are on releases older than the matching fixes.

## Fix
`program-code-details.component.ts`, error callback on `fetchProgramManagementByCode()`:
* 404 → `router.navigate(['/programs'])`. This is the same thing the existing `if (!this.selectedProgram)` branch does for an empty response.
* Any other status: no-op. The page stays as it was, but the error is no longer thrown as unhandled.

## Blast radius / existing-flow impact
* The success path is unchanged.
* The only behaviour change: an unknown or deleted program code now goes back to `/programs` instead of a blank page. That matches what the component already did when the API returned no program.
* No API, flag, tenancy or auth change.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → exit 0. `npx tsc -p tsconfig.spec.json --noEmit` → exit 0.
* Karma, both changed specs → `TOTAL: 15 SUCCESS`. 2 new tests here: a 404 navigates to `/programs` and does not throw; status 0 does not throw and does not navigate.
* ESLint: no config in the repo, not run.
* Not tested in a browser.

## Recommended close
* Code fix in review.
* Remaining status-0 events need a deploy (prod tenants run `bcf88383d`, `9dde12280`, `dab63831` …, all older than SAN-805/SAN-1930).
* Also the SAN-1930 status-0 `beforeSend` filter decision, still open.
