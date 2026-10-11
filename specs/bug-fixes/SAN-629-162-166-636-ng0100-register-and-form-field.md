# SAN-629 / SAN-162–166 / SAN-636 — NG0100 from synchronous state changes inside change detection

- **Linear:** SAN-629 (SC-SAAS-FRONTEND-5J/5R); SAN-162, 163, 164, 165, 166, 636 (FormFieldComponent NG0100 group)
- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (latent anti-pattern; symptom is dev-mode only)

## Problem
`ExpressionChangedAfterItHasBeenCheckedError` (NG0100):
- SAN-629: `register.component.html` `[disabled]="disableContinueButton || loader"`.
- SAN-162/163/166/636: a form-control value changes undefined -> null / [] between checks. SAN-164 (`disabled`) and SAN-165 (`ng-valid`)
  are the same mechanism seen through validity.

## Root cause
- Register: `AccountTypeComponent` / `AccountInformationComponent` emit validity synchronously from `ngOnInit` / `valueChanges`, and the
  parent handlers set `disableContinueButton` inside the same pass.
- FormFieldComponent (`modules/dynamic-forms/event-forms/form-field`; the only such component): `ngOnChanges` runs inside the parent's pass
  and called `handleCheckBoxChange`, `handleRadioGrpChange`, `handleCheckboxGrpChange`, `handleTextboxGrpChange`, `handleNumberboxGrpChange`,
  each of which patches the shared form control synchronously.

## Fix
Apply those updates in a microtask (`Promise.resolve().then(...)`), the same pattern as `320caa25b` / `c8b7b8447` (SAN-160/161): same values,
set right after the pass. `register.component.ts`: `checkAccountFormValid`, `checkAccountInformationValid`, `checkOtpCodeValid`.
`form-field.component.ts`: new `applyAfterChangeDetection()` wrapping the five calls in `ngOnChanges`.

## Not fixed
- SAN-935 (StepTwoProductComponent `disabled`): no code path mutating the bound values during a pass was found; needs the Sentry stack/breadcrumb.
- SAN-164/165: attribution to FormFieldComponent is the best-supported reading; the exact template binding was not identified.
- SAN-635 was already covered by `320caa25b`.

## Contract impact
None. Frontend-only; no API, flag, tenancy or auth change.

## Verification
- `tsc --noEmit` and `ngc` clean. No automated test added. Not verified in a browser (NG0100 does not occur in production builds).

## Commits
sc-saas-frontend `a34bb938e` (SAN-629), `9460997b4` (SAN-162/163/164/165/166/636), on `ai_native_setup_aman`. Not deployed.
