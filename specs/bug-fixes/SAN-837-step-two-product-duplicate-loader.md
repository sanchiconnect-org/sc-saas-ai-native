---
id: SAN-837
title: "Duplicate ngx-ui-loader \"master\" registration when step-two-product modal opens over host page"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-837
sentry:
  - SC-SAAS-FRONTEND-29
repos: [frontend]
commit: sc-saas-frontend@bf1d0d3f (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-837 — step-two-product duplicate loader

## Root cause
`Error: [ngx-ui-loader] - loaderId "master" is duplicated.` (52 occurrences / 43 users — highest-impact of the ngx-ui-loader duplicate group.) `edit-profile-modal/stepper/step-two-product/step-two-product.component.html:1` had a bare `<ngx-ui-loader></ngx-ui-loader>`, and the component calls `this.ngxLoaderService.start()/.stop()` with no explicit loaderId (defaults to "master"). This modal step opens over a host page (e.g. `/startups/dashboard`) that already renders its own master loader, so opening the modal registers a duplicate. The sibling `meeting-details-modal.component.html` had already fixed the identical pattern.

## Fix
Deleted the `<ngx-ui-loader></ngx-ui-loader>` at line 1 of `step-two-product.component.html`, matching the established `meeting-details-modal.component.html` fix — the modal's start/stop loader calls now fall through to the host page's existing master loader instance.

No API/DTO/flag/tenant-scoping impact — template-only, one duplicate element removed.

## Blast radius
`sc-saas-frontend`'s startup edit-profile modal, product step.

## Verification
Full `ng build --configuration development` (AOT) — exit code 0, no errors on this file. No automated test suite exists for this repo yet — manual repro (open the edit-profile modal, navigate to the product step, confirm no console error and loading spinner still shows/hides during save) is the substitute verification, still to be done by hand before commit.

## Related
Same defect class as SAN-836, SAN-632, SAN-630, SAN-628, SAN-548 — all "ngx-ui-loader master duplicated," each a distinct call site.
