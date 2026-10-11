---
id: SAN-1038
title: "Corporate engagement-details auto-save sends invalid payload"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1038
sentry: [SC-SAAS-FRONTEND-DA / -EC / -ED / -EE / -EF]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1038: Corporate engagement-details auto-save sends invalid payload

## Classification
CODE_ERROR

## Root cause
The auto-save `onSubmit(true)` ran purely off `isDirty`, so it sent empty `connectionRequirements` / `programName`. `totalSupported` was sent as a string (the `'0'` default or a patched value), which fails the backend `@IsInt`. The backend DTO (`engagement-information.dto.ts`, read-only check) requires connectionRequirements always, and programName plus an integer totalSupported when `hasInternalInnovationProgram` is true.

## Fix
`onSubmit()` returns early when `!isCurrentStepValid()` or when the resolved reasons list is empty (only "Others" ticked with blank text). An explicit save runs `checkInvalidFields()` instead. `totalSupported` is coerced with `Number()` when the program flag is set, and gets a `^[0-9]+$` pattern validator. The log is relabelled to `engagementInfoFault`.

## Files changed
- `src/app/modules/corporate/pages/edit/corporate-engagement/corporate-engagement.component.ts`
- `src/app/core/service/corporate.service.ts`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
Next Step is already blocked by `countInvalidFields > 0`, which is equivalent to the new `isCurrentStepValid()` guard, so it's unchanged. Only auto-save payloads that the backend DTO rejects are now skipped. `totalSupported` is converted with `Number()` only when the program flag is on, so valid numeric strings still save. Default `0` passes both `required` and `^[0-9]+$`. One new user-visible case: "Others" ticked with blank text now shows a toast instead of a backend 400 toast. `onSubmitProfile()` calls `flush()`, which behaves as before (the backend used to reject the same payload).

## 10-step process (SanchiConnect Developer Guide)
1. **Orient:** read the Sentry issue, event details and breadcrumbs. Done.
2. **/from-linear:** the Linear issue was created from Sentry and filed in the *Production Defects* project, assigned to Mahima. Done.
3. **Spec:** narrowly scoped, single-repo fix, so the lightweight `/bug-fix` path was used (this record) instead of a feature spec. Done.
4. **Design questions:** none pending. Data/ops follow-ups (if any) are listed above and not invented here.
5. **Contract check:** frontend-only. No controller, DTO, flag or tenant-scoped query changed, so `/audit-contract`, `/trace-flag` and `/check-isolation` don't apply. Backend code was only read, never edited.
6. **Tests first:** blocked workspace-wide (no guardian skill). As a substitute, `npx tsc -p tsconfig.app.json --noEmit` is clean and the `ng build --configuration development` AOT build exited 0. No automated regression test has been added; one is proposed and waiting for Mahima's go-ahead.
7. **Branch:** the working tree is `sc-saas-frontend` on `ai_native_setup_mahima`. No new branch was created. (CLAUDE.md names `ai_native_setup`; Mahima decides.)
8. **Implement:** done, see Fix.
9. **Verify:** existing-flow check above, bug-fix record written, Linear moved to In Review with a root-cause comment.
10. **Commit/push:** **not done, on purpose.** Waiting for Mahima's manual verification. Linear moves to Done only after that.
