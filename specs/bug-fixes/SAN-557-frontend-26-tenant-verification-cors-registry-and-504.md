# SAN-557 — FRONTEND-26 tenant verification failures: three distinct causes

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-557 (also SAN-1672; Sentry SC-SAAS-FRONTEND-26, ~3,850 events / ~1,750 users) · **Repo:** sanchiconnect-saas-tenants (+ sc-saas-frontend) · **Priority:** Urgent · **Assignee:** Aman kabra · **Classification:** MIXED (data/ops, infra load, client network). Earlier record: `SAN-557-tenant-verification-resolve-domain-failing.md`.

## Evidence
Probe (observed, 2026-10-07): `GET /api/v1/public/global/resolve-domain/<host>` with an `Origin` header and a browser User-Agent; registered hosts answer 200 + `Access-Control-Allow-Origin`, others 418.
- (a) **Unregistered origins, 418 without ACAO:** `sg.sanchiapp.com` (~1,720 events / ~465 users, about half the volume), `acceleration.ihubgujarat.in`, `edge.isba.in` (look like real customers), `messenger/admin.demo/adm/cms/cp/share/qa.sanchiapp.com`, `thub.sanchidev.in`; raw IPs `16.4.14.68`, `13.204.191.30` are bots (inferred).
- (b) **504 Gateway Timeout:** 744 events / 317 users on registered hosts (tenants API load; cause inferred).
- (c) **Status 0 on registered hosts:** client network drops (inferred).

## Root cause
(a) The `src/main.ts` origin callback rejects anything not in `CORS_DOMAINS` or the `cors_domains` registry (SAN-384, intentional) with HTTP 418 and no ACAO; the browser reports status 0 "Unknown Error". (b) Every page load hit uncached DB queries on the tenants API. (c) Transient client connectivity.

## Fix
- (b) `f74d37d` (SAN-557, 2026-10-05): 30 s resolve-domain cache + in-flight coalescing, already in the repo.
- (c) Frontend retry `e233de1af` (SAN-1672).
- (a) No code: registering an origin is an operator/data action (tenants-admin CORS Domain Management / `cors_domains`, ~30 s cache refresh, no deploy). **No domain was registered** (production data); ops action pending. Specs updated: `sanchiconnect-saas-tenants/src/core/module.spec.md`, `src/modules/global/module.spec.md`.

## Not fixed
(a) persists until operators register the real tenant hosts (or non-tenant hosts are filtered from Sentry). (b) infra capacity (`max_connections`, replicas x pool size) is unchecked. The leading-wildcard `LIKE %host%` in `matchesTenant` is the frozen `verify_tenant` contract (tripwire #1) and was deliberately left unchanged.

## Contract impact
None. No response shape, flag or auth change.

## Verification
Live probes only (above); no code changed this pass. The cache and retry fixes were not re-measured under load.

## Commit
`f74d37d` (tenants) and `e233de1af` (frontend), both earlier. Spec edits are uncommitted.

## Sentry
Resolved under policy with a reopen note: status 0 on a registered host or a 504 after `f74d37d` points to tenants API capacity or client network; a new unregistered host means an ops registration.

## Owner decision 2026-10-07
The hosts in cause (a) are not current customers, so they are intentionally NOT registered; the "register in tenants-admin" action is cancelled. Sentry FRONTEND-26 is ignored-until-escalating rather than resolved.
