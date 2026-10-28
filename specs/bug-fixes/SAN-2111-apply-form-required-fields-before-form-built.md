---
id: SAN-2111
title: "Program apply form: isSectionVisibleCommon reads .value of an undefined dynamicFormGroup"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2111
sentry: [SC-SAAS-FRONTEND-J3]
repos: [frontend]
related: []
commit: frontend@86a82ab91 (branch ai_native_setup_vishali, pushed)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2111: required-field recount runs before the form exists

## Root cause
* J3: 4 events, dev, `/programs/apply/fin2597/final-test`.
* Race inside `application-program-management-dynamic-form.component.ts`:
  * `getFormsList()` (~:380) starts async `getEventDetails()` without awaiting it, then calls `checkPricingDetails()`.
  * `getEventDetails()` only calls `buildForm()` (:1077) after its master-data fetches resolve.
  * `fetchPricing → verifyPayment` (next callback ~:1573) → `updateEmptyRequiredFields()` can therefore run before `this.dynamicFormGroup` exists, and `form.utils.ts:350` reads `.value` of undefined.
* The throw also skipped the Pay/Submit button toggles that follow it in `verifyPayment`.

## Fix
`updateEmptyRequiredFields()` (:703-709) returns early if `this.dynamicFormGroup` is not built yet. Once the form exists, `getEventDetails → initiateParticipation() → patchForm()` recomputes the list, and its `valueChanges` subscription keeps it current. `form.utils.ts` is unchanged.

## Blast radius / existing-flow impact
Frontend only. Visibility rules are unchanged whenever the form exists. In the race window the method skips instead of throwing, and the button toggles now run.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → 0; `npm run gates` → all 5 gates 0 (1338/1338)
* No new automated test. Manual: open a paid program apply link on a slow connection.
