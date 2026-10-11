---
id: SAN-1041
title: "metrics/all 403 -> navigate('/') loop for unapproved startups (logged as Jobs(...))"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1041
sentry: [SC-SAAS-FRONTEND-G3]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1041: metrics/all 403 -> navigate('/') loop for unapproved startups (logged as Jobs(...))

## Classification
CODE_ERROR

## Root cause
The Sentry breadcrumbs show about 40 cycles in roughly 1s of `GET metrics/all 403` -> `Jobs( Startup profile is not approved )` -> navigation -> `GET metrics/all`. The global interceptor toasts and calls `router.navigate(['/'])` on every 403, and the sidebar's background `fetchMatrics()` re-runs on the resulting store emission, so it loops. `getMetrics()` also used the copy-pasted `Jobs(` label.

## Fix
Added an `HttpContextToken` `SKIP_FORBIDDEN_REDIRECT` (new `core/http-interceptor/http-context-tokens.ts`). The interceptor rethrows a 403 without toasting or redirecting when the token is set. `getMetrics(background = true)` sets it and also skips its own toast/log on 403. The sidebar badge now uses `getMetrics(true)`. The log label is fixed to `metrics(`. Foreground callers (growth-matrics pages) are unchanged. SAN-1018's error callbacks stay in place.

## Files changed
- `src/app/core/http-interceptor/http-context-tokens.ts (new)`
- `src/app/core/http-interceptor/add-token-header.http-request-interceptor.ts`
- `src/app/core/service/metrics.service.ts`
- `src/app/layouts/public/public-layout-sidebar/public-layout-sidebar.component.ts`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
`SKIP_FORBIDDEN_REDIRECT` defaults to `false`, so every other request keeps the 401/403 interceptor behaviour. `getMetrics()` defaults to `background = false`, so the growth-matrics and print pages behave as before (toast + redirect on 403). Only the sidebar's background badge fetch no longer toasts or redirects on 403. The badge simply doesn't show, which is correct for an unapproved startup.

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
