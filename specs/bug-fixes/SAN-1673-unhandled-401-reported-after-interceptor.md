# SAN-1673 — unhandled HTTP 401 re-reported to Sentry after the interceptor already handled the session

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1673 (Sentry SC-SAAS-FRONTEND-2J, 1,038 users, 2,683+ events, reopens after every resolve)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** NOISE (expected condition reported as a defect)

## Problem
`Error: Http failure response for https://api.<tenant>/api/v1/<endpoint>: 401 OK`, unhandled, mechanism `angular`, still firing on the Saturday build `bcf88383d` (trise, supernova, nemecosystem, firstwings) across
`dashboards/user`, `connections`, `connections/requests/received`, `community-wall/posts/me/stats`, `mentorship/stats`.

## Root cause
`AddTokenHeaderHttpRequestInterceptor` handles a 401 completely (clears storage, toasts "Session expired", logs out, navigates to `/auth/login`; only a background auto-save 401 is silent, by design) and re-throws.
A caller with no error handler lets the `HttpErrorResponse` reach Angular's `ErrorHandler`, which reports an expired session as an unhandled error. SAN-471 filtered only the `console.warn` path. The group is a catch-all
for every unhandled `Http failure response`, which is why it reopens whichever endpoint fires first.

## Fix
`src/main.ts` `beforeSend`: drop an exception whose value matches `/^Http failure response for \S+: 401 /`. 401 only. 403 is left alone because a `SKIP_FORBIDDEN_REDIRECT` request is handled by its own caller and
the interceptor does not toast it; 0, other 4xx and 5xx are left alone because they can mean a missing handler or a real outage.

## Not fixed
The callers without an error handler. Each endpoint in the group still lacks one; the user experience is correct (the interceptor handles it), only the Sentry report was wrong. The 404s in the same group (one user,
all endpoints 404 in the same second) are a tenant routing problem and remain open.

## Contract impact
None. Sentry filtering only; no API, flag, tenancy or auth change; the interceptor is untouched.

## Verification
A node check of the real pattern: 5 real 401 titles dropped (`dashboards/user`, `connections`, `requests/received`, `community-wall/.../stats`, a `401 Unauthorized`), 9 others kept (404, 400 mark-read, 403, status 0,
504, 500, a URL containing `401`, a non-HTTP message, a type-prefixed message). 14/14. `tsc --noEmit` and `ngc` exit 0. No automated test added (none for main.ts).

## Commit
sc-saas-frontend `bd95b012c` on `ai_native_setup_aman` (module specs: `91a61c0e0`). Not deployed.
