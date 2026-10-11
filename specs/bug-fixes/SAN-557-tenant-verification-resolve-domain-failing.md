---
id: SAN-557
title: Tenant verification failing on resolve-domain — registration blocked (165 users)
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-557
sentry:
  - SC-SAAS-FRONTEND-26
repos: [frontend]
commit: n/a — cross-repo infra/DB issue, no frontend code change
created: 2026-09-03
updated: 2026-10-07
---

# SAN-557 — Tenant verification failing on resolve-domain

## Finding
`TenantService.getTenantDetails()` calls `resolve-domain/:hostname` on the tenants cockpit and correctly propagates a failure to `AppComponent.getTenantDetails()`'s error callback (`app.component.ts:369-393`). That callback already:
- Sets `tenantLoading = false` and hides the app loader (no infinite spinner).
- Sets `tenantError` from the response body.
- In production, calls `Sentry.captureMessage(...)` with a **fixed fingerprint** (`'tenant-verification-down'`) and tag `alert: 'tenant-verification-down'`, so every occurrence across every hostname collapses into one Sentry group instead of one per visitor.

That fixed-fingerprint behavior is exactly what SAN-159 ("Capture tenant-verification failures as fingerprinted Sentry issue + email alert rule") proposed — it's already implemented in committed code, even though SAN-159 is still showing Backlog in Linear (stale status, worth correcting).

Because of the fixed fingerprint, `SC-SAAS-FRONTEND-26`'s displayed message/culprit (`connect.trise.tripura.gov.in`) is just whichever event Sentry last received — the 165 users / 223 events figure likely spans many different tenant hostnames bucketed into this one group, not one broken domain.

## Re-investigated 2026-09-03
Re-confirmed: this is a genuine defect (real production failures, not noise) but not fixable from `sc-saas-frontend` — the frontend side of it is already correct. Conclusion stands.

## Action required (Tenants repo owner)
The frontend has no bug here — it fails gracefully and reports correctly. The actual `0 Unknown Error` responses originate from the tenants cockpit (`sanchiconnect-saas-tenants`), which is **not checked out in this workspace**, so root-causing it is out of reach from `sc-saas-frontend` alone. Two known related, already-triaged tickets to check against before assuming this is new:
- SAN-417 (Canceled) — `verify_tenant` failing at the DB, ECONNREFUSED/ETIMEDOUT
- SAN-188 (Done) — `verify_tenant` intermittent 504s from an unindexed LIKE scan (different failure mode — this is `0 Unknown Error`, not 504)

Recommend: pull per-hostname breakdown from the fingerprinted Sentry group (via `tenant_verification` context set in the capture above) to see whether this is one tenant or many, then investigate from the tenants cockpit side.

## Blast radius
None — no code changed.

## Verification
N/A — no code change made.

## Update 2026-10-07
Closed after the Oct 5-7 work (frontend retry `e233de1af` SAN-1672, tenants resolve-domain cache `f74d37d`, and the root-cause breakdown of FRONTEND-26 — unregistered origins get 418, 504s from tenants API load, client network drops). Full findings: `SAN-557-frontend-26-tenant-verification-cors-registry-and-504.md`.
