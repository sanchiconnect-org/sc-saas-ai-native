---
id: SAN-1875
title: "SES throttle-pause warning still firing (SC-SAAS-BACKEND-4X) — deploy lag"
type: bug-fix
status: blocked
linear: https://linear.app/sanchiconnect/issue/SAN-1875
sentry: [SC-SAAS-BACKEND-4X]
repos: [backend]
commit: none — no code defect, the SAN-1663 fix is awaiting deploy
created: 2026-10-12
updated: 2026-10-12
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
