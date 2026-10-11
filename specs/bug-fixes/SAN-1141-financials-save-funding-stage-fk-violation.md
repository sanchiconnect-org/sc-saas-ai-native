---
id: SAN-1141
title: FINANCIALS save error (500) — funding_stage_id truthy-check gap lets 0 skip validation and crash the FK write
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1141/sentry-sc-saas-frontend-d5-financials-save-error-regressed-post-fix-98
repos: [backend]
created: 2026-09-29
updated: 2026-09-29
---

# SAN-1141 — editFinancials() truthy check on fundingStageId lets 0 through to the DB write

## Request

Sentry triage follow-up (`/bug-fix`, Production Defects project): `SC-SAAS-FRONTEND-D5` ("FINANCIALS save error (Internal Server Error)") regressed past its earlier "Done" ticket (SAN-926) — 36→98 events, 8→15 users, substatus `regressed`, still firing same-day. SAN-926 never actually root-caused the backend 500; this ticket does.

## Investigation

Cross-checked `sc-saas-backend`'s own Sentry project for the tenant/error family and found three recent `QueryFailedError` FK-violation groups on `startup_financials.funding_stage_id` (`SC-SAAS-BACKEND-4C/4D/4E`, one of them on the exact matching tenant DB `sc_saas_firstwings`). Two related, already-"Done" tickets existed for FK violations on this same column (SAN-892: CSV import; SAN-1050: stakeholder-account-creation) — both in `sc-saas-admin`, both admin/background write paths, neither matching the end-user "Save Financial Details" button flow this ticket is about.

Traced that actual flow end to end in `sc-saas-backend`:
- `StartupService.editFinancials()` (`src/modules/startup/startup.service.ts:1057-1115`) — validation gate.
- `FundingStagesRepository.checkFundingStageIdExist()` (`src/modules/global/funding_stages/funding_stages.repository.ts:37-44`) — looks up `{ isActive: true, id }`, throws `NotFoundException` if missing.
- `StartupFinancialsRepository.updateFinancialsByStartupId()` (`src/modules/startup/repositories/startup-financials.repository.ts:43-120`) — write gate.

Ruled out the SAN-892 "stale full-entity resave" hypothesis for this path: `updateFinancialsByStartupId()` does a genuine partial-column `UPDATE` via `AuditedUpdateService.update()` → TypeORM `repo.update(criteria, patch)`, gated `if (fundingStageId !== undefined)` — it never re-persists a column the caller didn't send. Also confirmed `funding_stages` rows are never updated/deleted/deactivated anywhere in this backend (read-only + one seed insert), so a row can't go stale out from under a financials row via this repo.

## Root cause

`startup.service.ts:1074` (before fix): `if (startupFinancialsDto.fundingStageId) { await checkFundingStageIdExist(...) }` — a **truthy** check. `fundingStageId === 0` is falsy, so validation is skipped entirely for that value. The write gate one layer down is `!== undefined`, which *does* include `0`. Since `0` is never a valid `funding_stages.id` (seed ids start at 1, `funding_stages.repository.ts:46-51`), a request carrying `fundingStageId: 0` sails past validation and crashes the database write on the foreign-key constraint — surfacing to the end user as an uncaught 500, exactly matching the reported symptom. Plausible trigger: an Angular `<select>` for funding stage emitting `0` as its unselected/placeholder sentinel value when a user saves other financial fields without touching that particular dropdown.

## Fix

`src/modules/startup/startup.service.ts:1074` — changed the condition to `fundingStageId !== undefined && fundingStageId !== null`, matching the write gate's own condition exactly. `fundingStageId: 0` now correctly reaches `checkFundingStageIdExist(0)`, which throws a clean `404 Funding stage id:0 does not exist` instead of letting an uncaught FK violation reach the database and become a 500. No behavior change for any real (truthy) funding stage id — the fix only changes what happens for `0`/`null`/(unreachable, DTO-validated-out) non-numeric values.

## Design decisions taken (not asked, judgment calls)

- **Fixed the validation gate, not the write gate.** Matching the write gate's condition at the validation site means invalid input is rejected with a clear 404 before any database write is attempted — the correct place to reject bad input, rather than adding a second guard deeper in the repository that would just convert one kind of silent failure into another.
- **Did not touch the DTO's `@IsOptional()`/`@IsNumber()` decorators** (`startup-financials.dto.ts:20-25`) to also reject `0` at the transport layer. `0` is a syntactically valid number and `@IsOptional()` only skips `undefined`/`null` by design — changing DTO-level validation semantics for one field has wider blast radius (Swagger docs, any other caller of this DTO) than fixing the actual service-layer logic bug. Flagged as a possible defense-in-depth follow-up, not done here.
- **Did not investigate the Angular frontend's funding-stage `<select>`** to confirm it actually emits `0` for an unselected state — out of scope for a backend-only fix, and the backend fix is correct regardless of what triggers `fundingStageId: 0` (any other future caller sending the same value is now handled the same safe way).

## Verified

- `npx tsc --noEmit` — clean.
- `npx eslint src/modules/startup/startup.service.ts` — 7 pre-existing unused-import/var warnings (unrelated to this change, present before it), 0 errors.
- `git diff --stat` — 1 file, 16 lines (14 insertions, 2 deletions).
- Read `checkFundingStageIdExist()`'s exact implementation directly (not assumed) to confirm it actually throws for `id: 0` rather than silently passing.

## Not verified — genuinely outstanding

No live/integration test — this repo's `npm test` (Jest) exists but no test was added for this specific case; per the standing workspace process, stating that explicitly rather than silently skipping it. Did not confirm what the Angular financial-details form actually sends for an untouched funding-stage control (would require a `sc-saas-frontend` investigation, out of scope here).

## Rollout

Not committed, not pushed — per standing instruction, awaiting review.

## Separate finding, flagged not fixed here

While cross-checking backend Sentry, found `SAN-1050` (a different, already-"Done" Linear ticket for a related `funding_stage_id` FK bug in `sc-saas-admin`'s stakeholder-account-creation flow) documents a fix that was **never actually committed** — its own spec doc (`specs/bug-fixes/SAN-892-followup-stakeholder-creation-funding-stage-fk.md`) records `commit: sc-saas-admin@<pending, branch ai_native_setup_aman>`, and the live code at `sc-saas-admin/includes/stakeholder_account_creation_funcs.php:1575` still has the original unguarded `$funding_stage_id = $recordData["funding_stage_id"];` with no re-verification. Different repo, different write path — out of scope for this ticket, flagged separately rather than silently fixed here.

## Open questions

None blocking.
