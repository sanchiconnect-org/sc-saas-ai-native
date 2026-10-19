---
id: SAN-1923
title: "forms query hits \"Out of sort memory\" (SC-SAAS-BACKEND-5S) and forms-management/list/startup 504 (SC-SAAS-FRONTEND-2W)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1923
sentry: [SC-SAAS-BACKEND-5S, SC-SAAS-FRONTEND-2W]
repos: [backend]
related: [SAN-805, SAN-1760, SAN-1023]
commit: sc-saas-backend@688f5870 (branch ai_native_setup_vishali, pushed) — forms.repository.ts + new forms.repository.spec.ts
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1923: MySQL sort buffer overflow on the forms table

## Investigation
* **5S:** `QueryFailedError: Out of sort memory, consider increasing server sort buffer size`, 144 events, 2026-10-14 08:44–09:21 UTC, tag `failed_table: forms`. The failed query is a `FormsEntity` find that selects every column, including the `fields` JSON.
* **Only 3 `FormsEntity` queries have an ORDER BY.** All use `order: { position: 'ASC' }` in `src/modules/form-management/repositories/forms.repository.ts`:
  * `getAllForms`, behind `GET forms-management/list`;
  * `getFormsbyIds`, behind `GET forms-management/ids/:ids`;
  * `getFormsbyUUIds`, behind `GET forms-management/uuids/:uuids`.
* **Root cause:** MySQL 8 filesort copies every selected column into the sort buffer, JSON included, and `fields` holds the whole form definition. One large form bigger than `sort_buffer_size` fails the whole query.
* None of these queries has a LIMIT, so all rows are loaded anyway and sorting in Node costs nothing extra.
* **2W is a separate path.** `GET forms-management/list/startup` → `getAllFormsByUserType` has no ORDER BY, so it can't raise the sort error, and no code defect was found in it.
  * The 504s (513 events / 202 users all-time, still on prod release `218edca78`) are most likely the general DB/server degradation on 2026-10-14, the same window as 5S.
  * The response is heavy: every startup form with its full `fields` JSON.
  * Earlier tickets (SAN-805, SAN-1760, SAN-1023) only hardened the frontend handling.

## Fix
`forms.repository.ts`:
* Removed `order` from the 3 queries.
* Added an exported `sortFormsByPosition()`: sorts `position ASC`, then `id ASC`, on a copy. Used in all 3.
* Order is unchanged. Ties are now resolved by `id`, where MySQL's order was unspecified before.
* `where` filters unchanged; no schema change.

New `forms.repository.spec.ts`, 4 tests:
* sort order;
* input array not changed;
* each method keeps its filter;
* no method sends `order`.

## Blast radius
* Response shape is unchanged, including the `accountType` grouping in the service.
* No controller or DTO change, and `contracts/openapi.json` is unchanged, so frontend and admin consumers are unaffected.

## Verification
* `npx jest src/modules/form-management`: 2 suites, 12 tests pass.
* `npm run gates` (sc-saas-backend): exit 0.
  * lint, test, build: pass.
  * test-floors: 1329 passing, floor 1319.
  * openapi-floors: pass.

## Open
* Optional: raise MySQL `sort_buffer_size` (1–2 MB) as a safety net for other large-JSON sorts.
* The `list/startup` 504 needs RDS/APM metrics for 2026-10-14 to confirm. Consider slimming that response if it keeps happening.
