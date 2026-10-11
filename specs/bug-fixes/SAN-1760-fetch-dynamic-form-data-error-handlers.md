# SAN-1760 — fetchDynamicFormData callers have no error handler

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1760 (Sentry SC-SAAS-FRONTEND-2W)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (unhandled observable error) over an infrastructure 504

## Evidence
Sentry SC-SAAS-FRONTEND-2W: a 504 on `profile/data/<type>/<uuid>` reported as an unhandled error. All 8 callers of `PublicApiService.fetchDynamicFormData` subscribed with a success callback only.

## Root cause
`PublicApiService.fetchDynamicFormData` already shows a toast and rethrows. A subscriber with no error callback turns the rethrown error into an unhandled one, which Sentry captured. The 504 itself comes from upstream/infra (reported in the sweep as a supernova 504).

## Fix
Each caller now passes a no-op error callback with a comment (the toast has already been shown): `corporate-public-profile-v2`, `individual-public-profile`, `investor-public-profile-v2`, `mentor-public-profile`, `partners-details`, `profile-office-public-profile`, `service-provider-public-profile`, `startup-public-profile-v2` (all `.component.ts`). On failure `dynamicFormData` stays unset.

## Not fixed
The 504 on the profile-data endpoint (infra). The service's rethrow was kept deliberately.

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: the module specs of corporate, individual-profile, investors, mentors, partners-details, program-office, service-provider and startups under `sc-saas-frontend/src/app/modules/`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `49ee4426f` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-2W resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
