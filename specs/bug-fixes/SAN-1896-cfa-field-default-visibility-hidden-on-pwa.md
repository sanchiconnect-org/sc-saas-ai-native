# SAN-1896 — CFA form field never edited in the builder is hidden on the PWA apply form

Linear: https://linear.app/sanchiconnect/issue/SAN-1896 · Repo: `sc-saas-frontend` · Priority: Medium · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
A field dropped into the admin form builder and saved without ever saving its properties panel is never shown to applicants on the PWA, though the builder shows it.

## Evidence
- Dev `[QA] E2E template form` has one such field ("Enter Field Title"); every program importing that form shows an empty application form.
- `sc-saas-e2e` `tests/cfa/p3-apply-guest.spec.ts` (known-failing `test.fail`).

## Root cause
- Admin gives a newly dropped field the default rule `{show:"show", field:null, condition:"is", value:null}` (`sc-saas-admin/modules/form-management/edit-form.php:236`). The properties panel save rewrites `field` to `"none"`.
- `isFieldVisibleCommon()` (`shared/utils/form.utils.ts`) only treated `show` empty/`"null"` or `field === "none"` as "no rule". For `field: null` it evaluated `formValues[null] === null` → `undefined === null` → false, so the field was hidden (and its validators cleared, value reset).
- The admin builder itself already treats `field: null` as "no rule" (`themes/default/html/form-management/edit-form.php:3926`), which is why the builder looked fine.

## Fix (`sc-saas-frontend` only)
- `src/app/shared/utils/form.utils.ts`: `isFieldVisibleCommon()` treats a rule with no source field (`!visiblitySetting.field`: null / undefined / `""`) as "no rule" → always visible, same as `"none"`. Fixes already-saved fields without re-editing. `isFieldVisibleCommon` is shared by CFA apply, event forms, form preview and form submit.
- `src/app/shared/utils/form.utils.spec.ts` (new, 5 cases): default null rule, `"none"`, `""`, real `is` rule, real `is not` rule.

## Behaviour change to be aware of
A previously hidden **required** field with the default rule now shows and is validated.

## Not done / follow-ups
- Admin default (`edit-form.php:238`, `"field" => null` → `"none"`) intentionally NOT changed here (issue is labelled Repo: Frontend). Optional cleanup; the frontend fix is sufficient. Would be a separate Admin issue.
- `sc-saas-e2e` P3 test: remove its `test.fail` after this is deployed and verified (repo not in this workspace).

## Verification
- `tsc --noEmit -p tsconfig.app.json`: clean.
- `ng test --include form.utils.spec.ts` (ChromeHeadlessCI): 5/5 pass; with the fix reverted, 2 of 5 fail (null and empty-string cases), so the test catches the bug.
- No ESLint (not configured in this repo). Full Karma suite not run. No live PWA check.

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`. The working tree also holds unrelated local-dev changes (`angular.json`, `proxy.conf.js`, `environment.local.ts`, `tenant.service.ts`) that must not go into this commit.
