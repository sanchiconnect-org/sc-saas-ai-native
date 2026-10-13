# SAN-1869 — public profile dynamic form view throws when a section has no `fields`

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1869 (Sentry SC-SAAS-FRONTEND-H0 and H1)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (missing null guards) on unexpected data

## Evidence
FRONTEND-H0 (8 production events) and H1 (6 production events): TypeErrors reading `fields` / `map` / `filter` / `find` of undefined in `public-profile-dynamic-single-form-view.component.ts`. One user on `isgbb-bharatcares.sanchiapp.com`, release `bcf88383d`.

## Root cause (observed vs inferred)
- **Observed:** the component dereferenced `formObject.fields`, `field.fields`, `section.fields`, `formObject.fields[index]['fields']` and `s.fields` in `isFieldVisible` with no guard.
- **Inferred:** a section in the `getFormsByCode` response has no `fields`. The backend data that produces it was **not identified**.

## Fix
`public-profile-dynamic-single-form-view.component.ts`: `(this.formObject.fields || [])`, `(field.fields || [])`, `(section.fields || [])`, `fields[index]['fields'] || []`, and `s?.fields?.find` in `isFieldVisible`. A section without fields now falls into the existing hide-empty-section logic and is dropped instead of throwing.

## Not fixed
Why the response contains a section with no fields (form definition data or backend shape); no backend check was made.

## Contract impact
None. Frontend-only tolerance for a missing `fields`; no endpoint, DTO, flag or auth change.

## Verification
`tsc` clean. No automated test added (guardian skill blocked). Not run in a browser or with the failing tenant's data.

## Commit
sc-saas-frontend `c42bf95be` (with SAN-1870) on `ai_native_setup_aman`. Pushed, not deployed.

## Sentry
H0 / H1 left to the sweep policy; reopen only on a build containing `c42bf95be`.
