# SAN-1674 — event-registration question file upload: uncaught rejection, and a failed file still counted as the answer

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1674 (Sentry SC-SAAS-FRONTEND-2M, 69 users, 105 events, recurred after SAN-481)
- **Repo:** sc-saas-frontend · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (unhandled rejection + a validation hole)

## Why it repeated
SAN-481 (`f0484689f`, 2026-08-24) added try/catch around the forms-management uploads (`FormFieldComponent`). That commit is an ancestor of the builds that still produced 2M events afterwards
(`33244b02e` on 2026-09-24, `9dde12280` on 2026-09-28, and the Saturday build `bcf88383d`), so those events cannot be stale builds: the fix guarded a different call site. The failing URL
`https://api.startupcollective.tallysolutions.com/api/v2/events/<uuid>/upload-file` is `GlobalService.uploadFile()`, called from the event registration page `/events/register/<uuid>`.

## Problem
`Uncaught (in promise): ... status 400 ... /api/v2/events/<uuid>/upload-file ... HttpErrorResponse`.

## Root cause
`AttendInformationComponent.fileSubmit()` (`src/app/shared/common-components/attend-information/attend-information.component.ts`) is an `async` handler fed by `app-file-selector`. It adds the picked files to
`selectedImage[questionId]`, calls `onValidationCheck()` (which clears the question's `required` validator because files are present) and then `await`s `uploadAttachment()` with no try/catch. A failed upload
(`GlobalService.uploadFile()` toasts and rethrows) therefore rejects the handler: an uncaught promise rejection. It also leaves the failed file selected and the validator cleared, so the question looks
answered and the registration can be submitted without the file.

## Fix
`fileSubmit()` wraps the upload in try/catch. On failure it logs (the user was already toasted), removes the just-picked files from `selectedImage[questionId]` and re-runs `onValidationCheck()`, which restores
the `required` validator so the user has to pick the file again. A successful upload is unchanged.

## Not changed
`GlobalService.uploadFile()` builds the URL with a trailing space (`'/upload-file '`); the browser's URL parser strips it, so it works. `uploadAttachment()` re-uploads every file already in the list on each pick
(existing behaviour, a separate inefficiency).

## Contract impact
None. No API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` and `ngc` exit 0. No automated test added (no spec exists for this component). Not exercised in a browser.

## Commit
sc-saas-frontend `ca90d637f` on `ai_native_setup_aman` (shared module spec updated in the same commit). Not deployed.
