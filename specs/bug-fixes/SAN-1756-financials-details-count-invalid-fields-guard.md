# SAN-1756 — financials-details countInvalidFields reads financeForm before it exists

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1756 (Sentry SC-SAAS-FRONTEND-GJ)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (null dereference)

## Evidence
Sentry SC-SAAS-FRONTEND-GJ: `Cannot read properties of undefined (reading 'controls')` from the startups `FinancialsDetailsComponent` `countInvalidFields` getter. Event counts were not recorded in the sweep note.

## Root cause
`countInvalidFields` iterates `this.financeForm.controls`, but the template binds the getter before `createForm()` has assigned `financeForm`, so the first change-detection pass sees `undefined`.

## Fix
`src/app/modules/startups/pages/edit/financials-details/financials-details.component.ts`: the getter returns 0 when `!this.financeForm`; the rest is unchanged. Inferred: the count shows 0 until the form is built, then the real value.

## Not fixed
Nothing else in the component was changed; the template/`createForm()` ordering itself was left alone.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/startups/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `49ee4426f` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-GJ resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
