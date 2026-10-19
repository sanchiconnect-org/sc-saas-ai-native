---
id: SAN-1928
title: "getProfileDetails / investorDashboard \"Something went wrong. Please try again.\" (SC-SAAS-FRONTEND-F2 / G0)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1928
sentry: [SC-SAAS-FRONTEND-F2, SC-SAAS-FRONTEND-G0]
repos: [backend, frontend]
related: [SAN-1923, SAN-1930]
commit: none — no code defect found; see Investigation
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1928: the generic fault text is the frontend's fallback, not a backend error

## Investigation
* **F2:** `getProfileDetails Fault( Something went wrong. Please try again. )`, 10 events / 8 users, app.sanchiconnect.com `/startups/edit/financial-details`, release `3fe291506`, last event 2026-10-14 06:47 UTC.
* **G0:** `investorDashboard( Something went wrong. Please try again. )`, 1 event, sineedge.sineiitb.org `/investors/dashboard`.
* **Where the text comes from:** it is the default fallback of the frontend's `httpFaultMessage()` (`sc-saas-frontend/src/app/shared/utils/http-fault.util.ts:33-58`). The fallback is used only when the error body has no `error` or `message` field and isn't a string.
* **Not a backend 500.** The backend's `src/core/exceptions/global-exception.filter.ts` always returns `{ status_code, message, error }` with a non-empty `message`, so even an unhandled TypeError reaches the client with its own text.
* **What these events were:** network-level failures. Status 0 from being offline, an aborted request, or a gateway 502/504 without CORS headers. They are on the same day as the BACKEND-5S / FRONTEND-2W degradation (2026-10-14, SAN-1923).
* **Endpoints:**
  * `getProfileDetails` → `GET api/v1/users/profile` → `UserService.getUserProfile` (`user.service.ts:215`);
  * `investorDashboard(` is logged by both `GET investors/dashboard` and `GET investors/organization/profile_completeness` (`investor-dashboard.service.ts:49`, `:111`).

## Fix
None. The status-0 warning noise is handled by SAN-1930's recommended `beforeSend` filter.

## Blast radius
None, no code changed.

## Open
* **Separate latent defect:** `getUserProfile` (`user.service.ts` ~312-370) reads `userProfile.companyName` / `.name` without a null check, so an account whose profile row is missing gets a 500.
* Not fixed here: the fix changes behaviour for orphaned accounts (a 404 logs the user out on the frontend). It needs its own ticket and a decision.
