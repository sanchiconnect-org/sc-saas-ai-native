# SAN-2003 — Make Payment redirects to login: GET payments/coupons requires admin token

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-2003
- **Repo:** sc-saas-backend (branch `ai_native_setup_vishali`)
- **Classification:** CODE_ERROR (regression from SAN-1961, commit `abb23a1b`)
- **Priority:** High · **Assignee:** vishali kashyap

## Problem
In program payment, clicking **Make Payment** sends the user to `/auth/login` (thub.sanchidev.in).

## Evidence
`GET https://api.thub.sanchidev.in/api/v1/payments/coupons` → `401 {"message":"Admin token is required (Authorization: Bearer <token>)"}`, followed by a `logout` call.

## Root cause
SAN-1961 put `@UseGuards(AdminTokenGuard)` on `GET payments/coupons` on the grounds that the route had "no caller". The PWA does call it: `sc-saas-frontend` `checkout.component.ts` → `payments.service.ts getCouponList()`. The URL is built as `PAYMENT + "coupons"`, so a search for the literal path missed it. The frontend interceptor (`add-token-header.http-request-interceptor.ts`) treats every 401 as an expired session and does clear storage → logout → `/auth/login`.

## Decision
Product decision: coupons need no authorization, because users who haven't registered also apply coupons when they apply to a program. `payment_coupons` has no column that ties a coupon to a user (`applies_to` is never read), so the public list holds only active, in-date generic codes.

## Fix (files changed)
- `src/modules/payment-management/payment-management.controller.ts` — removed `AdminTokenGuard` from `getCoupons` (`FeatureGuard`/`PAYMENT_GATEWAYS` stays).
- `tests/unguarded-routes.json` — `allowList` entry (`kind: public`) for `getCoupons` with its reason and owner.
- `src/core/utils/own-profile.spec.ts` — dropped the SAN-1961 assertion that `getCoupons` has `AdminTokenGuard`.

## Verification
`npm run gates` in sc-saas-backend: lint 0, test 0 (1468 passed), test-floors 0, openapi-floors 0, unguarded-routes 0 (310 allow-listed, 42 unreviewed). `build` is 1 **on the untouched baseline too**: `deploy-migrate.ts:139` `runMigrations({ fake: true })` TS2345, not related to this fix.

## Open
- The `build` gate is red on the branch independently of this fix (`deploy-migrate.ts`).
- Optional frontend hardening (separate issue, Repo: Frontend): mark `getCouponList()` with `SKIP_UNAUTHORIZED_REDIRECT` so a failed coupon list never logs the user out.

## Commit
`232e07f4` on `ai_native_setup_vishali` (sc-saas-backend), pushed 2026-10-22. Linear: Done.
