---
id: SAN-882
title: "Schemes page served at confusing /operational-cost-reimbursement URL"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-882
sentry: []
repos: [frontend]
commit: sc-saas-frontend@5e455016 (branch ai_native_setup_vishali)
created: 2026-09-21
updated: 2026-09-21
---

# SAN-882 — Update Schemes URL and tab navigation

## Root cause
Not a defect — a naming/URL mismatch. The "Schemes" sidebar item (`navMenus.ts`) and its top-level lazy route (`app-routing.module.ts`) were both keyed off `operational-cost-reimbursement`, even though that page's default/primary tab is **Schemes** (scheme cards) and "Operational Cost Reimbursement" is a secondary tab within the same page. The tab-switching mechanism itself was already correct: `OperationalCostReimbursementComponent.activeTab: 'schemes' | 'ocr' = 'schemes'` is a plain local property defaulting to `'schemes'`, toggled purely by `(click)` handlers in the template — no query param, child route, or NgRx state involved, and only one child route exists inside the lazy module (both tabs render from the same routed component). So direct nav/refresh already worked correctly under the old URL; the only thing wrong was the URL segment itself.

## Fix (round 1 — URL rename)
- `sc-saas-frontend/src/app/app-routing.module.ts`: renamed the top-level lazy route `path: 'operational-cost-reimbursement'` → `path: 'schemes'` (kept `canActivate: [AuthGuard]` and `loadChildren` unchanged), and added a new redirect route `{ path: 'operational-cost-reimbursement', redirectTo: '/schemes', pathMatch: 'full' }` immediately after it so existing bookmarks/shared links keep working (confirmed with the user rather than assuming — this was an open decision called out in the ticket).
- `sc-saas-frontend/src/app/shared/constants/navMenus.ts`: updated the "Schemes" nav item's `route: 'operational-cost-reimbursement'` → `route: 'schemes'`. Left `id`, `featureKey: 'operational_cost_reimbursement_enabled'`, and `accountTypes: [ACCOUNT_TYPE.STARTUP]` unchanged — they gate visibility/identity, not the URL.

## Scope revision — round 2 (direct user request, 2026-09-21)
After round 1 shipped, the user tested and reported the OCR tab showing active by default and the URL changing on tab click — initially read as a bug report. Investigation (inspecting the actual served `main.js`/lazy chunk from the running `ng serve`, not just source on disk) proved the round-1 code had neither behavior: `activeTab` defaulted to `'schemes'` and the tab buttons had no navigation call at all. The user then clarified this wasn't a bug report — it was a **new requirement**: they explicitly want the URL to reflect the active tab. Revised behavior, confirmed directly with the user rather than assumed:
- `/schemes` — default landing AND what selecting the Schemes tab navigates back to; never grows a tab segment.
- Selecting the OCR tab navigates to `/schemes/operational-cost-reimbursement`.
- Both are directly nav-able/refreshable and open the correct tab.
- Old `/operational-cost-reimbursement` bookmark still redirects to `/schemes` (round 1's redirect, unaffected).

(An intermediate version briefly made the Schemes tab navigate to `/schemes/schemes` too — the user corrected this immediately: Schemes should stay on plain `/schemes` since it's the default/root state, only OCR gets a segment.)

### Fix (round 2)
- `operational-cost-reimbursement.module.ts`: added one more child route (`operational-cost-reimbursement`) alongside the existing empty-path default, both pointing at `OperationalCostReimbursementComponent` with `data.tab` (`'schemes'`/`'ocr'`) telling it which tab to show initially.
- `operational-cost-reimbursement.component.ts`: injected `ActivatedRoute`; `ngOnInit()` reads `route.snapshot.data['tab']` to set the initial `activeTab` (still defaults to `'schemes'` via the empty-path route). Added `selectTab(tab)`, which sets `activeTab` and calls `router.navigate(tab === 'schemes' ? ['/schemes'] : ['/schemes', 'operational-cost-reimbursement'])`.
- `operational-cost-reimbursement.component.html`: both tab buttons call `selectTab('schemes')` / `selectTab('ocr')` instead of setting `activeTab` directly.

### Trade-off
The three tab states are now distinct Angular routes (required to get this exact URL shape), so switching tabs recreates the component (default `RouteReuseStrategy` doesn't reuse across different route configs) — each tab click now re-runs `ngOnInit()`, re-fetching eligibility and the schemes list, instead of the previous pure in-memory toggle. Functionally correct and still fast; flagged in the Linear comment in case it becomes a perf concern later.

## Blast radius
Full-repo grep for the literal `operational-cost-reimbursement` path string (`routerLink`/`router.navigate`/breadcrumbs) found only the edited call sites — all other ~25 files matching the broader string are module/service/state folder and file names (e.g. `OperationalCostReimbursementModule`, `operational-cost-reimbursement.service.ts`), which are identifiers, not URL segments, and were intentionally left unchanged. `AuthGuard` (applied at the top-level `schemes` route, inherited by both child routes) and the feature-flag/account-type gating inside the component are unaffected by either round of changes since neither depends on the path string.

## Final shipped state
- `/schemes` — default landing and the Schemes tab's own URL (no segment).
- `/schemes/operational-cost-reimbursement` — the OCR tab's URL.
- `/operational-cost-reimbursement` — old bookmark, redirects to `/schemes`.
- Files changed: `app-routing.module.ts`, `navMenus.ts`, `operational-cost-reimbursement.module.ts`, `operational-cost-reimbursement.component.ts`, `operational-cost-reimbursement.component.html` (all in `sc-saas-frontend`).

## Verification
`tsc --noEmit` clean after every round. Full `ng build --configuration local`: exit code 0 each time, no errors (only pre-existing CommonJS-dependency optimization warnings, unrelated to this change). Verified against the **live dev server**, not just source: downloaded and grepped the actual served `main.js` and the OCR module's lazy chunk from `localhost:4200` at each round to confirm the routes and `selectTab()` bindings compiled and running matched what was written. No automated regression test was added — a `RouterTestingModule`-based test was proposed for round 1 and the user opted to skip it. Not committed/pushed — user verifying locally first.
