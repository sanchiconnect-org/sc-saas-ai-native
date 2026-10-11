# SAN-1762 — growth-matrics handleEdit uses showLoaderOnConfirm without preConfirm

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1762 (Sentry SC-SAAS-FRONTEND-AH)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (SweetAlert2 misuse warning)

## Evidence
Sentry SC-SAAS-FRONTEND-AH: SweetAlert2 warns when `showLoaderOnConfirm` is set without a `preConfirm`; the source is `growth-matrics.component.ts` `handleEdit`.

## Root cause
The `Swal.fire` options in `handleEdit` set `showLoaderOnConfirm: true` but define no `preConfirm`, so there is nothing for the loader to wait on.

## Fix
`src/app/modules/growth-matrics/growth-matrics.component.ts`: removed `showLoaderOnConfirm: true` (nothing else in the dialog changed). Inferred: no async work runs inside the dialog, so no spinner is lost.

## Not fixed
The same pattern remains untouched in `facilities-management/facility-details/facility-details.component.ts` and `ip-search/ip-search-details/ip-search-details.component.ts`.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/growth-matrics/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `49ee4426f` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-AH resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
