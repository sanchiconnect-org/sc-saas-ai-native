---
id: SAN-1904
title: "syncBroadcastEmailStats persistent SES throttling — quota decision"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1904
sentry: [SC-SAAS-BACKEND-5R]
repos: [backend]
commit: none — no code defect, see Investigation
created: 2026-10-14
updated: 2026-10-14
---

## Investigation
The warning is the SAN-1663 escalation in `sync-broadcast-email-stats.service.ts`: it fires only after `THROTTLE_WARN_EVERY_RUNS` (6) consecutive throttled runs. The code behaves as designed. The signal is that the shared SES account's `GetMessageInsights` rate is too low for all tenant deployments on the same schedule.

## Fix
None in code yet. A dev lead / infra decision is pending: raise the SES quota, stagger the cron per tenant, or cut the per-run budget. `[DESIGN DECISION PENDING]`

## Related
SAN-1663, SAN-1875
