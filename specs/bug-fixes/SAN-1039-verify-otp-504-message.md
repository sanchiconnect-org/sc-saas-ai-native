---
id: SAN-1039
title: "verifyOTP 504 on program apply shows generic error"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1039
sentry: [SC-SAAS-FRONTEND-FB (+F8)]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1039: verifyOTP 504 on program apply shows generic error

## Classification
CODE_ERROR (UX), with an upstream ENV cause

## Root cause
On a 504 the body is an HTML page, so the toast fell back to "Error while verifying OTP". That reads like a wrong code. Both callers (program-public-apply-modal, program-check-status-modal) already stop the loader and keep the OTP input. The 504 itself comes from the backend/gateway.

## Fix
`SignUpService.verifyOTP` now shows "The server is taking too long to respond. Please try again in a moment." for status 0/5xx. F8 (founders/list 504) already has the fallback chain, and its 504 is an upstream/backend issue, so there's no frontend change for it.

## Files changed
- `src/app/core/service/sign-up.service.ts`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
Only the toast text for status 0/5xx changed. 4xx messages (invalid or expired OTP) are unchanged. Both callers already stop the loader and keep the OTP input.

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
