# SAN-920 — hire page mounts two bare ngx-ui-loader instances (duplicate master id)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-920 (Sentry SC-SAAS-FRONTEND-EP)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (duplicate ngx-ui-loader master id); systemic cause NOT fixed

## Evidence
Sentry SC-SAAS-FRONTEND-EP (ngx-ui-loader `master` loader duplicated). The event is from release `022eafd6` (2026-07-31). One collision was proven from source: the `/hire` page.

## Root cause
A bare `<ngx-ui-loader>` registers the default `master` id. `hire.component.html` renders `app-dashboard-common-calender`, whose template starts with its own bare `<ngx-ui-loader>`, while the hire page already has a master loader, so two were mounted at once.

## Fix
`shared/common-components/startup-investor-dashboard-common-calender/dashboard-common-calender.component.{ts,html}`: new `@Input() renderLoader = true` and `<ngx-ui-loader *ngIf="renderLoader">`. `modules/hire/hire/hire.component.html` passes `[renderLoader]="false"`. Default behaviour for every other host is unchanged.

## Considered and rejected
Bulk-renaming loader ids: it would break modals that rely on the shared master loader.

## Not fixed
Only ONE collision was proven. About 95 other bare `<ngx-ui-loader>` elements remain (107 counted in the app, 8 have a `loaderId`); whether any two are mounted together cannot be proven from source. SAN-433's systemic fix (CI guard or an auto-id wrapper) was never implemented. EP may recur from another page.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/hire/module.spec.md` (and a cross-reference in `calender/module.spec.md`).

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `49ee4426f` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-EP resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
