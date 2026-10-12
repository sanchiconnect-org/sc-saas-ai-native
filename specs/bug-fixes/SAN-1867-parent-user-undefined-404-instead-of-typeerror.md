# SAN-1867 — profile with no parent user row crashes with a TypeError (500) instead of a 404

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1867 (Sentry SC-SAAS-BACKEND-52, -53, -54, -55, -56)
- **Repo:** sc-saas-backend · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (unguarded undefined) / possible data gap

## Evidence
BACKEND-52..56 are `Cannot read properties of undefined (reading 'id')` raised right after `userRepository.getParentUserByProfileType(...)`. BACKEND-52 had 12 production events (plus 15 local); the others were local only.
Failing methods: `ConnectionsService` list/requests methods, `MeetingsService.getPendingAcceptanceMeetingsList`, `DashboardService.getDashboardUser`. The caller got a 500 (FRONTEND-Y saw the 500 on `GET /connections`).

## Root cause (observed vs inferred)
- **Observed:** `getParentUserByProfileType` returns `undefined` and the callers read `.id` without a check.
- **Inferred:** the profile has no parent user row. **Why the row is missing was not investigated.**

## Fix
Early `throw new NotFoundException(ApiErrors.USER_NOT_FOUND)` when the result is undefined, at the failing line:
- `connections.service`: acceptConnection, rejectConnection, getTeamMembersWithUserId, getConnections, getConnectionsBasicInfo, getConnectionsRequestByType, blockConnection, getConnectionsListBasic, getConnectionParentUserByGroupUUID.
- `dashboard.service`: getDashboardUser. `meetings.service`: getMeetingsList, getPendingAcceptanceMeetingsList, acceptMeeting, rejectMeeting, getMeeting. `corporate.service`: the dashboard method.

## Not fixed
Same pattern, untriaged (some may be write or cron paths, where a 404 may be the wrong answer): connections.service ~261/~363 (createGroupChatForConnection), investor.service:653, individual.service:338, mentor.service:431/818/932, startup.service:1541, notifications.service:226, service-provider.service:399, program-office-members.service:351, growth-metrics-reminder.service:158, and admin-actions, user, vs-programs, form-management, program-management, public-portal, operational-cost-reimbursement.
The cause of the missing parent rows is also not fixed.

## Contract impact
Behaviour change: those routes now answer **404** (`USER_NOT_FOUND`) instead of 500 when the parent user is missing. Routes, DTOs, flags and auth are unchanged. Frontend callers that treated 500 specially were not checked; tenant scoping untouched.

## Verification
`tsc` clean. No automated test added (guardian skill blocked). Not run against a database or with an orphaned profile.

## Commit
sc-saas-backend `3473722f` (with SAN-1868) on `ai_native_setup_aman`. Pushed, not deployed.

## Sentry
BACKEND-52..56 left to the sweep policy; reopen only on `environment:production` events from a build containing `3473722f`. A new 404 from these routes is expected for orphaned profiles.
