# SAN-1672 — tenant bootstrap (`resolve-domain`) was a single un-retried call

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1672 (Sentry SC-SAAS-FRONTEND-26; server side SAN-557 / SAN-1560)
- **Repo:** sc-saas-frontend · **Priority:** Urgent · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (client resilience) over an infrastructure fault

## Evidence — still firing on the build deployed on Saturday 3 Oct
Release `sc-saas-frontend@bcf88383d` (PR #1902, merged 2026-10-02 21:31 IST) is the dominant production release (402 events in 4 days). It contains the earlier filters (SAN-471, SAN-599/601/608)
but none of the 5–6 Oct fixes. SC-SAAS-FRONTEND-26 is about 340 of those 402 events (about 85%), from these domains (events on that build, last 4 days):

| Domain | Events | Notes |
|---|---|---|
| sg.sanchiapp.com | 186 (61 users) | `0 Unknown Error` |
| connect.iiitdic.in | 49 | 504 and 0 |
| supernova.gdai.in | 35 | 504 and 0, still firing this morning |
| ecosystem.firstwingsconnect.com | 22 | 504 and 0 |
| acceleration.ihubgujarat.in | 11 | 504 and 0 |
| hub.startupsingam.com | 11 | 504 and 0 |
| sineedge.sineiitb.org | 8 | 504 and 0 |
| ihub.sanchiconnect.com | 6 | 0 |
| start.runwayincubator.com | 4 | 504 and 0 |
| connect.trise.tripura.gov.in | 4 | 0 |
| ecosystem.ihubup.com | 3 | 504 |
| community.ginserv.in, startupaffiliation.ciicies.in, nasscom.sanchiconnect.com, a direct-IP host | 1 each | |
| "Direct access is not allowed" (any host) | 5 | the app's own error state |

They arrive in bursts (for example 16:30–18:20 UTC on 4 Oct across many hosts at once), the signature of the tenants API timing out under load. Each domain's frontend is the same build, so
this is not a per-domain frontend defect.

Older releases are still in use as well, so the Saturday deploy did not reach every domain or every open tab: `022eafd6` (31 Jul; trise.tripura.gov.in, connect.acicvgu.com), `51eb6706` (18 Aug),
`dab63831` (3 Sep; trise, firstwings, supernova), `90bde7be0` (14 Sep; iiitdic, supernova, firstwings, isba, siic), `33244b02e` (19 Sep; iiitdic, runway, firstwings, supernova, sineedge),
`9dde12280` (25 Sep; trise, firstwings, supernova, hub.startupsingam, isba, ginserv, iiitdic), `e267a0303` (1 Oct; app.sanchiconnect.com).

## Root cause (two layers)
1. **Server side:** the tenants API times out under load. The cache and request coalescing is SAN-557 (`sanchiconnect-saas-tenants` `f74d37d`), committed but not deployed (a separate deployment).
2. **Client side (this issue):** `TenantService.getTenantDetails()` made one HTTP call with no retry, and `AppComponent.getTenantDetails()` treats any error as fatal ("Direct access is not allowed" state
   plus a fatal `tenant-verification-down` Sentry event). A transient 504 or network drop that would succeed a moment later took the whole site down for that visitor.

## Fix
New `shared/utils/http-retry.util.ts`: `isTransientHttpFault(err)` (status 0, 502, 503, 504) and `retryTransientHttp(retries = 2, baseDelayMs = 1500, jitterMs = 500)`, an RxJS `retry` with a delay
function that waits `baseDelayMs * attempt` plus jitter for a transient fault and rethrows anything else immediately. `getTenantDetails()` pipes it before `tap()`, so the dispatches only run on the
successful attempt. At most 3 attempts, about 5 s extra. The error that finally reaches `AppComponent` is unchanged.

## Not fixed (decision needed, no code)
Serving the last stored `brandDetails` when the call keeps failing (stale-if-error). It would keep returning visitors online through an outage, but could serve stale feature flags or maintenance
mode, which changes tenant-verification behaviour. Needs the product owner and dev lead.

## Risks
Up to 2 extra requests per failing visitor while the tenants API is struggling. Bounded by the retry count, backoff and jitter; SAN-557's server cache absorbs repeats once deployed.

## Contract impact
None. The tenant-verification request and response shape are unchanged; only how many times a transient failure is attempted. No flag, tenancy or auth change. Module specs updated: `src/app/core/module.spec.md`
(TenantService) and `src/app/shared/module.spec.md` (utilities).

## Verification
- A node script transpiled the real `http-retry.util.ts` and ran it against RxJS with real timers: 24 checks (transient and non-transient statuses, success not retried, 504 then success, 0 then 502 then
  success, backoff 1x then 2x base measured at 45 ms and 93 ms for a 40 ms base, exhaustion after 3 calls, 400/401/403/404/500 not retried, 504 then 404 stops, jitter bounded). All pass.
- Jasmine specs added: `shared/utils/http-retry.util.spec.ts` and four cases in `core/service/tenant.service.spec.ts`. **Karma cannot run in this repo at the moment** (unrelated specs fail to compile, SAN-1653),
  so these are compile-checked only: `tsc -p tsconfig.spec.json` reports 0 errors in these files (16 pre-existing errors elsewhere).
- `tsc --noEmit -p tsconfig.app.json` and `ngc` exit 0.

## Sentry
SC-SAAS-FRONTEND-26 stays **unresolved on purpose**: this reduces user impact but the cause is the tenants API. Close it after the tenants deploy (SAN-557) and a quiet period (SAN-1560 asks for third-party
verification and 48 h without events).

## Commit
sc-saas-frontend `e233de1af` on `ai_native_setup_aman`. Not deployed. The module-spec text for `core` and `shared` was committed in the same window inside `91a61c0e0`
(another session's docs commit swept those two working-tree edits into it); it is intact in HEAD.
