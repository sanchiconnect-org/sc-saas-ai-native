---
id: SAN-625
title: "getRecommendedInvestors/getRecommendedCorporates crash on investor/corporate with no linked user"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-625
sentry:
  - SC-SAAS-BACKEND-C
repos: [backend]
commit: sc-saas-backend@70788fd8
created: 2026-09-07
updated: 2026-09-07
---

# SAN-625 — getRecommendedInvestors/getRecommendedCorporates null user

## Root cause

`startup.service.ts:247` (`getRecommendedInvestors`) reads `investors.items[i].user[0].id` with no
guard — crashes when an investor record has no linked top-level user. Same unguarded pattern also
existed in `getRecommendedCorporates` (`corporates.items[i].user[0].id`, line 1970), not yet reported
in Sentry but identical shape. The sibling `getRecommendedMentors` already had the correct guard
(`mentors[i].user[0]?.id`) — confirming this was a pattern applied once and simply missed twice.

Note: this Sentry group (`SC-SAAS-BACKEND-C`) previously covered an unrelated, already-fixed bug
(`InvestorService.getRecommendedStartups` null.map, SAN-461) — Sentry appears to reuse group IDs for
distinct crashes on this project.

## Fix

Added `?.` to both unguarded call sites, matching the already-correct `getRecommendedMentors` pattern.

## Blast radius

None.

## Verification

`tsc --noEmit` clean project-wide. No existing test suite for `startup.service.ts`.

## Rollout

Committed and pushed `sc-saas-backend@70788fd8` directly to `ai_native_setup`, also present on
`ai_native_setup_aman`.
