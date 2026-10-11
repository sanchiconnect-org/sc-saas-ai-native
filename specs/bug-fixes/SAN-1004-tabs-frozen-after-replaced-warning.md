# SAN-1004 — Profile edit tabs stay faded/unclickable after the warning is replaced

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1004
- **Repo:** sc-saas-frontend · **Type:** Bug · **Priority:** High · **Assignee:** Mahima Sharma
- **Classification:** CODE_ERROR

## Problem
After filling the startup "Program Office" custom form, the whole profile-edit tab strip went
faded (50% opacity) and stayed unclickable until reload.

## Root cause
`ToastAlertService.showCenteredAlert()` adds `body.tabs-frozen-during-warning`. In `styles.scss`
that class sets `opacity: 0.5; pointer-events: none` on all nav-links tabs. The class was removed
only in `Swal.fire(...).then()`. In SweetAlert2 11.7.3, a new `Swal.fire()` (e.g. an auto-save
toast) opening while the warning is shown calls `_destroy()` on it without resolving its promise.
The `.then()` never ran and the class stuck.

## Fix
- `src/app/shared/utils/toast.service.ts`: remove the class in the `didDestroy` hook, which runs on a normal close and on replacement
- `src/app/shared/utils/toast.service.spec.ts`: exact-params assertion now uses `objectContaining`; the removal test uses a never-resolving `fire()` promise and calls `didDestroy`

## Verification
- `tsc --noEmit` (app + spec): clean
- `ng test --include=toast.service.spec.ts`: could not run. The Karma bundle already fails on 17 unrelated specs, so 0 tests executed
- Not verified in a browser

## Commit
sc-saas-frontend@7871102d (branch ai_native_setup_mahima)
