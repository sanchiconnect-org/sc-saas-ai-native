---
id: SAN-2110
title: "startup-information save on a 504: SaveStartUpInfo effect crashes reading err.error.message of null"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2110
sentry: [SC-SAAS-FRONTEND-3X, SC-SAAS-FRONTEND-J4, SC-SAAS-FRONTEND-J5, SC-SAAS-FRONTEND-J6, SC-SAAS-FRONTEND-J7]
repos: [frontend]
related: [SAN-474, SAN-1669, SAN-1040, SAN-2120]
commit: frontend@3cf10df2d (branch ai_native_setup_vishali, pushed)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2110: a regression hidden in a merge

## Root cause
* 3X: 23 events / 18 users, regressed, last on hub.startupsingam.com (release `218edca78`). J4–J7 are the console.warn echoes of the same 504s (same trace).
* `src/app/core/state/startup/startup.effect.ts:60` read `err.error.message`. A load-balancer 504 has no body, so `err.error` is null and the `catchError` itself threw.
* SAN-474 (`e10a960c9`, 08-20) had already changed this line to `httpFaultMessage(err)`. Merge PR #1807 (`3d4e5f857`, 09-08, from `ai_native_setup_mahima`) put the old line back. The regression is on main and every branch, so it is not deploy lag.

## Fix
`startup.effect.ts:60` uses `httpFaultMessage(err)` again, the shared helper the four sibling effects in the file already use. No other live `Fault(err.error.message)` remains in `core/state`.

J4–J7 (`savefounderInfo( HTTP 504 )` etc.) are left as they are. Whether to filter those echoes is the SAN-2120 decision.

## Blast radius / existing-flow impact
Frontend only. The fault message now always has a value instead of throwing. No API, flag or tenant-scoping change.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → 0
* `npm run gates`: openapi-types 0, loader-floor 0, build 0, unit-tests 0 (1338/1338), test-floors 0
* No new automated test (guardian skill absent). Manual: block the save request with a 504 and check for a toast, no TypeError, and that a second save still dispatches.
