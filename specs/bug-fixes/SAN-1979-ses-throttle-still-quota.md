---
id: SAN-1979
title: "syncBroadcastEmailStats still SES-throttled after SAN-1904: ops quota decision, no code defect (SC-SAAS-BACKEND-5R)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1979
sentry: [SC-SAAS-BACKEND-5R]
repos: [backend]
related: [SAN-1904, SAN-1663, SAN-1353, SAN-1155]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1979: SES GetMessageInsights throttling

## Investigation
* **Events:** 10 between 2026-10-13 and 2026-10-21, production, `level: warning`, `app_start_time` 2026-10-14.
* **The message is the SAN-1663 escalation.** It is emitted only after `THROTTLE_WARN_EVERY_RUNS` (6) consecutive hourly runs ended in `TooManyRequestsException`, which works out to about one event per day.
* **Mitigations already in** `src/modules/cron/sync-broadcast-email-stats.service.ts`:
  * a random start jitter of up to 10 min across tenants (`MAX_START_JITTER_MS`);
  * 1 call per second (`DELAY_BETWEEN_CALLS_MS`);
  * 3 retries with 2/4/8 s backoff (`THROTTLE_BACKOFF_MS`);
  * stop on throttle and resume on the next run;
  * a reentrancy guard;
  * per-run budgets of 300 broadcast and 900 other rows.
* **Production runs the same logic:** `origin/main` differs from the branch by 5 lines in that file.

## Root cause
Every tenant deployment shares one SES account, and that account's `GetMessageInsights` rate quota is lower than their combined call volume. The code already paces and backs off, so what is left is a capacity signal, not a defect.

## Fix
None in code. `[DESIGN DECISION PENDING]` (dev lead / infra, carried over from SAN-1904). The options:
* **(a)** Request a higher SES `GetMessageInsights` quota.
* **(b)** Stagger the cron minute per tenant (the `cron_jobs` row, data only) instead of running every tenant at :20.
* **(c)** Lower `BATCH_SIZE` / `OTHER_BATCH_SIZE`. Stats would then lag further on large tenants.

Options (a) and (b) need no code.

## Blast radius / existing-flow impact
None (no change). While throttled, broadcast and other email stats (delivery, open, bounce) update late, but they do update: each run resumes where the last one stopped.

## Verification
* Code read and branch diff.
* `npm run gates` for the slice: lint 0, test 0, test-floors 0, openapi-floors 0, build 1, unguarded-routes 0. The build failure is pre-existing and unrelated (see SAN-1976).

## Ops follow-ups
* An infra owner chooses (a), (b) or (c). (a) is a Service Quotas / AWS Support request for SES v2 `GetMessageInsights` in ap-south-1.
* Keep 5R open as the signal until the decision lands.

## Related
SAN-1904, SAN-1663, SAN-1353, SAN-1155.
