---
id: SAN-2030
title: "Accepting an already-accepted or withdrawn connection: the 409 escapes to ErrorHandler and the button stays on Accept"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2030
sentry: [SC-SAAS-FRONTEND-2J]
repos: [frontend]
related: [SAN-1011, SAN-1665, SAN-1673, SAN-1971, SAN-2005]
commit: frontend@08db8e130 (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2030: 409 on connections/accept reached Sentry

## Root cause
* 2J collects every thrown `Http failure response for …: 4xx` that has no stack.
  * In the last 14 days most of these are 401s from stale tenant builds that predate SAN-1673. That part is deploy lag, already covered by SAN-1971.
  * The live event on the current prod release (`218edca78`) is `…/connections/accept/<uuid>: 409`.
* Backend `connections.service.ts:1422-1426` returns 409 (`ALREADY_CONNECTED` / `CANNOT_PROCESS_REQUEST`) when the request was already accepted somewhere else or withdrawn. That response is correct.
* On the frontend:
  * `ConnectionsService.acceptConnection` shows a toast and rethrows.
  * `connect-button.component.ts` and `connections-v3.component.ts` used `tap(next, errFn)` followed by a bare `.subscribe()`. `tap` doesn't swallow errors, so the error reached Angular's ErrorHandler and then Sentry.
  * Nothing refreshed the UI, so the button stayed on "Accept".

## Fix
* `connect-button.component.ts`:
  * accept: the error handler swallows the error, because the service already toasted. On a 409 it calls `refreshConnectionStatus(toUserUUID)`, the same refresh the success path uses.
  * send-from-investor, send, remove and reject: these follow the same pattern (the service toasts and rethrows), so each now has `subscribe({ error: () => {} })`.
* `connections-v3.component.ts` accept: same error handler; on a 409 it calls `setConnectionsTypesCount()` and `setPendingRequestsData()`.
* Tests:
  * `connect-button.component.spec.ts`: a 409 refreshes the status; a 500 doesn't. Neither throws.
  * `connections-v3.component.spec.ts`: a 409 refreshes both lists.

## Blast radius / existing-flow impact
* The success paths, toasts and loader stop are unchanged: the existing `tap` error callback and `finalize` still run.
* No API change.
* Not touched: `removeConnection` / `rejectConnection` in connections-v3 still end in a bare subscribe. They are candidates for a follow-up.

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
* Added success-path specs:
  * connect-button: accept success refreshes, emits `accept` and stops the loader; reject success refreshes and emits `reject`.
  * connections-v3: accept success refreshes and navigates to `/connections/active-requests`.
* **Against the original components (HEAD)**, the success-path specs pass (6/6), so the behaviour is identical. With the error-path specs included, the original code crashes the test run on an unhandled error, which is the bug itself.
* Final `npm run gates`: all gates 0, 1309 tests passing.
