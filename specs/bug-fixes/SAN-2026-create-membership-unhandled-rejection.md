---
id: SAN-2026
title: "Column 'profile_type' cannot be null as an unhandled rejection: createMembership() is fire-and-forget with no catch"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2026
sentry: [SC-SAAS-BACKEND-4F]
repos: [backend]
related: [SAN-1021, SAN-1152, SAN-1561]
commit: backend@1ff837bb (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2026: membership insert failures escape as frame-less rejections

## Root cause
* 4F has 4 events:
  * 09-29, 09-30 and 10-04 in production;
  * 10-23 from a developer's local Docker.
* All are `handled: no`, `mechanism: onunhandledrejection`, with no first-party frame and no `failedQuery`. No production event since 10-04.
* This is not the same path as SAN-1021 (the admin `event_booths` insert, already fixed). SAN-1152 was inconclusive.
* Likely path `[UNVERIFIED — no event carries the SQL]`:
  * `memberships.profile_type` is `varchar(50) NOT NULL DEFAULT 'startup'`. TypeORM writes `NULL` for an explicit `null`.
  * `createMembership()` sets `profileType: membershipData?.profile_type`.
  * `membershipData` can carry an explicit null: on main it is the raw client payload, and SAN-1561 `21435b70` sets `profile_type ?? null` on the call-for-applications path.
* Both callers (`createTransaction` ~1718 and `createDiscountedTransaction` ~2407) call `this.createMembership(order);` without `await` or `.catch`. `main` has the same code. Any failure therefore becomes an unhandled rejection with no frame, which matches the event's mechanism exactly.

## Fix
`src/modules/payment-management/repositories/payment.repository.ts`:
* Both fire-and-forget calls now do `this.createMembership(order).catch((error) => this.logMembershipFailure(order, error))`.
* The new private `logMembershipFailure()` logs `LOG_ERROR: 'createMembership() failed'` with `orderId`, `moduleType` and the error message.

The payment flow never waited for the membership insert, and it still doesn't. Only the failure reporting changes.

New spec `payment.repository.san2026.spec.ts`:
* A rejected `createMembership` still returns the saved transaction and logs the order id.
* A successful one logs nothing extra.

**Not done, on purpose:**
* Silently defaulting `profile_type` to `'startup'`. That would attach the membership to the wrong profile type.
* Any change around line 549 (the call-for-applications `profile_type ?? null`). Nirmal owns that under SAN-1561.

## Blast radius / existing-flow impact
Backend only, and logging only. API contract unchanged (no controller/DTO touched). Tenant scoping unchanged (no new query).

## Verification
* `npx jest src/modules/payment-management/repositories`: 2 suites, 21 tests passed (SAN-1561 + SAN-2026).
* `npm run gates` (sc-saas-backend), run together with SAN-2021:

```
  0    lint
  0    test
  0    test-floors
  0    openapi-floors
  0    build
  0    unguarded-routes
=> passed
```

Tests: 1704 passed, 23 skipped (floor 1702).
* Local note: `bcryptjs@2.4.3` was declared and locked (SAN-2015) but missing from this machine's `node_modules`. I installed it with `npm install --no-save`, so `package.json` and the lockfile are unchanged by that.

## Decision pending
**Dev lead / Nirmal:** when a membership order's profile type can't be resolved, should checkout reject it, or should the server derive the type?
