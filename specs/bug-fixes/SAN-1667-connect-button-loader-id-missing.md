# SAN-1667 — ConnectButton starts/stops an ngx-ui-loader that does not exist

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1667 (Sentry SC-SAAS-FRONTEND-5Y 4 events / 4 users, GT 1 event)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (console error)

## Problem
`[ngx-ui-loader] - loaderId "connect-button-<random>" does not exist.` on app.sanchiconnect.com `/startups/dashboard`.

## Root cause
`ConnectButtonComponent` renders `<ngx-ui-loader [loaderId]="loaderId">` inside `*ngIf="brandDetails.features?.connections"` but called `ngxLoaderService.startLoader/stopLoader(this.loaderId)`
unconditionally at 15 sites, several inside `finalize()` callbacks. The library reports an unregistered id when (1) the tenant has the `connections` feature off, so the element never exists,
or (2) a `finalize()` runs after the component is destroyed, which unregisters the loader. (The earlier duplicate-id error was fixed by the per-instance random id.)

## Fix
All 15 calls go through `startConnectLoader()` / `stopConnectLoader()`, which do nothing when `!brandDetails?.features?.connections` or the component `isDestroyed` (set in `ngOnDestroy`).

## Not fixed
SC-SAAS-FRONTEND-GP (`Cannot read properties of undefined (reading 'get')` in the same component's template, 1 event) was not diagnosed; no reproduction.

## Contract impact
None. No API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` and `ngc` exit 0 (ngc compiles the template). No automated test added (no spec for this component). Not checked in a browser.

## Commit
sc-saas-frontend `f61fb929a` on `ai_native_setup_aman`. Not deployed.
