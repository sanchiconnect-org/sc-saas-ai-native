# SAN-1886 — CFA apply API accepts applications to closed / past-deadline programs

Linear: https://linear.app/sanchiconnect/issue/SAN-1886 · Repo: `sc-saas-backend` · Priority: High · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
`POST /api/v1/application-programs-management/:programUUID/:submissionId/apply` created an application even when the CFA program had applications closed, was closed, or was past its deadline. Only the PWA (`program-public-apply.component.ts` `applicationClosed`) enforced it.

## Evidence / ticket claims checked
- `applyForProgram()` had no check on `applicationsClosed`, `programClosed` or `applicationClosedDate` (confirmed).
- **Unpublished (`status=0`) was already handled**: `getSingleProgramByUUID()` filters `status: true`, so it answers `PROGRAM_NOT_FOUND`. Ticket bullet was wrong for this path.
- `dead_line` belongs to challenges, not CFA programs; CFA uses `applicationClosedDate`.
- No admin path calls `/apply` (the admin backfill script writes rows directly), so import/move are unaffected.

## Fix (`sc-saas-backend` only)
- `application-program.service.ts`: `isProgramClosedForApplications()` mirrors the PWA rule: `testModeEnabled` bypasses; closed when `applicationsClosed` or `programClosed`, or `applicationClosedDate <= now - 1 day` (same one-day grace as the PWA; absolute instants, no timezone math). `applyForProgram()` throws `ForbiddenException(PROGRAM_APPLICATIONS_CLOSED)` only when a NEW round row would be created (`!checkSubmission`).
- `api-error-message.ts`: `PROGRAM_APPLICATIONS_CLOSED = 'Applications for this program are closed.'`.
- `module.spec.md`: rule + known limit documented.
- `application-program.service.spec.ts`: 8 new cases.

## Decisions (not confirmed by product)
- Existing round rows are never gated: re-apply after rejection (SAN-352) and an in-progress retry keep working even after the deadline. If product wants the deadline to apply to re-apply too, it is a one-line change.
- 403, like the other gates in this method.

## Verification
- `jest application-program.service.spec.ts`: 45/45 pass (37 existing + 8 new). With the gate disabled, the 3 reject cases fail and the 5 allow cases pass, so the tests catch the bug.
- `eslint` on the 3 touched TS files: 0 errors (10 pre-existing warnings); `prettier --check`: clean.
- `tsc --noEmit`: only error is `src/modules/notifications/push.service.ts` (`web-push` listed in package.json but not installed in local node_modules; environment, unrelated).
- NOT done: live call against a running backend, e2e (FT-006 P4 "closed program rejects apply" test lives in `sc-saas-e2e`, not in this workspace).

## Known limit (not fixed here, out of this ticket)
The PWA saves the form submission through a separate endpoint BEFORE calling `/apply`. A refused apply therefore leaves a saved `forms_submissions` row with no round row (the SAN-336 orphan shape: invisible in the admin Kanban, still counted in stats/exports). A late direct-API caller can still save a submission; closing that needs a deadline check on the submission-save path. Also, an honest applicant submitting just after the deadline gets an error toast while their form data stays saved.

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
