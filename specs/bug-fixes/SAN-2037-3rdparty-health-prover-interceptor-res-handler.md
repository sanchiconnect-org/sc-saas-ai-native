---
id: SAN-2037
title: "3rdparty-webservices: /api/health and the Sentry prover 404 double-reply through the global interceptor and filter"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2037
sentry: []
repos: [3rdparty-webservices]
related: [SAN-2022, SAN-1572, SAN-1574]
commit: 3rdparty-webservices@378caa4 (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2037: the same @Res() defect as SAN-2022, in the gateway

## Root cause
I found this while reviewing SAN-1572. It is latent: there are no Sentry events yet. The cause is the same as SAN-2022 in tenants.

1. Two handlers reply with `@Res()` and return `undefined`:
   * `src/core/health/health.controller.ts`
   * the 404 path for a missing or wrong token in `src/core/health/sentry-prover.controller.ts`
2. The global `TransformInterceptor` (`main.ts:66`) does `map(({ message, data }) => …)`. Destructuring `undefined` throws a TypeError.
3. `GlobalExceptionFilter` then calls `response.status().json()` on a reply that was already sent.
4. In this repo the filter calls `Sentry.captureException` on every exception. So every health probe and every token-less prover call would send Sentry events, which breaks the prover's stated design. `captured` mode would also send 2 events instead of 1.

sc-saas-backend already guards its interceptor. Tenants is fixed by SAN-2022.

## Fix
* `src/core/interceptors/transform.interceptor.ts`: pass the body through untouched when `res.headersSent` is true.
* `src/core/exceptions/global-exception.filter.ts`: when `response.headersSent` is true, return without writing.
  * The guard sits after the Sentry capture and logging. A genuine error raised after a reply has gone out is still reported; only the second write is skipped.
* `src/core/health/health.controller.ts`: corrected the comment.
* New specs:
  * `transform.interceptor.spec.ts`
  * `global-exception.filter.spec.ts`
  * `health.http.spec.ts`: boots Nest with the global interceptor, `APP_FILTER` and the real health and prover controllers, and counts `Sentry.captureException` calls.

## Blast radius / existing-flow impact
3rdparty only. For every normal controller `headersSent` is false, so the `{status_code, message, data}` envelope that sc-saas-backend consumes is unchanged. Error shapes are unchanged, and errors are still reported to Sentry. No API or contract change.

## Verification
* `npx jest src/core`: 6 suites, 24 tests passed, including the existing prover and gateway-key specs.
* `health.http.spec.ts` against the **original** interceptor and filter (HEAD):
  * passed: the envelope, the error shapes, and `uncaught` mode;
  * failed: health, the prover's token-less 404, and `captured` mode, all with extra Sentry calls.
* Against the fix, all 6 pass.
* `npm run gates`:

```
  0    lint
  0    test
  0    test-floors
  0    build
  0    unguarded-routes
=> passed
passing tests: 36 (floor 26)
```

* Local note: this machine had no `node_modules` for this repo. I installed them with `npm ci` from the committed lockfile, and no tracked file changed.

## Real-app check (built gateway, `node dist/main`)
Both the original code (HEAD) and the fix were built, then booted the same way:
* with dummy config, from a scratch folder, so no real `.env` and no external providers were used;
* with a local fake Sentry ingest that counts error events;
* with `GATEWAY_KEY_MODE=log`.

Each build got the same 9 requests.

| Request | Response, original vs fix | Sentry events, original → fix |
|---|---|---|
| `GET /`, `GET /api` | identical | 0 → 0 |
| `POST /api/v1/sms/send-otp {}` (400 validation) | identical | 1 → 1 |
| `GET /api/v1/nope` (404) | identical | 1 → 1 |
| `GET /api/health` | identical | **2 → 0** |
| prover, no token / wrong token | identical | **2 → 0** each |
| prover `captured` | identical | **3 → 1** |
| prover `uncaught` | identical | 1 → 1 |

* The original logged `TypeError: Cannot destructure property 'message'` and `ERR_HTTP_HEADERS_SENT` on every `@Res()` route. The fix logged neither.
* The process stayed up in both runs.
