---
id: SAN-2027
title: "syncBroadcastEmailStats SES throttling still firing: infra quota decision still pending"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2027
sentry: [SC-SAAS-BACKEND-5R]
repos: [backend]
related: [SAN-1663, SAN-1875, SAN-1904, SAN-1979]
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2027: 5R is the known SES quota limit

## Investigation
* 12 events, `level: warning`:
  * production hosts `-151/-175/-176/-177/-180/-217`, the latest at 2026-10-22 14:59;
  * 2 from local developer containers (10-17 and 10-23). The event from "2 days ago" is a local one.
* The message is the SAN-1663 escalation (`THROTTLE_WARN_EVERY_RUNS`, `sync-broadcast-email-stats.service.ts` ~183-193). It fires only once every 6 consecutive throttled runs per tenant, so it is already deduplicated, and `warning` is the right level.
* `origin/main` has the same throttling logic: the file differs by +24/-4 lines, none of them in the throttle path.

## Root cause
Every tenant shares the account's SES `GetMessageInsights` quota. This is an ops/infra limit, not a code defect.

## Fix
None in code.

## Blast radius / existing-flow impact
None.

## Verification
Read-only.

## Decisions pending (infra, carried from SAN-1979)
Choose one:
* (a) raise the SES `GetMessageInsights` quota in ap-south-1;
* (b) stagger the `cron_jobs` minute per tenant;
* (c) reduce batch sizes.

In Sentry, archive the issue "until escalating" rather than resolving it.
