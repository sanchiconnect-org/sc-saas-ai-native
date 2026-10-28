---
id: SAN-1976
title: "Corporate save 500s with `WHERE id IN ( )` when the ecosystem sync maps an empty sectoralInterestIds (SC-SAAS-BACKEND-5V)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1976
sentry: [SC-SAAS-BACKEND-5V, SC-SAAS-FRONTEND-AW]
repos: [backend]
related: [SAN-1983]
commit: backend@ef3a3902 (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1976: empty `IN ( )` on industry_domains

## Investigation
* **Event:** 26 events on 2026-10-16 08:51–09:01 UTC, `environment: local`, server `468e2fa18dd4` (a developer's Docker backend behind `thub.sanchidev.in`). No production events.
  * `failed_table=industry_domains`.
  * `failedQuery`: `SELECT IndustryDomainsEntity.id, .name, .is_active FROM industry_domains IndustryDomainsEntity WHERE id IN ( )`.
* **The SQL shape pins the call site.** The `( )` with an inner space comes from the template `'id IN (:...ids )'` with an empty array. The `IndustryDomainsEntity` alias comes from `IndustryDomainsEntity.getRepository().createQueryBuilder()` with no alias. There are about 30 such sites. Every one is guarded with `.length > 0` except one: `mapElasticSearchCorporateInfo()` in `src/modules/corporate/repositories/corporate.repository.ts` (~1511). It used a plain truthiness check, and `[]` is truthy.
* **Matches SAN-1983 (SC-SAAS-FRONTEND-AW):** the frontend `loginFault( Internal Server Error )` events on `/corporates/edit/corporate-intro` fire at the same seconds: 08:51:34, 08:53:48, 08:56:10, 08:58:43 and 09:00:24. They come from the same Noida dev session.

## Root cause
1. `PATCH api/v1/corporates/corporate-information` runs `CorporateService.editCorporateInformation()`. It commits the update.
2. If `ECOSYSTEM_ENABLED`, the corporate is approved and `isSearchResults` is set, it then awaits `EcoSystemService.updateCorporate()`.
3. That calls `getCorporateByUUIDForEcosystem()`, then `mapElasticSearchCorporateInfo()`.
4. With `sectoralInterestIds = []` (a corporate with no sectoral interest selected), the query becomes `IN ( )`. MySQL raises a syntax error.
5. That throw sits outside `updateCorporate()`'s axios try/catch, so the request returns 500 *after* the save was already committed.
6. The corporate-intro 20 s auto-save repeated the request, which accounts for the event volume.

The same defect is on `origin/main` (line 1508).

## Fix
`src/modules/corporate/repositories/corporate.repository.ts`, `mapElasticSearchCorporateInfo()`: the lookup runs only when `Array.isArray(sectoralInterestIds) && sectoralInterestIds.length > 0`. Otherwise it returns `[]`, the existing fallback. This matches the guard already used by `mapIdsFields()` in the same file.

## Blast radius / existing-flow impact
* There are three callers: `getCorporateByUUIDForEcosystem`, `getEcosystemCorporateInformation` and the elastic-search list mapper.
* For a non-empty array: same query, same names. For `null`/`undefined`: `[]` as before. For `[]`: `[]` instead of a SQL error.
* No controller, DTO, route, flag, auth or tenancy change, so `/audit-contract` is not needed.

## Verification
* New cases in `src/modules/corporate/repositories/corporate.repository.spec.ts`:
  * `[]`, `null` and `undefined` skip the lookup and return `[]`;
  * `[3, 7]` still queries `'id IN (:...ids )'` and maps to names.
  * Result: 8/8 pass.
* `npm run gates` (run once for the whole slice):
```
gates summary (exit code, gate):
  0    lint
  0    test
  0    test-floors
  0    openapi-floors
  1    build
  0    unguarded-routes
```
  * `test`: 98 suites passed, 4 skipped.
  * The `build` failure is pre-existing and unrelated: `src/core/database/deploy-migrate.ts:139` `runMigrations({ fake: true })` TS2345. The local `node_modules` has typeorm 0.3.6, while `package-lock.json` pins 0.3.17. That file is untouched, and `tsc --noEmit` shows it as the only error.

## Ops follow-ups
* None for the data.
* Optional, not done: wrap the post-save `ecoSystemService.updateCorporate()` calls in `corporate.service.ts` (lines 202 and 277) in a try/catch, so a failed ecosystem sync can never 500 a save that already committed. `[DESIGN DECISION PENDING]` (dev lead): should an ecosystem sync failure surface to the user or only be logged?

## Related
SAN-1983 (frontend side of the same 500). The same `[]`-is-truthy guard already sits in `mapIdsFields()` in the same file.
