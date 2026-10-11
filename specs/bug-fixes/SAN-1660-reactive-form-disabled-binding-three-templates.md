# SAN-1660 — `[disabled]` binding next to `formControlName` on three templates

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1660 (Sentry SC-SAAS-FRONTEND-Z, 361 events, 13 users)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (console noise, behaviour unaffected)

## Problem
Angular logs "It looks like you're using the disabled attribute with a reactive form directive..." with `console.warn` when `[disabled]` is bound on an
element that also has `formControlName`. `captureConsoleIntegration` forwards it to Sentry. SAN-558, SAN-830 and SAN-145 fixed other forms; three
templates still have it.

## Root cause
On a reactive-form element the `FormControlName` directive claims the `disabled` input, only warns, and does not apply the value, so the binding has no effect:
1. `investors/pages/edit/organization-details/organization-details.component.html` (`organizationName` input, `[disabled]="profileCompleness?.isApproved"`).
   The component already calls `organizationForm.get('organizationName').disable()` when the profile is approved (`organization-details.component.ts:216`).
2. `auth/pages/register/sign-up-forms/account-information/account-information.component.html` (partner `ng-select`,
   `[disabled]="!!partnerFromLocalStorage"`). The select is also `[readonly]` with the same condition, which stays.
3. `tracker/components/rating-modal/rating-modal.component.html` (`ngx-star-rating`, `[disabled]="false"`, a constant no-op).

## Fix
Remove the three bindings. No TypeScript change. Behaviour-preserving because the removed binding was ignored by Angular on these elements.

## Contract impact
None. Frontend templates only; no API, flag, tenancy or auth change, so `/audit-contract`, `/trace-flag` and `/check-isolation` have nothing to check.

## Not covered
The largest Sentry groups (OTP 2Q/3H/34, Invalid access token 2A/5Q/5P/67) are already fixed in code (SAN-599/601/608, SAN-471/930/932) and still fire from
tenants running old builds (e.g. release `51eb6706`, 18 Aug, predates the 20 Aug and 4 Sep filters). That needs a deploy, not a code change.

## Checks that the removals are no-ops
- ng-select (`@ng-select/ng-select` `ng-select.component.d.ts`): `disabled` is a getter only, not an `@Input`, so the binding reached only `FormControlName`.
- ngx-star-rating: `disabled` is an `@Input`, but the component defaults it to `false` in its own init, and the binding was the constant `false`.
- organization-details: the control is already disabled in TypeScript (line 216) when the profile is approved.

## Verification
- `tsc --noEmit -p tsconfig.app.json` and `ngc -p tsconfig.app.json --noEmit` both exit 0 (ngc compiles the templates).
- No automated test added (none exists for these templates). Not checked in a browser, so the Sentry warning going away is expected but not observed.

## Commit
sc-saas-frontend `77e203d58` on `ai_native_setup_aman`. Not deployed.
