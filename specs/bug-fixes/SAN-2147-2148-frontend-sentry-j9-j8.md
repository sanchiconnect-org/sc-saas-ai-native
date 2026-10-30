---
id: SAN-2147-2148
title: "sc-saas-frontend: SC-SAAS-FRONTEND-J9 (undefined form group) and J8 / HW (expected 401 / 403 reported as warnings)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-2147
sentry: [SC-SAAS-FRONTEND-J9, SC-SAAS-FRONTEND-J8, SC-SAAS-FRONTEND-HW]
repos: [frontend]
related: [SAN-2111, SAN-1959, SAN-1899, SAN-2032, SAN-2132, SAN-2148]
commit: sc-saas-frontend 2fafe6200 on ai_native_setup_aman
created: 2026-10-30
updated: 2026-10-30
---

# SAN-2147 / SAN-2148: two real frontend Sentry groups on the current build

## Triage of the 14 unresolved groups (project sc-saas-frontend, 90 days)
Twelve already had Linear tasks marked Done (SAN-1673, 598, 1923 / 1760 / 2123, 1759, 1899, 922, 1623 / 2035, 2032, 661 and others). Their events in the last 24 hours came from older builds (releases `218edca78`, `bcf88383d`, `33244b02e`, `da74b0962`, `51eb6706`, `dab63831`, `022eafd6`): users keep running cached PWA builds (see SAN-1925, SAN-2123), so they are not new bugs. Only J8 had events from the current production build (`3d44c42be`), and J9's code has no guard on `main`.

## SAN-2147 (J9)
* Event: `TypeError: Cannot read properties of undefined (reading 'get')` at `form.utils.ts:308`, 1 event, dev, release `96646ef05`.
* Path: payment status subscribe -> `toggleButtons` -> `calculateProgressOnly` -> `traverseAllFormFields`. For a non-multi section the group list is `[dynamicFormGroup]`; when the form is not built yet it is `[undefined]`.
* Fix: `traverseAllFormFields` skips a missing group and reads the multi-value section with `dynamicFormGroup?.get(...)`.

## SAN-2148 (J8 / HW)
* Event: `applicationProgramManagementApplicationDetails( This application belongs to someone else. )`, 11 events, 2 users, production, current release.
* Cause: the backend applicant check (`applicant-or-owner.guard.ts`, SAN-1959) answers `/details` with 403 `APPLICANT_NOT_OWNER` or 401 `APPLICANT_TOKEN_REQUIRED` / `_EXPIRED`. The catch block only skipped 404 and status 0, so each went to Sentry as a `console.warn`.
* Fix: 401 and 403 are skipped as well. Other statuses still warn, without the applicant's email.
* The returning-applicant case (stored email, no valid token) already gets the OTP prompt (`ensureApplicantToken()`, see the programs module spec); a 403 means the stored token belongs to a different email.

## Verification
* `npx tsc --noEmit -p tsconfig.spec.json` -> no errors.
* `ng test --watch=false --browsers=ChromeHeadless` on `form.utils.spec.ts` and `program-public-apply.component.spec.ts` -> `TOTAL: 44 SUCCESS`.
* With `form.utils.ts` reverted, the new test "does not throw when the form group is not built yet" fails: `TOTAL: 1 FAILED, 6 SUCCESS`; restored afterwards.
* Not run: `npm run gates` (production build and the full Karma suite with floors).

## Open
* Not deployed: it has to reach `ai_native_setup`, then `main`, and be built. Then check J9 / J8 / HW get no events from a release that contains it, and resolve them in Sentry.
* Sentry groups from old builds (2J, 17, 1, 2W, 14, EX, 7V, EP, HN, JA) can be marked resolved in the current release so only newer builds reopen them.

## Spec updates made
* `src/app/modules/programs/module.spec.md` (401 / 403 handling), `src/app/shared/module.spec.md` (`form.utils.ts`).
