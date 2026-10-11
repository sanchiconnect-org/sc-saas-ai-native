---
id: SAN-478
title: "SC-SAAS-BACKEND-B conflates unrelated QueryFailedErrors — fingerprint override so future SQL errors split correctly"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-478/sentry-sc-saas-backend-b-queryfailederror-unknown-column-nan-in-field
sentry: [SC-SAAS-BACKEND-B]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-478 — SC-SAAS-BACKEND-B fingerprint conflation

## Root cause
`SC-SAAS-BACKEND-B` has been fought over by four separate tickets across a month (SAN-380, SAN-405, SAN-478, SAN-892) because Sentry's default grouping fingerprints by stack trace, and **every** raw MySQL query failure in this app (`QueryFailedError` from TypeORM) bubbles up through the exact same generic frames — `mysql2`'s socket/packet-parser internals into `MysqlQueryRunner.onResult` — with no first-party application frame anywhere in the trace. Confirmed directly via `search_events`: on 2026-09-24 alone, this single issue ID received both `"Unknown column 'NaN' in 'field list'"` events (07:38, 08:23) and unrelated `"Cannot add or update a child row: a foreign key constraint fails (startup_financials, FK funding_stage_id)"` events (06:41 x6 — the bug already fixed today in `sc-saas-admin`, SAN-892) — two completely different bugs, indistinguishable in Sentry's UI because they share one issue.

This explains the "regressed" status and the appearance of the same short ID being reused for different bugs: it was never actually a different bug reusing the ID, it's one ID silently absorbing every distinct SQL failure that happens to hit this generic driver-level catch.

## Fix
Added `fingerprintQueryFailedError()` to `src/instrument.ts`'s `beforeSend` chain — overrides `event.fingerprint` to `['queryfailederror', exception.value]` (the exception's own message) whenever `exception.type === 'QueryFailedError'`. Distinct SQL error messages now group into distinct Sentry issues instead of collapsing onto the shared stack-trace fingerprint.

**Known tradeoff, accepted**: a MySQL error message that embeds a per-event variable value (e.g. `Duplicate entry 'X' for key 'Y'` where `X` differs per occurrence) would now fragment into one Sentry group per distinct value, rather than one shared group. This is a net improvement for this codebase's actual failure modes observed so far (stable messages: "Unknown column 'NaN'", a fixed FK constraint name) but is worth revisiting if a future high-cardinality query-error message starts producing excessive distinct issues.

## Blast radius
`sc-saas-backend` only, `instrument.ts`. No behavior change to the application — purely a Sentry-side grouping change for future events. Does not touch, fix, or mask any actual SQL error; a query that fails today still fails identically.

## Verification
`npx tsc --noEmit` clean. No test suite covers `instrument.ts`. Verified the conflation itself directly via Sentry's `search_events` (two distinct messages under one `issue.id`), which is the evidence this fix responds to.

## Rollout
This does **not** fix the underlying "Unknown column 'NaN'" bug itself — that root cause (which endpoint/query produces a `NaN` numeric parameter) is still not pinpointed. Ruled out during investigation: the `profileCompletenessPercent` raw-interpolation pattern repeated across 7 repositories (individual/corporate/investor/mentor/partner/service-provider/startup) — all call sites pass either `null` or a hardcoded literal (`'< 100'`, `'< 95'`), never a computed value, so none of them can produce `NaN`. Also confirmed empirically (via `mysql2`'s own `format()`) that a bound `NaN` parameter serializes identically to raw string interpolation (`WHERE id = NaN`, unquoted) — meaning the actual bug could be in a parameterized query too, not only raw-interpolated ones, which broadens rather than narrows the remaining search. Next occurrence of this specific message will now land in its own Sentry issue, making it traceable without cross-contamination from unrelated SQL errors.

## Open questions
The exact endpoint/query producing the `NaN` numeric parameter is still unidentified. Recommend checking the next isolated occurrence's timing against access/CloudWatch logs for the exact request, since Sentry itself doesn't capture request context on this error class (raised from the raw MySQL driver layer, before Express/Nest's request-scoped Sentry context attaches).
