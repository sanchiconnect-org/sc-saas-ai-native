---
id: SAN-1933
title: "Search filter preview crashes reading 'name' when an applied filter id isn't in the dropdown options (SC-SAAS-FRONTEND-HH)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1933
sentry: [SC-SAAS-FRONTEND-HH]
repos: [frontend]
commit: sc-saas-frontend@d7d588876 (branch ai_native_setup_vishali, pushed) — shared/utils/filters.helper.ts + new filters.helper.spec.ts
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1933: filter preview crashes on an unmatched filter id

## Root cause
* **Sentry:** `Uncaught (in promise): TypeError: Cannot read properties of undefined (reading 'name')`.
  * 1 event, 2026-10-15 09:05 UTC, ecosystem.firstwingsconnect.com `/search/investors`.
  * Release `218edca78`, which is current prod, so this is not deploy lag.
* **Where:** `src/app/shared/utils/filters.helper.ts:112` (`createFiltersPreviewObject`) did `ids.map(e => detailsArr.find(b => b.id == e).name)`.
* **How it fails:** an applied id with no matching option makes `find()` return undefined, and `.name` throws. Causes include a removed option, a per-parent state/city list, or a stale URL or saved filter.
* **Effect:** the exception aborts the whole preview build.
* **Callers:**
  * `advanced-filter-wrapper.component.ts:388` (applied-filter chips);
  * `saved-filters-view.component.ts:139` (saved-filter previews).
* The git log of `filters.helper.ts` shows no earlier fix.

## Fix
`ids.map(e => detailsArr.find(b => b.id == e)?.name ?? e)`.
* Matched ids map to names exactly as before.
* An unmatched id falls back to the raw id, so its chip still renders and can be removed.

## Blast radius
* The output shape is unchanged (array of names/strings).
* The behaviour only differs where it used to throw.
* There is no backend or contract impact.

## Verification
* New `src/app/shared/utils/filters.helper.spec.ts`, 4 specs:
  * ids map to names;
  * a single numeric id works;
  * an unmatched id doesn't throw and falls back to the raw id;
  * the value is left untouched when the options aren't loaded.
* `npx tsc --noEmit -p tsconfig.app.json` and `-p tsconfig.spec.json`: exit 0.
* `npm run gates`: passed.
  * openapi-types, loader-floor, build, test-floors: pass.
  * unit-tests: 1107/1107 pass (floor 1098).
