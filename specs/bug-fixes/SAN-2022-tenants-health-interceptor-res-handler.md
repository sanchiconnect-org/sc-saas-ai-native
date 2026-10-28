---
id: SAN-2022
title: "GET /api/health: TransformInterceptor destructures the undefined return of an @Res() handler, then the exception filter writes a second reply"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2022
sentry: [SC-SAAS-TENANTS-8, SC-SAAS-TENANTS-9]
repos: [tenants]
related: [SAN-1572, SAN-1574]
commit: tenants@01625da (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2022: tenants health probe produces two Sentry events per hit

## Root cause
* TENANTS-9 and TENANTS-8 each have 4 events, about 11 ms apart in the same trace, from 2026-10-24 to 2026-10-26. They come from `api.tenants.sanchidev.in` (`environment: local`), with a `curl 8.7.1` user agent, shortly after app start: post-deploy checks.
* The route comes from `ab2e98a` (SAN-1574). That commit is on `ai_native_setup` but not on development, stagingdemo or master, so this is new code, not a stale build.
* How the two events happen:
  1. `src/core/health/health.controller.ts` writes its reply with `@Res()` + `res.status().json()` and returns `undefined`. Its comment assumed `@Res()` bypasses global interceptors. It doesn't: Nest only skips sending the return value.
  2. `src/core/interceptors/transform.interceptor.ts:25` did `map(({ message, data }) => …)`, which throws a TypeError on `undefined`. That is TENANTS-9.
  3. `GlobalExceptionFilter` then called `response.status().json()` on an already-sent reply, which throws inside the filter as an unhandled rejection. That is TENANTS-8.
* The same thing happens on the 404 path of `sentry-prover.controller.ts`, so a stranger probing `/api/ops/sentry-prove` sent 2 Sentry events. That defeats its own design.
* The client always got the right 200/503 body, because the body is written before the interceptor runs.
* sc-saas-backend already guards this case in its own `transform.interceptor.ts`. Tenants didn't.

## Fix
* `src/core/interceptors/transform.interceptor.ts`: when `res.headersSent` is true, pass the body through untouched. Otherwise build the same `{status_code, message, data}` envelope as before.
* `src/core/exceptions/global-exception.filter.ts`: when `response.headersSent` is true, log and return without writing.
* `src/core/health/health.controller.ts`: corrected the misleading comment.
* New specs:
  * `src/core/interceptors/transform.interceptor.spec.ts`: the envelope for a normal handler, and the pass-through for an `@Res()` reply.
  * `src/core/exceptions/global-exception.filter.spec.ts`: the normal error shape, and no write once headers are sent.

## Blast radius / existing-flow impact
Tenants only. For every normal controller `headersSent` is false, so the response envelope and the tenant-verification contract (invariant #3) are unchanged. A non-`@Res()` controller that returns `undefined` still errors, as it does today. Consumers of `/api/health` are unaffected.

## Verification
* `npx jest src/core`: 8 suites, 43 tests passed.
* `npm run gates` (sanchiconnect-saas-tenants):

```
  0    lint
  1    test
  0    test-floors
  0    build
  0    unguarded-routes
```

The `test` failure is unrelated to this change and is an artifact of this machine. There are 3 failures, all generated-contract "is up to date" checks: `ai-credits.contract.spec.ts` (2) and `tenant-verification.contract.spec.ts` (1). This Windows checkout has `core.autocrlf=true`, so `contracts/generated/*.ts` are on disk with CRLF and the byte comparison fails. All 138 other tests pass (floor 137).
* After deploy: run `curl /api/health` and confirm no new TENANTS-8/9 events, then resolve both.
* An HTTP-level test through a real Nest app was added afterwards. See the regression check below.

## Regression check (old flow unchanged)
* New `src/core/health/health.http.spec.ts` boots a real Nest app wired like `main.ts`/`app.module.ts` (global `TransformInterceptor`, `GlobalExceptionFilter` as `APP_FILTER`, real `HealthController`) and calls it over HTTP with supertest.
* **Against the original interceptor/filter (HEAD):** the success envelope, the 4xx error shape and the 500 shape all pass, but both `/api/health` tests fail. **Against the fix:** all 5 pass. So existing API responses are unchanged and only the health bug is gone.
* Final `npm run gates`: lint 0, test 1, test-floors 0 (143 passing), build 0, unguarded-routes 0. The 3 failing contract checks pass (9/9) once `contracts/generated/*` are converted to LF, which proves they fail only on this CRLF checkout. The files were restored afterwards and `contracts/` is untouched.
