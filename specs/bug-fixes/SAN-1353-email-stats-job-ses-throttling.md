# SAN-1353 — Email stats job throttled by SES ("Rate exceeded")

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1353 · **Sentry:** SC-SAAS-BACKEND-4M
- **Repo:** sc-saas-backend · **Priority:** High · **Assignee:** Nirmal Singh · **Related:** SAN-1155, SAN-1156

## Problem
`syncBroadcastEmailStats() stopped early -- TooManyRequestsException: Rate exceeded`: 69 production events since
2026-09-30. `GetMessageInsights` is rate-limited per AWS account, and every tenant backend runs the hourly job at
:20 against the same account, at about 5 calls/s each. Runs stopped at the first throttle, so stats weren't
collected, and each stop was logged as an error to Sentry.

## Fix (`src/modules/cron/sync-broadcast-email-stats.service.ts`)
- About 1 call/s per tenant (`DELAY_BETWEEN_CALLS_MS` 200 → 1000) and a random 0–10 min start delay
  (`MAX_START_JITTER_MS`). A run's worst case is 10 min + 1,200 calls ≈ 30 min, which fits within the hour.
- `sendWithBackoff()`: a throttled call is retried after 2 s / 4 s / 8 s. If it is still throttled, the run pauses
  until the next hour with a **warning**. Credential errors (`AccessDenied`, `InvalidSignature`, …) still stop the
  run with an error.

## Verification
- `tsc` clean; eslint 0 errors on touched files.
- 14/14 tests pass. New: backoff then success continues the run; start delay < 10 min; credential error is still
  an error. Updated: a throttled row makes 4 calls (1 + 3 retries), then a warning instead of an error.

## Commit
sc-saas-backend `1bfd2e71` (on `ai_native_setup`)
