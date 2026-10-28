---
id: SAN-1994
title: "step-two-product handleBusinessModelSave reads 'id' of undefined when no stage is selected (SC-SAAS-FRONTEND-HJ)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1994
sentry: [SC-SAAS-FRONTEND-HJ]
repos: [frontend]
commit: frontend@553628da2 (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1994: step-two-product crashes when Next is clicked with no stage

## Root cause
* **Sentry:** `TypeError: Cannot read properties of undefined (reading 'id')`.
  * 1 event, 1 user, 2026-10-16, app.sanchiconnect.com `/startups/dashboard` (edit-profile modal), Chrome on Windows, production, release `3fe291506`.
  * Path: Next button (`step-two-product.component.html:239`) → `handleSave()` → `handleBusinessModelSave()`.
* **Where:** `src/app/modules/startups/components/edit-profile-modal/stepper/step-two-product/step-two-product.component.ts:335` (now inside the guard) did `{ productStageId: this.selectedStage.id }`.
* **How it fails:** `selectedStage` is `undefined` unless the user picks a stage, or the saved stage is re-selected on load.
  * The Next button's `[disabled]` no longer checks it (`<!-- !selectedStage || -->` is commented out in the template).
  * Clicking the active stage again deselects it.
  * The saved-stage re-select at line 125 runs over `productStages`, which may not have loaded yet.
* **Effect:** `handleSave()` had already fired the product-info and elevator-pitch saves, but the throw stopped `saveBusinessModels` from running, so the user's business-model selection was lost.
* The only change since `3fe291506` is 4 unrelated lines from SAN-1930, so this is a live bug.

## Fix
The stage save (`saveProductInfo({ productStageId })` and its `loader = true`) is wrapped in `if (this.selectedStage)`. `saveBusinessModels` runs either way.
* **With a stage selected:** the same two calls as before, in the same order.
* **With no stage:** no stage request is sent, so the stage already saved on the backend (if any) is left as it is instead of being overwritten. The business models are now saved instead of being lost.

## Blast radius / existing-flow impact
* The happy path is identical. The behaviour only differs where it used to throw.
* No new UX: Next is still enabled without a stage, as before.
* No API, DTO, flag or tenant-scoping impact.
* `[DESIGN DECISION PENDING]` (not blocking this fix, for the product owner): the Stage heading has a red `*`, but the Next button doesn't require a stage. Should Next be disabled until a stage is picked (re-enable the commented `!selectedStage ||`)? That is a UX change, so it was not made here.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → exit 0.
* Two new specs in `step-two-product.component.spec.ts`:
  * no stage → no throw, `saveProductInfo` not called, `saveBusinessModels({ businessModelIds: [7] })` called;
  * stage selected → `saveProductInfo({ productStageId: 3 })` and `saveBusinessModels` both called.
* `npx ng test --watch=false --browsers=ChromeHeadless --include=<step-two-product spec> --include=<dynamic-form-submit spec>` → `Executed 6 of 6 SUCCESS`, `TOTAL: 6 SUCCESS`.
* Lint: none configured in this repo.

## Related
SAN-837 (same component, loader). Same sweep: SAN-1986, SAN-1991, SAN-1993, SAN-1982.
