---
id: SAN-554
title: "getOrganizationNameWithMentorNull missing optional-chaining guards"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-554
sentry:
  - SC-SAAS-BACKEND-1D
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-554 — getOrganizationNameWithMentorNull null guards

## Root cause — hypothesis, never fully confirmed

Sentry's culprit for SC-SAAS-BACKEND-1D pointed at `getOrganizationName()`, which is already fully
guarded (`user.investor?.organizationName ?? ''` style on every branch) and cannot throw as written.
Its sibling `getOrganizationNameWithMentorNull()` in the same file was NOT guarded
(`user.investor.organizationName` with no `?.`) — the far more likely actual crash site, given
Sentry's culprit resolution can misattribute to the nearest named export in a compiled build.

This issue recurred unchanged 13 days after the fix shipped (still `environment: local`, no
production recurrence seen), so the hypothesis was never conclusively verified against a real
stacktrace.

## Fix

Added the same optional-chaining guards to `getOrganizationNameWithMentorNull()` that
`getOrganizationName()` already has (STARTUP/INVESTOR/CORPORATE/SERVICE_PROVIDER/PARTNER branches).

## Blast radius

None — hardens an unsafe function regardless of whether it was the exact original crash site.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.

## Open questions

If SC-SAAS-BACKEND-1D recurs again after this deploys, the real crash site needs a fresh look with
an actual stacktrace/sourcemap — this fix was defensive, not confirmed root-cause.
