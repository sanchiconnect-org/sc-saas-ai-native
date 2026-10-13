---
id: SAN-1895
title: "Meetings list / dashboards 500 when a meeting's creator account is soft-deleted (SC-SAAS-BACKEND-5Q)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1895
sentry: [SC-SAAS-BACKEND-5Q]
repos: [backend]
related: [SAN-1867]
commit: sc-saas-backend@60a20f65 (branch ai_native_setup_vishali, pushed) — meetings.repository.ts + new meetings.repository.spec.ts + meetings module.spec.md
created: 2026-10-13
updated: 2026-10-13
---

# SAN-1895: meeting with a soft-deleted creator

## Investigation
* **Sentry:** `TypeError: Cannot read properties of null (reading 'id')` at `MeetingsRepository.getMeetings` (`userIds.includes(meeting.user.id)`).
  * Production, 1 event, 2026-10-12 12:48 UTC.
  * It happened on a build started 2026-10-11 15:43, so this is **not** deploy lag.
  * Before this, it had no Linear ticket.
* **Root cause:** `users` are soft-deletable (`AbstractEntity.deletedAt`), and `leftJoinAndSelect('meetings.user', 'user')` excludes soft-deleted rows. So when the account that **created** a meeting is deleted, `meeting.user === null`. The other participant still matches the query via `other_user_id IN (userIds)`.
  * The post-processing loop dereferences `meeting.user` unguarded: `.id`, `.accountType`, the connection lookup, and `meetings[key].user['companyName']`.
  * The first null throws, and the **whole response 500s**.
* **Blast radius is wider than the Sentry event suggests.** `getMeetings` feeds the meetings page **and every role's dashboard**: startup, investor, mentor, corporate, individual, program-office, service-provider, plus `dashboard.service`. One orphaned meeting therefore 500s that user's dashboard.
* The mirror case, a deleted *other* participant (`otherUserId = null`), was already tolerated: `?.id`, and `receiver` is guarded.
* `getMeetingByUUID` has the same unguarded `meeting.user.id`. Opening an old link or notification for such a meeting would 500.
* `getInterviewMeeting`'s loop does not dereference `meeting.user`, so it is safe. `updateZohoRecordId` is a separate Zoho sync path and was left alone.

## Fix (sc-saas-backend@60a20f65)
`src/modules/meetings/repositories/meetings.repository.ts`:
* **`getMeetings`:** filter out meetings with `user == null` right after `getMany()`. Each one is logged with `logger.log({ SKIPPED_MEETING_WITHOUT_CREATOR: uuid })`. This is `log`, not `warn`, so it doesn't reach Sentry. Every other meeting goes through the loop unchanged.
* **`getMeetingByUUID`:** `if (!meeting || !meeting.user) throw NotFoundException(MEETING_NOT_FOUND)`. This uses the existing error, the same one returned for a missing meeting, and is consistent with the list leaving the meeting out.

### Why skip instead of returning the meeting with `user: null`
The frontend dereferences `meeting.user` unguarded, for example `meeting-details-modal.component.html`: `modalData.event.user.name` / `.companyName`. Returning a null user would just move the crash to the browser. The orphaned meeting isn't actionable either, because its creator no longer exists.

**Before the fix**, the whole list or dashboard failed. **After**, everything is shown except that one meeting. This is a strict improvement, with no change for normal meetings.

**Known edge:** dashboard callers that pass a `limit` may get one fewer item when an orphan falls inside the limit. That's acceptable compared with a 500.

## Contract checks
* **API contract (#2):** the response shape of each meeting is unchanged. Only orphaned items are omitted, and the details endpoint returns the existing `MEETING_NOT_FOUND`.
* **Flags, auth, tenant scoping:** no change.

## Verification
* **New spec `meetings.repository.spec.ts` (5 tests)** drives the real `getMeetings` loop and `getMeetingByUUID`. Only the query builder and the two static entity lookups are stubbed.
  * **With the fix: 5/5 pass.**
  * **Without the fix (repository reverted):** the two bug tests fail with the exact Sentry error `TypeError: Cannot read properties of null (reading 'id')`. The 3 behaviour-preservation tests pass both ways:
    * a normal meeting has the same `canPerformAction`, `canProposeTime`, `receiver`, `user`, `sharedMeetingNotes` and stripped `id`;
    * a deleted other participant still returns `receiver: null`;
    * the online-meetings flag off still returns `[]`.
* `tsc --noEmit` is clean, and ESLint shows 0 non-CRLF errors before and after.
* **Full backend jest suite:** 1,188 passed (up from 1,183, the 5 new tests). The same 4 suites fail as the pre-change baseline: 3 pre-existing failures, plus the unrelated `partner-domain-access` 1 ms timing flake.

## Closed 2026-10-13
* Pushed `60a20f65` to `ai_native_setup_vishali`. The meetings `module.spec.md` "Watch out for" section now documents the soft-deleted-creator guard.
* SAN-1895 is closed as Done.
* The commit message carries `Fixes SC-SAAS-BACKEND-5Q`, so Sentry may auto-resolve the group on merge, before the fix is deployed. If 5Q fires again after deploy, Sentry reopens it as regressed. In that case reopen SAN-1895.
* Deploy: merge to `main` and deploy the backend.
