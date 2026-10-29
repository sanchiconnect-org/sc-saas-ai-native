# SAN-2132 — Check Application Status says "Application not found" for a saved draft

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-2132
- **Repo:** sc-saas-frontend · **Priority:** High · **Assignee:** Vishali
- **Classification:** CODE_ERROR (regression from SAN-1959)
- **Commit:** `9004d88c1` on `ai_native_setup_vishali`
- **Status:** Done (2026-10-29)

## Problem
On a public call-for-applications page, an applicant who saved their application as a draft could not use **Check Application Status**. After the OTP the modal showed "Application not found for program", the email was not remembered, and the draft could not be reopened.

## Evidence
- `sc-saas-backend/src/modules/application-management/application-program.service.ts` `checkApplicationStatus(programUUID, email, showDetails=true)`: the form submission is found, but a draft has no `application_program_submission_rounds` row, so `getProgramBySubmissionIdAndProgramId` returns null and `/details` answers 200 with empty `data`. With no submission at all, `getSubmissionViaEmail` throws 404.
- `checkApplicationStatusMultiple` in the same service already treats "submission, no round row" as `isDraft: true`.
- Before SAN-1959 (`917bb1f8c`, 2026-10-23) the modal called the plain `check_application_status/:email` route, which returns `true` for any submission, drafts included.

## Root cause
Since SAN-1959 the modal reads only `/details` after the OTP and treated an empty answer as "not found".

## Fix
`src/app/modules/programs/program-public-apply/program-check-status-modal/program-check-status-modal.component.ts`: when `/details` is empty, confirm with the plain status route (same `ApplicantOrOwnerGuard` / `program-email` scope; the applicant token from the OTP is already stored). If the submission exists, store the applicant email and close; `handleCheckStatusButton` then opens the Application Form tab so the draft can be continued. Otherwise the 404 still shows "Application not found". Frontend only, no API contract change.

Regression test added in `program-check-status-modal.component.spec.ts` ("a saved draft (empty /details, submission exists) stores the applicant and closes"); the existing empty-answer test now also stubs the status route as not found.

## Verification
- `npx ng test --watch=false --browsers=ChromeHeadless --include=…/program-check-status-modal.component.spec.ts` → `TOTAL: 10 SUCCESS`
- `npx tsc --noEmit -p tsconfig.app.json` → exit 0
- Not run: full `npm run gates`; manual repro on a QA tenant (save a draft, clear localStorage, Check Status with the same email).
