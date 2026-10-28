---
id: SAN-2020
title: "PowerPitch create-session fails with Maximum number of redirects exceeded: dev host 301-loops to itself"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2020
sentry: [SC-SAAS-BACKEND-5W, SC-SAAS-BACKEND-59]
repos: [backend]
related: []
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2020: dev-api.videopitchrecorder.com redirects to itself

## Investigation
* Sentry events:
  * BACKEND-59: 8 events from 2026-10-07 to 2026-10-22, status regressed.
  * BACKEND-5W: 2 events with `httpStatus=undefined` on URL `https://dev-api.videopitchrecorder.com/api/v1/externals/create-session`.
  * Both come from a dev host (`environment: local`).
* Call path: `PowerPitchController.connectToPowerPitchForCallForApplications` → `PowerPitchService` → `PowerPitchExternalService.createSession`.
* `curl -sI` on 2026-10-26 returned `301` with `Server: cloudflare` and `Location: https://dev-api.videopitchrecorder.com:443/api/v1/externals/create-session`, which is the same URL. `HEAD /` and `OPTIONS` loop the same way, so the whole host loops.
* The backend builds the URL correctly, already over https (`power-pitch-external.service.ts:26-31` and `:106-107`).

## Root cause
Cloudflare "Flexible SSL" combined with an origin that forces HTTP→HTTPS on the PowerPitch dev host. This is not SanchiSaaS code. `../SanchiPowerpitch` is not cloned here, so I couldn't inspect the origin config.

## Fix
None in code. I considered setting `maxRedirects: 0` on the call, which would give a clearer "HTTP 301" error. I rejected it because it would break any environment whose base URL legitimately 307/308-redirects.

## Blast radius / existing-flow impact
None, and invariant #6 is untouched. While the loop lasts, every `/v1/externals/*` call from dev fails, including `domain-registry-sync.service.ts:58`.

## Verification
The `curl -sI` evidence above.

## Ops follow-ups
For the PowerPitch/infra owner:
1. Set the Cloudflare SSL mode for `videopitchrecorder.com` to Full or Full (strict). The alternative is to make the origin honour `X-Forwarded-Proto` / `CF-Visitor`.
2. Check that `curl -sI <url>` returns a non-3xx status and that "connect to PowerPitch" works on dev.
