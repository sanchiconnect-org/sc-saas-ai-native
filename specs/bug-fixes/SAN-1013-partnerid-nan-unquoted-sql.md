---
id: SAN-1013
title: "QueryFailedError: Unknown column 'NaN' — JWT-sourced partnerId unquoted in raw SQL"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1013
sentry: [SC-SAAS-BACKEND-3M]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-29
updated: 2026-09-29
---

# SAN-1013 — partnerId NaN reaching raw SQL unquoted

## Root cause
`startup.repository.ts`'s `searchStartupOrLiveDeal()` interpolates `partnerId` **unquoted** into raw SQL: `startups.partnerId = ${partnerId}` (line 1144, plus two more unquoted/quoted uses in the same clause). If `partnerId` is ever a non-numeric JS value, the resulting SQL becomes e.g. `startups.partnerId = NaN` — MySQL parses the bare `NaN` as a column/identifier reference rather than a value, producing exactly `QueryFailedError: Unknown column 'NaN' in 'field list'`. This is the same error-message shape as SAN-380/405/478, but a different, previously-unfixed call site — Sentry opened a new group (SC-SAAS-BACKEND-3M) because the exact error text differs.

Traced where `partnerId` comes from in `search.service.ts`. There are two paths:
1. Query string: `search.controller.ts:78` — `Number(req.query.partnerId) || null`. Already safe (NaN is falsy, coerces to `null`).
2. **JWT-sourced**: `search.service.ts` — `if (loggedInUser?.accountType === 'partner' && loggedInUser.partnerId) { partnerId = loggedInUser.partnerId; }`. This path had **no numeric guard at all** — any truthy non-numeric value on the logged-in user's session/token (e.g. a stringified non-numeric value) would flow straight through to the unquoted SQL interpolation. This exact same copy-pasted block appears **7 times** in `search.service.ts` (one per search method: startup, investor, corporate, mentor, job, corporate-live-deal variants), all with the identical gap.

## Fix
`search.service.ts`: replaced the truthy check with `Number.isFinite(Number(loggedInUser.partnerId))` and assign `partnerId = Number(loggedInUser.partnerId)`, mirroring the guard the query-string path already had. Applied identically to all 7 occurrences (byte-identical blocks, confirmed via grep before using `replace_all`).

`startup.repository.ts`: also added the already-established `.filter(Number.isFinite)` guard (per the SAN-478 precedent) to 5 sibling array-split blocks that were missing it (`industryDomainSubCategoryIds`, `mentorshipAreas`, `programs`, `businessModelIds`, `instrumentIds`) — these interpolate into quoted `JSON_CONTAINS(...,'${value}')` calls so they couldn't produce this specific "Unknown column" error, but shared the same missing-guard anti-pattern and are worth closing for consistency/defense-in-depth while in this code.

## Blast radius
`sc-saas-backend`: `search.service.ts` (7 identical call sites) and `startup.repository.ts` (5 array-filter additions). No behavior change for any valid numeric `partnerId` — only changes what happens when it isn't one (previously: crash; now: treated as "no partner scoping", same as the already-safe query-string path).

## Verification
`npx tsc --noEmit -p tsconfig.json` clean. No test suite covers this path.

## Rollout
Not resolving SC-SAAS-BACKEND-3M outright — recommend watching for recurrence for a few days post-deploy, since the exact upstream source of the non-numeric `loggedInUser.partnerId` value was never pinned down (couldn't inspect live JWT/session payloads from this session) — the fix closes the crash regardless of that value's origin, but if it keeps happening, worth checking what's writing a non-numeric `partnerId` onto partner sessions in the first place.

## Open questions
None.
