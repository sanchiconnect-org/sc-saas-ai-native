---
id: SAN-1037
title: "\"Industry domain ids should not be empty\" on industry-technology (startup + partner)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1037
sentry: [SC-SAAS-FRONTEND-DN / -D4 / -D9]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1037: "Industry domain ids should not be empty" on industry-technology (startup + partner)

## Classification
ENV_ERROR (deploy lag), no code change

## Root cause
The latest DN event came from release `sc-saas-frontend@90bde7be0`, which does NOT contain the SAN-705 fix (commit `608d37732`, 2026-09-14). SAN-705 already blocks the silent auto-save when `isFormDataValid` is false, and `isFormDataValid` requires both industry and technology on the startup and partner pages. The current release `33244b02e` contains it.

## Fix
No code change. Watch DN/D4/D9 after the next deploy and resolve them in Sentry if they stay quiet.

## Files changed
- none

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
No code change.

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
