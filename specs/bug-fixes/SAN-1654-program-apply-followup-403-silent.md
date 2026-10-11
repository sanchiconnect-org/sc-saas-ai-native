# SAN-1654 — Program apply: follow-up apply 403 silently dropped after form submit

- **Linear:** SAN-1654 (SC-SAAS-FRONTEND-74, 55 events, local-dev traffic)
- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (user feedback missing)

## Problem
After a public program application form is submitted, a follow-up apply request can be refused with a 403. The component had no error
handler for it, so the applicant saw nothing and Sentry recorded an unhandled fault.

## Fix
`program-public-apply.component.ts`: inject `ToastAlertService` and add an error handler on the apply call that tells the applicant the
request was refused (the backend message when present). No change to the success path or to who may apply.

## Contract impact
None. The backend already returns the 403; only the client now surfaces it. No API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` clean. No automated test added. Not checked in a browser.

## Commit
sc-saas-frontend `e5c36e21e` on `ai_native_setup_aman`. Not deployed. (An earlier commit message mis-referenced another issue; it was re-committed under SAN-1654 before pushing.)
