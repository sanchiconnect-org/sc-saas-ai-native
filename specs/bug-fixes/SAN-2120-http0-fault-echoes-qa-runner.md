---
id: SAN-2120
title: "Profile-completeness, getProfileDetails and metrics '( HTTP 0 )' fault echoes on thub dev"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-2120
sentry: [SC-SAAS-FRONTEND-J0, SC-SAAS-FRONTEND-J1, SC-SAAS-FRONTEND-HZ, SC-SAAS-FRONTEND-HY, SC-SAAS-FRONTEND-J2]
repos: [frontend]
related: [SAN-2032]
commit: none — decision pending
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2120: QA-runner network aborts reported as warnings

## Investigation
* These are console.warn fault echoes, 1 event each, dev. SAN-2032 (`865618f41`) created these `Label( HTTP 0 )` texts and left the `beforeSend` filter to the dev lead, so no suppression exists in `src/main.ts`.
* "Three profile types on one login page" is not a bug. `profile.service.ts:170-294` dispatches completeness only for the current user's `accountType`. All four `/auth/login` and apply-page events came from one Azure IP (20.231.101.37) within ~6 min on 10-26, with `environment=local` and slug `qa-cfa-run-20261026-…`. That points to the e2e runner logging in as different account types in turn, and HTTP 0 being requests aborted on navigation or teardown `[inferred]`.

## Decision pending
**Dev lead:** should a narrow `beforeSend` drop warn-level `…( HTTP 0 )` (and possibly `( HTTP 504 )`) echoes? The trade-off is a quieter Sentry against losing sight of a real CORS problem or outage that shows up only as status 0.
