# SAN-1866 — 3rdparty gateway reports bare-root probes (`Cannot GET /api`) to Sentry

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1866 (Sentry SC-SAAS-3RDPARTY-WEBSERVICES-1)
- **Repo:** sc-saas-3rdparty-webservices · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** NOISE (unmatched-route 404 reported as an error)

## Evidence
SC-SAAS-3RDPARTY-WEBSERVICES-1: 929 events, all `NotFoundException` with a message of the form `Cannot GET /api` / `Cannot GET /` (bare root). The gateway has no route at `/` or `/api`, so Nest answers 404.
`GlobalExceptionFilter` called `Sentry.captureException` for every exception it caught, including these.

## Root cause (observed vs inferred)
- **Observed:** `src/core/exceptions/global-exception.filter.ts` captured every exception unconditionally; the 404s are for the bare root only.
- **Inferred:** the caller is an ALB/ECS health check or a scanner hitting the root. It was **not identified** (no source IP or User-Agent was checked).

## Fix
`global-exception.filter.ts`: new `isUnmatchedRoute404(exception)` (a `NotFoundException` whose message matches `^Cannot (GET|HEAD) /(api/?)?$`); `Sentry.captureException` is skipped only for that. Logging and the 404 response are unchanged.
The match is deliberately narrow. A first draft used a broad "any `Cannot METHOD`" pattern and was narrowed because it would have hidden `Cannot GET /api/v1/video-sdk/meetings//sessions`, the empty-id symptom of SAN-421/422.
Still captured: deeper unmatched routes, 5xx, provider errors, service 400s. The regex was checked on 10 sample messages.

## Not fixed
The probing caller itself (health-check path not changed or confirmed). No route was added at `/`.

## Contract impact
None. Responses are unchanged; only what reaches Sentry changes. No flag, auth or tenant-scoping change (the gateway is stateless).

## Verification
`tsc` clean; regex checked on 10 messages. No automated test added (guardian skill blocked workspace-wide). Not run against a deployed gateway or Sentry.

## Commit
sc-saas-3rdparty-webservices `0fbd5ca` on `ai_native_setup`. Pushed, not deployed.

## Sentry
The group will stop receiving events only after a deploy; existing events remain. Reopen if it recurs on a build containing `0fbd5ca`.
