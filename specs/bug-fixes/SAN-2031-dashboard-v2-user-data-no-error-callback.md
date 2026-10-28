---
id: SAN-2031
title: "dashboard-v2 getDashboardUserData() has no error callback: a 0/5xx on dashboards/user is thrown to ErrorHandler"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2031
sentry: [SC-SAAS-FRONTEND-1]
repos: [frontend]
related: [SAN-804, SAN-1930, SAN-1978]
commit: frontend@c2c995137 (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2031: dashboards/user failure was unhandled

## Root cause
* FRONTEND-1: `Http failure response for …/api/v1/dashboards/user: 0 Unknown Error`.
  * The latest event is from thub dev, during an outage of the dev API.
  * In prod it is sporadic: 2 events on `218edca78` in 30 days.
* `dashboard-v2.component.ts` subscribed to `getDashboardUserData()` without an error callback.
* The service shows a toast and rethrows, so the error reached ErrorHandler.

## Fix
* `getDashboardUserData()` is now subscribed with `{ next, error }`. The error callback is empty: the service already toasted, and the dashboard renders without user events.
* Test in `dashboard-v2.component.spec.ts`: when user data fails, nothing throws, `userEvents` stays undefined, and `content` still loads.

## Blast radius / existing-flow impact
None on the success path.

## Verification
* Targeted specs: `npx ng test --watch=false --browsers=ChromeHeadlessCI --include=<connect-button, connections-v3, dashboard-v2, program-public-apply, app.component specs>` → `TOTAL: 48 SUCCESS`.
* `npx tsc -p tsconfig.app.json --noEmit` → 0; `npx tsc -p tsconfig.spec.json --noEmit` → 0.
* `npm run gates` (sc-saas-frontend, all five frontend tickets together):

```
passing tests: 1304 (floor 1295)
  0    openapi-types
  0    loader-floor
  0    build
  0    unit-tests
  0    test-floors
=> passed
```

## Regression check (old flow unchanged)
* Added a success-path spec: when both calls succeed, `userEvents` and `content` are set as before. It passes against the original component (HEAD) and against the fix.
* Final `npm run gates`: all gates 0, 1309 tests passing.
