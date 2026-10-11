# SAN-1658 — 3rd-party gateway: `GET /` returns NotFoundException (895 Sentry events)

- **Linear:** SAN-1658 (SC-SAAS-3RDPARTY-WEBSERVICES-1)
- **Repo:** sc-saas-3rdparty-webservices · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (probe noise)

## Problem
`AppController`'s `GET /` ("API works!") lived under `setGlobalPrefix('api')`, so a probe or bot requesting the bare root URL got a
`NotFoundException` that Sentry recorded 895 times.

## Fix
`src/main.ts`: `setGlobalPrefix('api', { exclude: [{ path: '/', method: RequestMethod.GET }] })`. Only `GET /` is excluded; `POST /` and every
other path stay 404. `src/app.controller.spec.ts` (3 cases) re-creates the main.ts prefix/versioning setup and documents the behaviour.

## Behaviour change to know about
The handler is now served at `/` and no longer at `/api`. The backend's gateway client always calls versioned paths (`ThirdPartyURL.*_V1`) and
nothing calls the bare `/api`.

## Auth model
Unauthenticated, static message, no data — the same handler that was already reachable under the prefix. Stated explicitly per the workspace
unauthenticated-endpoint rule.

## Contract impact
None for callers: the gateway is called only by sc-saas-backend on versioned routes, which are unchanged. No flag, tenancy or auth change.

## Verification
`app.controller.spec.ts` (the `GET /` case fails without the exclusion), full suite 12 passed, `tsc --noEmit` clean. The spec does not import main.ts,
so it must be kept in step with it.

## Commit
sc-saas-3rdparty-webservices `1b86070` on `ai_native_setup_aman`. Not deployed.
