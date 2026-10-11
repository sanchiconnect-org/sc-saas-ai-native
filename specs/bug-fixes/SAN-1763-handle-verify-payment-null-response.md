# SAN-1763 — handleVerifyPayment reads response.length when the child emits null

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1763 (Sentry SC-SAAS-FRONTEND-GV)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (null dereference)

## Evidence
Sentry SC-SAAS-FRONTEND-GV (new group, `environment: local`): `Cannot read properties of null (reading 'length')` in `handleVerifyPayment`.

## Root cause
The `membership-plans` child emits `null` when its payment-verify API call errors. `handleVerifyPayment` in two parents then evaluated `response.length === 0` on that null.

## Fix
Early `if (!response) { return; }` (comment: the child emits null when payment-verify errors; nothing to toggle) in `src/app/modules/dynamic-forms/application-program-management-dynamic-form/application-program-management-dynamic-form.component.ts` and `src/app/modules/programs/programs-details-page/programs-details-page.component.ts`. `isPaymentVerify` is still assigned before the return, so the payment and submit button flags are simply left as they were.

## Not fixed
The child's decision to emit `null` on error was kept as is.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/dynamic-forms/module.spec.md` and `programs/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `d18c43e4c` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-GV resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
