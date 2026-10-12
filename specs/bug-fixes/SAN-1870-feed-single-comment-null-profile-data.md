# SAN-1870 — feed comment delete icon throws when `profileData` is null

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1870 (Sentry SC-SAAS-FRONTEND-H5 and H9)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (missing null guard in a template)

## Evidence
FRONTEND-H5: 1 production event (release `9a97d8378`); FRONTEND-H9: 4 local events. TypeError reading `uuid` of null in `feed-single-comment.component.html` line 34, `*ngIf="profileData.uuid === comment.user.uuid"`.

## Root cause (observed vs inferred)
- **Observed:** the template reads `profileData.uuid` and `comment.user.uuid` unguarded.
- **Inferred:** `profileData` is null (not loaded yet or failed to load). Not reproduced.

## Fix
`feed-single-comment.component.html:34`: `*ngIf="profileData?.uuid && profileData?.uuid === comment?.user?.uuid"`. The `profileData?.uuid &&` part also stops two missing uuids from comparing equal (`undefined === undefined`) and showing the delete icon.

## Not fixed
Other `comment.user.` reads in the template remain unguarded. Why `profileData` is null was not investigated.

## Contract impact
None. Template guard only; no endpoint, DTO, flag or auth change.

## Verification
`tsc` clean. No automated test added (guardian skill blocked). Not run in a browser.

## Commit
sc-saas-frontend `c42bf95be` (with SAN-1869) on `ai_native_setup_aman`. Pushed, not deployed.

## Sentry
H5 / H9 left to the sweep policy; reopen only on a build containing `c42bf95be`.
