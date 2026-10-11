---
id: SAN-830
title: "[disabled] binding still hard-coded on partners-dashboard industry-technology form (reactive form directive warning)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-830
sentry:
  - SC-SAAS-FRONTEND-Z
repos: [frontend]
commit: sc-saas-frontend@a01b1d58 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-830 — partner-industry-technology hard-coded disabled binding

## Root cause
`partner-industry-technology.component.html:68` had a blanket `[disabled]="true"` alongside `[formControlName]="industry.id"`. Angular logs "It looks like you're using the disabled attribute with a reactive form directive" whenever a form-bound control also carries a static `disabled` attribute, because reactive forms are supposed to control enabled/disabled state programmatically, not via the template attribute.

The identical bug existed on the sibling startups-module page (`startups/pages/edit/industry-technology/industry-technology.component.html`) and was fixed 2026-09-03 by commit `31fa01bf` (SAN-558) by removing the blanket `[disabled]` binding, since the component already calls `ctrl.disable()/enable()` programmatically per control (confirmed here too: `partner-industry-technology.component.ts`'s `industrySelectionChange()` at line 171 already does `ctrl.disable()`/`ctrl.enable()` based on `isMaxIndustriesSelected`). The SAN-558 fix was never ported to this partners-dashboard copy.

## Fix
Removed `[disabled]="true"` from `partner-industry-technology.component.html:68`. Enable/disable behavior is unchanged — it was already fully handled by `industrySelectionChange()`'s per-control `ctrl.disable()/enable()` calls; the static attribute was dead weight only triggering the framework warning.

No API/DTO/flag/tenant-scoping impact — frontend template-only, one attribute removed.

## Blast radius
`sc-saas-frontend`'s partners-dashboard industry-technology edit page only.

## Verification
Full `ng build --configuration development` (AOT) — exit code 0, no errors/warnings on this file. No automated test suite exists for this repo yet — manual repro (open the page, select industries up to the max, confirm remaining checkboxes still disable/enable correctly and the console warning is gone) is the substitute verification, still to be done by hand before commit.

## Related
Mirrors SAN-558 (SC-SAAS-FRONTEND equivalent bug on the startups-module copy of this same form pattern) — that fix should have been audited for sibling copies at the time; this ticket closes the gap.
