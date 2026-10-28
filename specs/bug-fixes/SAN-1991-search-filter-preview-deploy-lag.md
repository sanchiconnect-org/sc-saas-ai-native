---
id: SAN-1991
title: "Search filter preview \"d.find(...) is undefined\" on Firefox — already fixed by SAN-1933, deploy lag (SC-SAAS-FRONTEND-HQ)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1991
sentry: [SC-SAAS-FRONTEND-HQ]
repos: [frontend]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1991: Firefox duplicate of SAN-1933, deploy lag

## Investigation
* **Sentry:** `Uncaught (in promise): TypeError: can't access property "name", d.find(...) is undefined`.
  * 1 event, 1 user, 2026-10-21 06:49 UTC, ecosystem.firstwingsconnect.com `/search/startups`, Firefox 158 on Windows, production.
  * Release `218edca78`. The frame is in `src_app_modules_search_search_module_ts.*.js`, i.e. the search module chunk.
* This is Firefox's wording of the Chrome message in SAN-1933 (SC-SAAS-FRONTEND-HH, "Cannot read properties of undefined (reading 'name')").
* **Same call site:** `git show 218edca78:src/app/shared/utils/filters.helper.ts` line 112 still has `detailsArr.find((b) => b.id == e).name`. `filters.helper.ts` is imported only by search-module components (`advanced-filter-wrapper`, `saved-filters-view`) and `filters.model.ts`, so it is bundled into the search chunk the frame points at.
* **Fix status:** `git merge-base --is-ancestor d7d588876 218edca78` → not an ancestor. `git branch -a --contains d7d588876` lists only the `ai_native_setup*` branches, so the SAN-1933 fix has not been promoted to `main`/prod yet.
* **Current code:** `filters.helper.ts:114` is `detailsArr.find((b) => b.id == e)?.name ?? e`. A grep for `find(...).name` across `src/app/modules/search` and `src/app/shared/utils` finds no other unguarded site.

## Fix
None. Current source already guards it (SAN-1933, `d7d588876`, with `filters.helper.spec.ts`). The event will stop once that commit reaches production.

## Blast radius / existing-flow impact
None, since nothing was changed.

## Verification
* `git merge-base --is-ancestor d7d588876 218edca78 && echo "fix IN release" || echo "fix NOT in release"` → `fix NOT in release`.
* `git show 218edca78:src/app/shared/utils/filters.helper.ts` line 112 → `valueMapped = ids.map((e) => { return detailsArr.find((b) => b.id == e).name })`.
* Current `filters.helper.ts:114` → `valueMapped = ids.map((e) => { return detailsArr.find((b) => b.id == e)?.name ?? e })`.

## Recommendation
Close as a duplicate of SAN-1933 once `d7d588876` is deployed to prod. If HQ recurs on a release that contains `d7d588876`, reopen it.

## Related
SAN-1933 (fix). Same sweep: SAN-1986, SAN-1993, SAN-1994, SAN-1982.
