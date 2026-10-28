# SAN-2004 — Checkout: a failed coupon-list call logs the user out and redirects to login

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-2004
- **Repo:** sc-saas-frontend (branch `ai_native_setup_vishali`)
- **Classification:** CODE_ERROR · **Priority:** High · **Assignee:** vishali kashyap
- **Related:** SAN-2003 (backend half), SAN-1961 (the change that turned the route into a 401)

## Problem
On program payment → Make Payment, registered and unregistered users are both sent to `/auth/login` when `GET /api/v1/payments/coupons` returns 401.

## Root cause
`checkout.component.ts` loads the coupon picker in the background through `payments.service.ts getCouponList()`. `add-token-header.http-request-interceptor.ts` treats every 401 as an expired session and does clear storage → logout → `/auth/login`, so a failure in an optional list ends the user's session.

## Fix (files changed)
- `src/app/core/service/payments.service.ts` — `getCouponList()` sends `SKIP_UNAUTHORIZED_REDIRECT` (the same pattern as `notifications.service.ts`, SAN-1729) and returns `[]` on error. Checkout keeps working without the picker, and a code can still be typed (`coupon/verify`).

## Verification
`npm run gates` in sc-saas-frontend: openapi-types 0, loader-floor 0, build 0, unit-tests 0, test-floors 0 (1125 passing, floor 1116) → passed. Not yet verified in a browser; that needs a deploy.

## Open
- Needs a merge to `ai_native_setup` / `development` and a redeploy, then a browser check logged in and logged out.

## Commit
`baad7d0dc` on `ai_native_setup_vishali` (sc-saas-frontend), pushed 2026-10-22. Linear: Done.
