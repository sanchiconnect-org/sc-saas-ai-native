---
id: SAN-1996
title: "foundersFault( Invalid access token ) on trise startup-information (SC-SAAS-FRONTEND-96) — release predates SAN-471 filter"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1996
sentry: [SC-SAAS-FRONTEND-96]
repos: [frontend]
related: [SAN-672, SAN-471, SAN-216, SAN-930, SAN-1925]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1996: foundersFault( Invalid access token )

## Investigation
* **Events (30 days):** 3 events, all on release `51eb6706` (2026-08-18): trise `/startups/edit/startup-information` (2026-10-18) and tallysolutions (2026-09-28).
* **Source:** `FoundersService.getFounders()` (`core/service/founders.service.ts:34`) warns on the expired-session 401.
* **What the user gets:** `AddTokenHeaderHttpRequestInterceptor` (`core/http-interceptor/add-token-header.http-request-interceptor.ts:86-91`) clears storage, toasts the backend message / "Session expired", and navigates to `/auth/login`. The user is not left on a broken edit page. This matches SAN-672's verdict: expected auth expiry.
* **The filter:** `src/main.ts` `HANDLED_HTTP_FAULT` (current line 269) drops a warning-level, exception-less message ending in `( Invalid access token )`. It was added by SAN-471 `2e1dd4dc7` (2026-08-20).
* **Ancestry:**
  * `git merge-base --is-ancestor 2e1dd4dc7 51eb6706` → **no**.
  * `2e1dd4dc7` on `origin/main` → yes.

## Fix
None needed.

## Blast radius / existing-flow impact
None (no change).

## Verification
Ancestry checks above.

## Recommended close
Close as deploy lag / expected condition. Trise and tallysolutions are still on a 2026-08-18 bundle (stale PWA, see SAN-1925).
