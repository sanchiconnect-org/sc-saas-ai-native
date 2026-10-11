---
id: SAN-983
title: "DivisionByZeroError in pre_issue.php share-percentage calc"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-983
sentry: [SC-SAAS-ADMIN-V]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-983 — DivisionByZeroError in pre_issue.php

## Root cause
`themes/default/html/portfolio_management/round/pre_issue.php:479` — `$stakeholder["total_shares"] / $total_market_shares` where `$total_market_shares = $this->portfolio['roundInfo']['pre_issue_shares']` can be `0` for a round that hasn't had its pre-issue shares configured yet.

## Fix
`$total_market_shares > 0 ? round(($stakeholder["total_shares"] / $total_market_shares) * 100, 2) : 0` — shows 0% instead of crashing the page when the round isn't configured yet.

## Blast radius
Single template file, single line. No behavior change once a round has pre-issue shares set.

## Verification
`php -l` clean.

## Rollout
Sentry issue SC-SAAS-ADMIN-V marked resolved. Not committed/pushed — sitting on `ai_native_setup_aman`, pending review.

## Open questions
None.
