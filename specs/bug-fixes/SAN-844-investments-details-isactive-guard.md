---
id: SAN-844
title: "investments-details crashes setting 'isActive' on unmatched investment-type id (findIndex -1)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-844
sentry:
  - SC-SAAS-FRONTEND-EY
repos: [frontend]
commit: sc-saas-frontend@59b2d4aa (branch ai_native_setup_vishali, pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-844 — investments-details isActive index guard

## Root cause
`TypeError: Cannot set properties of undefined (setting 'isActive')` — production, url `/investors/edit/investments-details`, release `sc-saas-frontend@d16ce597b`.

`investments-details.component.ts:230-265` had six near-identical blocks:
```ts
this.investmentInfo.investmentMechanismIds.forEach((item) => {
  if (item.id) {
    const index = this.investment_mechanisms.findIndex(mh => mh.id === item.id);
    this.investment_mechanisms[index].isActive = true;
  }
});
```
at lines 233 (`investment_mechanisms`), 239 (`investment_preferences`), 245 (`industries`), 251 (`investment_stages`), 257 (`investability_metrics`), 263 (`business_models`). If a saved `investmentInfo` id doesn't exist in the freshly-loaded master list (e.g. the backend returns an id for a type since renamed/deleted from master data), `findIndex` returns `-1`; indexing the array at `-1` gives `undefined`, and setting `.isActive` on it throws. This was originally investigated as SC-SAAS-FRONTEND-EY, mistakenly conflated with SC-SAAS-FRONTEND-F4 (a different bug, `community-feed-stats-count.component.ts`, tracked separately as SAN-831) before the actual Sentry event data was pulled and the real culprit identified.

## Fix
Added `if (index !== -1)` before all 6 `[index].isActive = true` assignments. No functional change for ids that do match the master list; a mismatched id is now skipped instead of crashing.

No API/DTO/flag/tenant-scoping impact — six identical index guards in one component.

## Blast radius
`sc-saas-frontend`'s investor investments-details edit page only.

## Verification
`npx tsc --noEmit` — no new errors on this file (only pre-existing missing test-runner-globals errors in the unrelated `.spec.ts`, same workspace-wide issue seen elsewhere). No automated test suite exists for this repo yet — manual repro (edit an investor profile whose saved investment-type id no longer matches the master list) is the substitute verification, still to be done by hand.

Vishali reviewed and had this committed and pushed as `sc-saas-frontend@59b2d4aa` on `ai_native_setup_vishali`. Linear moved to Done. Sentry SC-SAAS-FRONTEND-EY marked resolved with a comment referencing the commit. Note this branch is still behind `main`'s deployed prod build (workspace-wide frontend deploy lag) — the fix won't reach production until the next deploy.

## Related
[[SAN-831]] (SC-SAAS-FRONTEND-F4) — a separate, unrelated bug that this ticket's Sentry issue was initially and incorrectly conflated with before investigation.
