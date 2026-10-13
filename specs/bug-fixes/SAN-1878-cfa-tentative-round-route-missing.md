# SAN-1878 — CFA "Tentative" always fails (backend has no tentative-round route)

Linear: https://linear.app/sanchiconnect/issue/SAN-1878 · Repo: `sc-saas-backend` · Priority: Medium · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
Admin's `tentativeApplication()` (`sc-saas-admin/modules/application_management/submission-application-management.php:180`) POSTs to
`v1/application-programs-management/{programUUID}/tentative-round/{adminToken}`. The CFA controller had no such route, so it 404'd.
The legacy (`program-management`) and VS (`vs-programs-management`) controllers already had it. Tracked as gap A-10 in the module spec and in SAN-1471.

## Evidence
- `application-program.controller.ts` had `update-round`, `reject-round`, etc., but no `tentative-round`.
- A `TentativeRoundDto` (`dto/application-tantative-round.dto.ts`, extends `ApplicationRejectRoundDto`) already existed, unused by this controller.
- The ticket said legacy tentative does not notify. Current code does (SAN-1471, `ProgramsService.tentativeRound`), and the SAN-1471 spec's A-10 was waiting on this route.

## Root cause
Route + service method never implemented for the CFA module.

## Fix (`sc-saas-backend` only)
- `application-program.controller.ts`: `POST /:programUUID/tentative-round/:adminMd5` → `applicationProgramService.tentativeRound()`. Same `:adminMd5` auth model as `update-round` / `reject-round` (token validated in the service via `checkIsValidAdmin`).
- `application-program.service.ts`: `tentativeRound()` — validates admin and program; per application: freeze guard on the current round (403), sets `applicationStatus='tentative'`, `isRejected=false`, `rejectedOn=null`, `adminId`; no round change, no email; in-app notification via `notifyApplicationStatus` (`ApplicationStatusCopies.tentative`).
- `module.spec.md`: A-10 line updated.
- Tests: 3 cases added to `notifications/application-status-notifications.spec.ts` (sets tentative + notifies; frozen round → throws, nothing written; failed update → throws, no notification).

## Decisions
- Notification: **sent** (in-app), consistent with legacy/VS/mentor and the SAN-1471 spec. Not confirmed by the product owner — easy to remove if they disagree.
- Admin panel intentionally **unchanged** (user instruction). The CFA admin page has handlers (`.tentativeApplication`, `#bulkTentativeBtn`, `.bulkHold`) but no Hold/Tentative button in its HTML, so the route is only reachable via API / e2e until an admin issue adds the button.

## Verification
- `tsc --noEmit`: clean.
- `jest src/modules/notifications/application-status-notifications.spec.ts`: 60/60 pass.
- `eslint` on the 3 touched TS files: 0 errors (warnings are pre-existing unused-var ones); `prettier --check`: clean.
- NOT done: live call against a running backend / DB, admin UI check, e2e run, formal `/audit-contract` (additive route only; no existing route/DTO changed).

## Follow-ups
- Admin issue: add Hold/Tentative button to the CFA Kanban page (separate repo → separate issue).
- SAN-1882 / `sc-saas-e2e`: remove the tentative "known-failing" mark once verified on QA.

## Commit
Not committed yet (awaiting user go-ahead). Push branch: `ai_native_setup_sandeep`.
