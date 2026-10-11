---
id: SAN-988
title: "Every cron job fire-and-forgets its promise — unhandled rejections lose all stack context"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-988
sentry: [SC-SAAS-BACKEND-X]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-988 — cron jobs fire-and-forget, losing all error context

## Root cause
User asked to verify whether `SC-SAAS-BACKEND-X` (`AxiosError: Request failed with status code 500`, `mechanism: onunhandledrejection`, no stacktrace) was local-dev noise like SAN-895's cluster. Checked via `search_events`: all 10 most recent occurrences span 7 distinct production ECS instances over 3 weeks, all `environment: production` — genuinely live.

Traced the mechanism: `cron.service.ts`'s `setCronJobs()` registers all 33 scheduled jobs using the raw `cron` package's `CronJob` class with bare synchronous callbacks:
```ts
() => {
  this.someService.someAsyncMethod();
}
```
Not `@Cron()` — a plain function that invokes an async method and discards its returned promise. No `await`, `.then()`, or `.catch()` anywhere. Any rejection not caught by the target method's own internal try/catch becomes a fully unhandled promise rejection with zero first-party stack frame, exactly matching this issue's signature. Confirmed separately that every axios call in the backend already uses `await` (25 files checked) — ruling out a simple missing-await bug at the call site itself; the gap is one level up, at the fire-and-forget scheduling layer.

While reading through all 33 case blocks, found a second, unrelated bug: `COMMUNITY_WALL_POSTS_WEEKLY_REMINDER`'s callback read `this.communityWallPostReminderService.sendWeeklyCommunityPostsEmail;` — a property reference, missing `()`. This cron has been firing on schedule but never actually invoking the reminder method.

## Fix
- Added `runCronJob(cronJobName, work)` to `CronService` — calls `work().catch((error) => this.logger.error(...))`, attributing any failure to the specific cron job name with the real error message and stack.
- Wired all 33 `case` blocks in `setCronJobs()` through it. Verified exact 1:1 coverage (`grep -c "case CronJobName\."` = 33, `grep -c "this.runCronJob("` = 33).
- Fixed the missing `()` on `COMMUNITY_WALL_POSTS_WEEKLY_REMINDER` so it actually runs.

## Blast radius
Single file, `src/modules/cron/cron.service.ts`. No behavior change to any cron's actual work — every job still does exactly what it did before. Only the community-wall reminder fix is a real behavior change (it will now actually fire weekly, which it never did).

## Verification
`tsc --noEmit` clean.

## Rollout
This does not retroactively explain which axios call produced SC-SAAS-BACKEND-X's 47 historical events. Left that Sentry issue open (not resolved) — the fix only makes the *next* cron-triggered unhandled rejection (this one or any other) attributable to a specific job with a real stack trace, closing the diagnostic gap rather than the underlying failure.

## Open questions
Once deployed, the next occurrence of a cron-triggered rejection will identify the exact job and error — follow up on that specific call site at that point.
