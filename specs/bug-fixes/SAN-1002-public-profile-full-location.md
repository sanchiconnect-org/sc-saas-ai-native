# SAN-1002 — Startup public profile header: show full location

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1002
- **Repo:** sc-saas-frontend · **Type:** Improvement · **Priority:** Medium · **Assignee:** Mahima Sharma
- **Blocked by:** SAN-1001 (backend) · **Related spec:** SAN-984
- **Classification:** CODE_ERROR

## Problem
The header on `startup-public-profile-v2` shows only "State, Country" (e.g. "Assam, India").
It should show every part of the location the startup has saved.

## Root cause
Both location `<li>` blocks in `startup-public-profile-v2.component.html` hardcode
`registeredStateR` + `registeredCountryR`.

## Fix
- `startup-public-profile-v2.component.ts`: new `fullLocation` getter that builds City, Sub-District, District, State, Country. It skips empty parts and repeated names (case-insensitive). District/Sub-District show only when `startup_district_subdistrict_enabled` is on.
- `startup-public-profile-v2.component.html`: both header spots render `{{ fullLocation }}`
- `core/domain/startup.model.ts`: optional `registeredDistrictR`/`registeredSubDistrictR` on `IStartupPublicProfileData`

## Verification
- `npx tsc --noEmit -p tsconfig.app.json`: clean
- Not yet checked in the browser; no automated regression test added yet

## Commit
sc-saas-frontend@7871102d (branch ai_native_setup_mahima)
