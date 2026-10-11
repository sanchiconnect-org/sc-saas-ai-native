---
id: SAN-665
title: "Uncaught (in promise): Cannot read 'mobileNumber' in connect-button shared component — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-665
sentry:
  - SC-SAAS-FRONTEND-79
repos: [frontend]
commit: "sc-saas-frontend@f0484689 (SAN-482), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-665 — profileDetails-undefined crash, already fixed

## Root cause
Same `profileDetails`-undefined pattern as SC-SAAS-FRONTEND-6A/SAN-482, reused in the shared
connect-button component within the programs module.

## Fix
Already fixed in commit `f0484689` (SAN-482, 2026-08-24), which added the guard for this exact crash
signature (referenced there as SC-SAAS-FRONTEND-3D). This issue's last-seen (2026-09-03) postdates the
fix commit, but the frontend has a known 17+ day prod deploy lag — likely stale prod, not unfixed code.

## Verification
Confirmed the guard added in SAN-482 covers this component's call site too. Deploy status should be
verified before treating as still-open (see [[project_frontend_prod_deploy_lag]]).
