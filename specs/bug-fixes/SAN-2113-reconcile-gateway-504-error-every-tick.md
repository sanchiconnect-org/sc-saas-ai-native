---
id: SAN-2113
title: "Payment reconcile cron logs an error every tick while Easebuzz returns 504"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2113
sentry: [SC-SAAS-BACKEND-67]
repos: [backend]
related: [SAN-2104]
commit: backend@a641b3e8, superseded by SAN-2104 60477c01 in merge 8eefa78d (branch ai_native_setup_vishali)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2113: a gateway outage is not a reconcile failure

## Root cause
* 67: `Reconcile failed for order 181 (EZ1793075332773): Request failed with status code 504`, 19 events in 36 min on dev.
* `verifyPendingPayments()` (`src/modules/cron/verify-pending-payments.service.ts`) logged every per-order error at error level, gateway 5xx and timeouts included, so the same 504 was captured on every run. There was no per-order backoff.

## Fix
* `a641b3e8` added `isTransientGatewayError()`: a gateway 5xx or a timeout now warns and leaves the order for the next run.
* Aman's **SAN-2104** (`60477c01`, on `ai_native_setup`) fixed the same catch independently. His version also adds per-call gateway timeouts (`GATEWAY_TIMEOUT_MS`) and a spec (`verify-pending-payments.service.spec.ts`).
* When `ai_native_setup` was merged into `ai_native_setup_vishali` (merge `8eefa78d`), the conflict was resolved by taking the SAN-2104 version. The SAN-2113 helper was dropped as a duplicate; behaviour is the same.

## Blast radius / existing-flow impact
Backend only. No change to paid, credited or state-transition logic, and no new column. As before, a failing order skips `markOrderAbandonedIfStale` for that run and is polled again next time.

## Verification
* After the merge: `npx tsc --noEmit` → 0; `npx jest src/modules/cron src/modules/payment-management` → 17 suites passed, 197 tests passed (SAN-2104 spec included)
