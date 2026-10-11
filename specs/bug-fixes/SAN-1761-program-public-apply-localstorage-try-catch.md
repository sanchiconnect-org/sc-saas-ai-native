# SAN-1761 — program-public-apply applicationMeta throws when localStorage is blocked

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1761 (Sentry SC-SAAS-FRONTEND-2F)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (unguarded browser storage access)

## Evidence
Sentry SC-SAAS-FRONTEND-2F: Firefox throws (NS_ERROR_FAILURE/ABORT) on `localStorage` access when site storage is blocked or unavailable; the access is in the `applicationMeta` getter.

## Root cause
`ProgramPublicApplyComponent.applicationMeta` read `localStorage.getItem('application-<uuid>')` and `JSON.parse`d it with no guard, and it runs on every change-detection pass.

## Fix
`src/app/modules/programs/program-public-apply/program-public-apply.component.ts`: the read and parse are wrapped in try/catch; on any error the value is `undefined` ("no saved application"), so the existing `!val?.email` path sets `activeTab = 'program-information'`.

## Not fixed
Other `localStorage` readers in the app were not audited here.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/programs/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `49ee4426f` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-2F resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
