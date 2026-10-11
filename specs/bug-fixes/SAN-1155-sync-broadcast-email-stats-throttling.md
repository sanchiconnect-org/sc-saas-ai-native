---
id: SAN-1155-followup
title: "syncBroadcastEmailStats() stopped early on TooManyRequestsException — call rate too aggressive for GetMessageInsights quota"
type: bug-fix
status: done
linear: []
sentry: [SC-SAAS-BACKEND-4M, SC-SAAS-BACKEND-4J, SC-SAAS-BACKEND-4T, SC-SAAS-BACKEND-4P]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-10-01
updated: 2026-10-01
---

# SAN-1155 follow-up — SES GetMessageInsights throttling

## Root cause
`SyncBroadcastEmailStatsService` (SAN-1155/FA-009, a ~15-20min cron that backfills SES delivery/open/bounce stats) already has a sound design: it stops the whole run on the first throttling/credential error rather than retrying in a loop, logging a clear message and letting the next scheduled run pick up where it left off. Its per-call delay (`DELAY_BETWEEN_CALLS_MS = 200`, "~5 calls/second, to stay well under SES API rate limits") was an unverified assumption, though.

In production (confirmed via Sentry tags: `environment: production`, real AWS ECS ap-south-1 infra), this job hit `TooManyRequestsException` on effectively every run — 69 occurrences in 17 hours, actively firing. `GetMessageInsights` is a narrower SES v2 API with its own quota, separate from (and apparently lower than) general SES sending throughput; 5 calls/second exceeded it immediately on most runs.

Separately, 5 other new Sentry groups from the same message class (`AccessDeniedException` with a "SanchiSaasDevS3" IAM user, `InvalidSignatureException`, `UnrecognizedClientException`) were all confirmed `environment: local` (Docker containers, Intel desktop CPUs, not AWS ECS) — local dev-machine noise using local/dev-tier AWS credentials, unrelated to this production throttling issue.

## Fix
1. Raised `DELAY_BETWEEN_CALLS_MS` from 200 to 1000 (1 call/second) — a conservative backoff. The existing stop-on-throttle/retry-next-run design already tolerates a slower per-run budget fine; this doesn't change behavior, only how fast it paces itself.
2. Added a reentrancy guard (`isRunning` boolean): `cron.service.ts`'s `runCronJob()` fire-and-forgets with no concurrency protection. A run could now take longer at the slower rate; if the job's DB-configured interval is shorter than a run's worst case, overlapping runs could double up SES calls against the same quota. The guard logs and skips if a previous run is still in flight.

## Blast radius
Single file (`sync-broadcast-email-stats.service.ts`). No change to selection logic, batch sizes, or stats-writing behavior — only pacing and re-entrancy.

## Verification
`npx tsc --noEmit -p tsconfig.json` clean (after `npm install` to pull in `@aws-sdk/client-sesv2`, present in `package.json` but missing from `node_modules` locally). Existing `sync-broadcast-email-stats.service.spec.ts` (11 tests) passes unchanged.

## Rollout
Not resolving the Sentry issues outright — recommend watching SC-SAAS-BACKEND-4M/4J/4T/4P for a few days post-deploy. If throttling still recurs at 1 call/second, the account's actual `GetMessageInsights` quota is lower still and needs an AWS support quota-increase request, not a further code tweak.

## Open questions
Real AWS-side `GetMessageInsights` quota for this account was never confirmed (no AWS console/support access in this session) — 1 call/second is a reasonable conservative guess, not a verified number.
