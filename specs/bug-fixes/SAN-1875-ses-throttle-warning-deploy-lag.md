---
id: SAN-1875
title: "SES throttle-pause warning still firing (SC-SAAS-BACKEND-4X) — deploy lag"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1875
sentry: [SC-SAAS-BACKEND-4X]
repos: [backend]
commit: none — no code defect. The SAN-1663 fix (sc-saas-backend@21a495f5, via main @ 6e7ca5c8) was deployed 2026-10-11 ~16:47 UTC and is verified in production
created: 2026-10-12
updated: 2026-10-13
---

# SAN-1875: 4X is a deploy lag

## Investigation
* The SAN-1663 fix (`21a495f5`, 2026-10-06) reached main only through PR #2027 (2026-10-11 20:47 IST).
* The latest event (2026-10-11 15:59 UTC) carries the pre-fix message text, with no `[consecutive throttled runs: N]` suffix.
* Its container started 2026-10-03, so the running build predates the fix.

## Action
1. Redeploy the backend from main.
2. Confirm the new wording appears, with at most one event per 6 consecutive throttled runs.
3. Resolve SC-SAAS-BACKEND-4X.

If the escalation warning persists after that, the SES GetMessageInsights quota is too low; that's an AWS request, not code.

## Verified 2026-10-13: deployed and quiet
* **Redeploy observed.** Between 2026-10-11 16:46 and 16:49 UTC, about 10 production hosts each emitted the process-start AWS-SDK notices (SC-SAAS-BACKEND-1/2). That is a fleet-wide restart about 90 minutes after PR #2027 (`6e7ca5c8`, which includes `21a495f5`) merged at 15:17 UTC.
* **4X stopped at the restart.** Daily counts were steady at 54 to 96 events from 10-02 to 10-10. On 10-11 there were 34, the last at 15:59 UTC, before the restart. There have been 0 on 10-12 and 0 so far on 10-13. Other backend issues kept reporting through the same window (3M, 5Q, 5J, 5N), so Sentry ingestion is working.
* **No escalation.** No `still paused after N consecutive runs` issue exists. SES throttling has not persisted for 6 runs on the new build, so the AWS quota request mentioned under Action is not needed.
* **Caveat:** routine pauses now go to `logger.log()`, and Sentry Logs is not enabled for the backend, so the cron's normal runs can't be seen from Sentry. CloudWatch is the place to confirm them if needed.
* **Remaining step:** resolve SC-SAAS-BACKEND-4X in Sentry. Reopen SAN-1875 if the escalation warning appears.

## Old-flow safety check (2026-10-13)
* **The `21a495f5` diff touches only the final logging branch of `runSync()`.** It adds an in-memory `consecutiveThrottledRuns` counter and swaps `logger.warn` → `logger.log` for routine throttle pauses. These are unchanged:
  * the SES calls and the throttle backoff (`THROTTLE_BACKOFF_MS`)
  * the broadcast and other selection budgets
  * the rows updated and the bounce → promotional-email disable
  * the stop-early decision and the reentrancy guard
  * the public method signature, so `cron.service.ts` is unaffected
* **The credential-stop path still logs `error`, as before.** It now also resets the counter.
* The local file is identical to `origin/main`, and no later commits touch it.
* **`sync-broadcast-email-stats.service.spec.ts`: 18/18 pass.** This covers the unchanged selection order, budgets, backoff-then-continue, credential error, no-credentials skip, recipient-scoped insights and bounce handling, plus the 4 new throttle-count cases. To run it locally, the declared `@aws-sdk/client-sesv2@3.600.0` was installed with `--no-save`, because it was missing from local `node_modules` (pre-existing local gap). No tracked file changed.
