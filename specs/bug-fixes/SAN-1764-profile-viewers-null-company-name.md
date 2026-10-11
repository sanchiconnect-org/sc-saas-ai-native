# SAN-1764 — profile-viewers openDetailsView crashes on a null viewerCompanyName

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1764 (Sentry SC-SAAS-FRONTEND-8H)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (null dereference)

## Evidence
Sentry SC-SAAS-FRONTEND-8H: `viewerData.viewerCompanyName.split(' ')` on null in `ProfileViewersComponent.openDetailsView`.

## Root cause
The viewer's company name can be null (inferred: viewers without a company name), and the method built the route slug by splitting it unconditionally.

## Fix
`src/app/modules/account/pages/profile-viewers/profile-viewers.component.ts`: `(viewerData.viewerCompanyName || '')` is used for the slug, and the slug route segment is only appended when non-empty, so the opened URL is `/<type>/profile/<uuid>` for nameless viewers. The component is declared in `SharedModule`, not `AccountModule`.

## Not fixed
The backend null source was not investigated.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/account/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `d18c43e4c` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-8H resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
