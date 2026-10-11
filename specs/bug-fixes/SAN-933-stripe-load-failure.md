---
id: SAN-933
title: Failed to load Stripe.js on community.ginserv.in — unguarded loadStripe()
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-933
sentry:
  - SC-SAAS-FRONTEND-2C
repos: [frontend]
commit: sc-saas-frontend@a2f2247e (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-933 — checkout.component.ts unguarded Stripe.js load

## Root cause
`checkout.component.ts:241` called `await loadStripe(stripeKey || '')` with no try/catch. A CDN or
network failure loading Stripe.js (66 users, 76 events) crashed checkout with an unhandled rejection
instead of failing gracefully.

## Investigation note
Also checked and corrected an old assumption in SAN-447 (a prior "Stripe loads on every page"
hypothesis) — the only live call site found is this user-initiated checkout path; a second
Stripe-loading component exists in the codebase but is dead/unrouted. Flagged on SAN-447 directly
rather than silently leaving a stale hypothesis on record.

## Fix
Wrapped `await loadStripe()` in try/catch. On failure: stop the checkout loader, show a toast
("Stripe is unavailable right now, please try another payment method"), and return before attempting
payment creation.

## Blast radius
None on the success path. Failure path changes from an uncaught crash to a controlled toast + early
return — strictly safer.

## Verification
Re-read the file after editing to confirm the injected `toastAlertService`/`ngxLoader` and `Stripe`
type were reused rather than introduced new. No automated test added — step 6 (tests-first) is
blocked workspace-wide (no `guardian` skill); substituted a direct code read.
