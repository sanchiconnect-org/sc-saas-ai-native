---
id: SAN-1993
title: "ngx-ui-loader loaderId \"master\" duplicated in resource-viewer-modal (SC-SAAS-FRONTEND-HN)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1993
sentry: [SC-SAAS-FRONTEND-HN]
repos: [frontend]
commit: frontend@335b4000b (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1993: resource-viewer-modal duplicate "master" loader

## Root cause
* **Sentry:** `Error: [ngx-ui-loader] - loaderId "master" is duplicated.`
  * 1 event, 1 user, 2026-10-18, sineedge.sineiitb.org `/resources`, Edge on Windows, production, release `218edca78`.
  * The frame is `resource-viewer-modal.component.html` during the first change detection, where `NgxUiLoaderComponent.ngOnInit` → `bindLoaderData('master')` throws.
* **Where:** `src/app/modules/public/components/resources-component.sections/resource-viewer-modal/resource-viewer-modal.component.html:1` had a bare `<ngx-ui-loader></ngx-ui-loader>`, which claims "master".
* **How it fails:** the modal is opened over a page (`resources-detail-component.ts:115`), so if any other bare loader is already on screen, the modal's loader is a second "master". Other bare loaders include `register-modal` (reachable from this modal's download flow) or another stacked modal.
* **Not needed:** the modal never drives that loader. Its only `start()` in `ngOnInit` is commented out, and so is `onDocumentLoaded`/`stop()`.
* The file is unchanged since `99921364b`, so this is a live defect.

## Fix
Deleted the bare `<ngx-ui-loader></ngx-ui-loader>` at line 1, the same fix as SAN-837 (step-two-product) and SAN-836/628/630/548.
* `node scripts/loader-floor.js lower` → `loader-floor.json: 88 -> 87`. The file's entry is removed from the per-file list and `measuredAt` is 2026-10-22.
* A named `loaderId` (the SAN-1623 approach) was not used. That approach is for components that start their own loader, and this one never does.

## Blast radius / existing-flow impact
* No visible change: the removed loader was never started, so no spinner disappears.
* The modal's rendering, download, login/register and email-resource flows are untouched (template line 1 only).
* No API, DTO, flag or tenant-scoping impact.

## Verification
* `node scripts/loader-floor.js check` → `87 bare loaders, at the floor.`
* `npx tsc -p tsconfig.app.json --noEmit` → exit 0.
* No automated test was added. The existing `resource-viewer-modal.component.spec.ts` ("should create") is unaffected, and the `loader-floor` gate now guards the count.
* Manual check still to do: open a resource on `/resources`, confirm no console error, and confirm download/login still work.

## Related
SAN-837, SAN-836, SAN-630, SAN-628, SAN-548, SAN-1623 (loader floor). Same sweep: SAN-1986, SAN-1991, SAN-1994, SAN-1982.
