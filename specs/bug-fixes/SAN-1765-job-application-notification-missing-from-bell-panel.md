# SAN-1765 / SAN-1766 — Job application notification missing from bell panel

- **Linear:** SAN-1765 (Repo: Backend), SAN-1766 (Repo: Frontend) — Bug, Medium, assignee Mahima Sharma
- **Classification:** CODE_ERROR

## Problem
When someone applies to a job, the poster's bell count goes up, but the bell panel ("All" → Today) shows nothing for it. The newest item in the panel is still an older connection request.

## Evidence / root cause
- The bell number is `counters.bell`, a sum of section counters that includes unviewed job applications (`jobs.total`).
- The panel list is `GET notifications`, which reads rows from the `notifications` table.
- `JobService.applyForJob` only saved the application and called `refreshJobTeamCounters` (socket `fetch-count`). It never wrote a `notifications` row, and `NotificationType` had no job-application value. So the count went up with nothing behind it in the list.
- The Today/Earlier grouping (`centreFieldsFor`, IST calendar day) works correctly. It had no row to group.

## Fix
Backend (`sc-saas-backend`):
- `src/core/constants/enum.ts` — `NotificationType.JOB_APPLICATION = 'job_application'`, mapped to `InAppCategory.JOB_APPLICATIONS` in `NOTIFICATION_TYPE_IN_APP_CATEGORY` (the in-app mute setting applies).
- `src/modules/notifications/types/notification.type.ts` — `JobApplicationNotificationType`.
- `src/modules/notifications/repositories/notifications.repository.ts` — `addJobApplicationNotifications()`: one row per recipient, category `new`, `source_type`/`source_id` = the application.
- `src/modules/job/job.service.ts` — `applyForJob` writes rows for the poster and their team (same people whose Jobs badge moves, excluding the applicant), url `/jobs/<job uuid>/details`. It writes these *before* the `fetch-count` push, only with the notification centre on, and in a try/catch so a failure never breaks the application.
- `src/modules/job/job.module.ts` — provide `NotificationsRepository`.
- Schema: `synchronize: true` adds the new enum value to `notifications.type` on boot. No manual migration is needed.

Frontend (`sc-saas-frontend`):
- `src/app/modules/notifications/notifications.enum.ts` — `JobApplication = "job_application"`.
- `src/app/modules/notifications/pages/notifications/notifications.component.ts` — icon + "View applications" CTA. The bell panel already navigates to the row's relative `url`.

## Verification
- Backend: `tsc --noEmit` clean apart from one existing unrelated error (`@aws-sdk/client-sesv2` missing in `cron/sync-broadcast-email-stats.service.ts`). ESLint: no errors on the touched files. Jest `src/modules/notifications` + `src/modules/job`: 7 suites, 104 tests pass.
- Frontend: `tsc --noEmit -p tsconfig.app.json` clean, ESLint clean on the touched files.
- No regression test added yet (proposed, waiting for go-ahead). Not exercised end-to-end against a running backend.
- Existing applications made before the fix get no row; only new applications appear in the panel.

## Commit
_pending — Mahima commits_
