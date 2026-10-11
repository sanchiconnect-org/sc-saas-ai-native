---
id: SAN-902
title: "OCR claims KPI counters ignore month/date filters"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-902
sentry: []
repos: [admin]
commit: sc-saas-admin@b33383f7 (branch ai_native_setup_vishali)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-902 — OCR claims KPI counters ignore filters

## Root cause
CODE_ERROR — `modules/operation_cost/claims.php`'s `ocrFetchClaimsCount($apiUrlBase, $adminToken, $status = null)` only ever accepted a `$status` filter. The 5 stat-card calls (Total/Submitted/Under Process/Sanctioned/Rejected) never passed `monthIndex`/`startDate`/`endDate`, while the main table query just above builds the exact same `queryParams` with all four filters included, hitting the same `GET admin/claims` backend route. Result: the KPI cards always show all-time-per-status counts, visibly disagreeing with the filtered table whenever a month or date-range filter is applied.

## Fix
Extended `ocrFetchClaimsCount()` to accept `$monthIndex`/`$startDate`/`$endDate` and pass them through at all 5 call sites, mirroring the main list query's own `$queryParams` build. Single-repo, admin-only — the backend endpoint already supports these params (confirmed: the main list query already uses them successfully against the same route).

## Also verified while investigating (per request to check counters/actions/filters)
- Filters (status/month/date-range): correctly applied server-side, single query, no N+1.
- Bulk Sanction / Download: correctly enforce sanctionability/status-transition rules server-side; client-side gating is UX-only.
- Tenant scoping: this admin module makes zero direct DB queries for claims — fully proxied to `sc-saas-backend` (one-deployment-per-tenant). No cross-tenant leakage found.
- Minor, out-of-scope note: `sc-saas-backend`'s bulk-sanction path re-fetches the same claim rows twice when resolving an explicit claimId selection (`getClaimsByUuids()` then `getClaimsByIds()`) — a redundant round-trip, not a correctness bug, not fixed here.

## Blast radius
Only `modules/operation_cost/claims.php` touched (the `ocrFetchClaimsCount()` function and its 5 call sites). No template/JS change, no backend change.

## Verification
No PHP linter available locally (`php` not on PATH in this environment) — reviewed the diff by hand for balanced syntax; it's a small, mechanical parameter-passthrough change following the exact pattern already used two lines above it for the main list query. No test framework exists in this repo (per this workspace's standing note). Committed and pushed: `sc-saas-admin@b33383f7` (branch `ai_native_setup_vishali`), after user review.
