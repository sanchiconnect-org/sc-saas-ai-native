---
id: SAN-836
title: "Duplicate ngx-ui-loader \"master\" registration in extra-intro-program-office (two loaders in one template)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-836
sentry:
  - SC-SAAS-FRONTEND-3F
repos: [frontend]
commit: sc-saas-frontend@1f57b9aa (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-836 — extra-intro-program-office duplicate loader

## Root cause
`Error: [ngx-ui-loader] - loaderId "master" is duplicated.` `extra-intro-program-office.component.html` had two bare `<ngx-ui-loader></ngx-ui-loader>` elements in the same component — line 1 (unconditional) and line 6 (inside `*ngIf="!isPreviewPage"`, true on the normal edit route `/program-office-members/edit/custom-forms/:uuid/:slug`, matching the Sentry event URL). Both default to loaderId "master", so the second mount registers a duplicate.

## Fix
Deleted the line-6 `<ngx-ui-loader></ngx-ui-loader>`, kept line 1. The page still has exactly one master loader instance, same as intended.

No API/DTO/flag/tenant-scoping impact — template-only, one duplicate element removed.

## Blast radius
`sc-saas-frontend`'s program-office-members edit/custom-forms page (non-preview mode).

## Verification
Full `ng build --configuration development` (AOT) — exit code 0, no errors on this file. No automated test suite exists for this repo yet — manual repro (open the page in non-preview mode, confirm no console error and the loader still shows/hides correctly during save actions) is the substitute verification, still to be done by hand before commit.

## Related
Same defect class as SAN-837, SAN-632, SAN-630, SAN-628, SAN-548 — all "ngx-ui-loader master duplicated," each a distinct call site across the app rather than one shared bug.
