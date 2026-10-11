# SAN-1663 — SES stats cron: an expected throttle pause was a Sentry event on every run

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1663 (Sentry SC-SAAS-BACKEND-4X, 338 events in 4 days; also explains 4M / 4T)
- **Repo:** sc-saas-backend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** NOISE (expected-condition logging)

## Problem
`syncBroadcastEmailStats() paused until the next run -- SES is throttling (TooManyRequestsException: Rate exceeded)`, about 85 events a day in production.

## Root cause
`SyncBroadcastEmailStatsService.runSync()` (`src/modules/cron/sync-broadcast-email-stats.service.ts`) treats a `GetMessageInsights` throttle stop as expected under load and,
since SAN-1353, logs it with `logger.warn()`. `SentryLoggerService.warn()` (`src/core/logger/sentry-logger.service.ts`) forwards every warning to Sentry via
`captureMessage(..., 'warning')`, so the expected condition still produced an event on every throttled run from every tenant deployment sharing the AWS account. The older
`stopped early -- TooManyRequestsException` groups (4M, 4T) were the same condition before SAN-1353 re-classified it as a pause.

## Fix
- A throttled run logs the pause with `logger.log()` (not forwarded) and counts it (`consecutiveThrottledRuns`).
- Every 6th consecutive throttled run (`THROTTLE_WARN_EVERY_RUNS`; the job runs hourly) it logs a `logger.warn()` that names the likely quota problem, so a genuinely too-low
  `GetMessageInsights` quota still surfaces in Sentry.
- A run that does not end throttled resets the counter, including a credential stop, which stays a `logger.error`.
- In-memory per process (resets on restart).

## Not fixed
The underlying quota. If throttling really is permanent, the escalation warning and the SES account quota (shared by all tenant deployments) are what need attention. Each run makes
up to 300 + 900 `GetMessageInsights` calls at 1 call/second per tenant.

## Contract impact
None. Logging behaviour only; no API, flag, tenancy or auth change. The job still runs per tenant deployment against that tenant's own DB only.

## Verification
- `src/modules/cron/sync-broadcast-email-stats.service.spec.ts`: existing throttle test updated (a single throttled run no longer warns) and 4 new cases (quiet for runs 1-5, warn
  on the 6th, again on the 12th and not in between, reset by a non-throttled run, reset by a credential stop). Suite 18/18 passes.
- `tsc --noEmit` exits 0.

## Commit
sc-saas-backend `21a495f5` on `ai_native_setup_aman`. Not deployed.
