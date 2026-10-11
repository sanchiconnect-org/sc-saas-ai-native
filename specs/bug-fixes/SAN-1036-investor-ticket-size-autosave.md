---
id: SAN-1036
title: "Investor ticket size Max <= Min sent by auto-save; mislabeled loginFault"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1036
sentry: [SC-SAAS-FRONTEND-EB (+D6, EZ)]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1036: Investor ticket size Max <= Min sent by auto-save; mislabeled loginFault

## Classification
CODE_ERROR

## Root cause
`isTicketSizeValid` gated Next Step but not `persistInvestmentInfo()`. The 20s auto-save tick kept sending Max <= Min, the backend rejected it, and the user got a generic error toast every tick. Both investment-info and representative-info saves logged as `loginFault(...)`.

## Fix
`persistInvestmentInfo()` now returns early while the ticket size is invalid, with an error toast only when the save isn't silent. The form stays dirty, so the next tick saves once the values are fixed. Relabelled the logs to `investmentInfoFault` / `representativeInfoFault`. The org-details `loginFault` is left alone because it belongs to SAN-1019. D6 ("Preference type not found") and EZ ("Industry domain id:48 does not exist") are stale master-data ids rejected by the backend, so they're a data issue and are only relabelled.

## Files changed
- `src/app/modules/investors/pages/edit/investments-details/investments-details.component.ts`
- `src/app/core/service/investors.service.ts`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
Manual Next Step and Save were already disabled via `saveButtonDisabled`, which includes `!isTicketSizeValid`, so they're unchanged. Only the silent auto-save now skips a payload the backend would reject anyway. The auto-save in-flight counter is incremented and decremented synchronously in try/finally inside `AutoSaveHandle.attemptSave`, so an early return can't leave it stuck. The form stays dirty, so the next tick saves once the values are corrected. The `loginFault` label changes only affect Sentry grouping.

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
