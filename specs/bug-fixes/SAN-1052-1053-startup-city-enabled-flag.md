# SAN-1052 / SAN-1053 — `startup_city_enabled` flag gates the City field in startup Edit Profile

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1052 (tenants) · https://linear.app/sanchiconnect/issue/SAN-1053 (frontend)
- **Repos:** sanchiconnect-saas-tenants, sc-saas-frontend · **Assignee:** Nirmal Singh · **Related:** SAN-984 (District/Sub-District flag)
- **Classification:** FEATURE (flag)

## Change
- **tenants** (`59f537e`): new `TenantUsersEntity.startup_city_enabled` boolean, **default true** (opt-out). City has always
  been shown, so every existing tenant's form is unchanged until an operator turns it off. The flag is added to both
  hand-maintained lists in `global.service.ts`: the `verify_tenant()` features object and the `getTenantSettings()`
  SELECT. That pass also fixed a pre-existing gap: `startup_district_subdistrict_enabled` (SAN-984) had never been in the
  `getTenantSettings()` list.
- **frontend** (`0a9908f3`): `IFeatures.startup_city_enabled`.
  - Edit Profile: the state→city fetch and the City `<select>` are gated behind the flag (`*ngIf`), mirroring the
    District pattern. Saved `registeredCityId` values are never cleared.
  - Public profile v2: `fullLocation` hides City when the flag is off.

## Known gaps (found 2026-10-01, see Linear)
- **sanchiconnect-saas-tenants-admin switch list** (`modules/tenant_management/_switch_sections.php`) lists neither
  `startup_city_enabled` nor `startup_district_subdistrict_enabled`, so operators can't toggle either flag from
  Create/Edit Tenant.
- **sc-saas-backend `Feature` enum** has `STARTUP_DISTRICT_SUBDISTRICT_ENABLED` but no `STARTUP_CITY_ENABLED`
  (invariant #1: naming consistency). Nothing in the backend gates on it today.

## Verification
- Tenants build clean. Frontend type-check per commit. No automated tests were added (guardian skill missing).

## Commits
sanchiconnect-saas-tenants `59f537e` · sc-saas-frontend `0a9908f3` (on `ai_native_setup`)
