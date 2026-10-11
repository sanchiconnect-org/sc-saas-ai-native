---
id: SAN-1032
title: "events/attend 409 unhandled — Uncaught (in promise) on calendar/events"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1032
sentry: [SC-SAAS-FRONTEND-8]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1032: events/attend 409 unhandled — Uncaught (in promise) on calendar/events

## Classification
CODE_ERROR

## Root cause
`EventDetailsModalComponent.selectResponse()` awaited `bookEventSlot()` / `updateWebinarEventBooking()` via `.toPromise()` with no try/catch. A 409 from `POST v2/events/attend/:uuid` (already registered) became an unhandled promise rejection. The interceptor only handles 401/403, so the user saw nothing. (82 users, 129 events, regressed.)

## Fix
Wrapped both awaits in try/catch. On failure, the selected response is reset to the previous one and the backend message is shown as an error toast. 401/403 are skipped because the interceptor already toasts those. `attend-information.component.ts` was already wrapped in try/catch, so it's unchanged.

## Files changed
- `src/app/shared/common-components/event-details-modal/event-details-modal.component.ts`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
The success path (booking and updating a response) is unchanged. Only a rejected call is now caught. `attend-information.component.ts` already had its own try/catch and wasn't touched. 401/403 still go through the interceptor, with no double toast.

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
