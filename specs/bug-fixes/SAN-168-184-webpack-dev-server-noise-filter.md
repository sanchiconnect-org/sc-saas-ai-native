---
id: SAN-168..184
title: "webpack-dev-server compile warnings flooding Sentry — filtered at ingestion"
type: bug-fix
status: done
linear: [SAN-168, SAN-169, SAN-170, SAN-171, SAN-172, SAN-173, SAN-174, SAN-175, SAN-176, SAN-177, SAN-178, SAN-179, SAN-180, SAN-181, SAN-182, SAN-183, SAN-184]
sentry: [SC-SAAS-FRONTEND-21, -20, -1Y, -1X, -1W, -1V, -1T, -1S, -1R, -1Q, -1P, -1N, -1M, -1K, -23, -22, -1Z]
repos: [frontend]
commit: sc-saas-frontend@<pending, branch ai_native_setup_aman>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-168..184 — webpack-dev-server noise filter

## Root cause
17 separate Linear tickets, one per Sentry issue, all `[webpack-dev-server] WARNING`/`Warnings while compiling.` messages with culprit `http://localhost:4200/...`. `captureConsoleIntegration({levels:['warn']})` in `main.ts` forwards every `console.warn` call to Sentry, including webpack-dev-server's own compile-warning logging during `ng serve`. webpack-dev-server only exists inside a local dev-server process — it is never bundled into a deployed build — so any event with this message prefix can only originate from someone's local machine, regardless of the `environment` tag it happens to carry (confirmed: today's `environment:local` events are 100% `localhost:4200`).

## Fix
Added an early `beforeSend` check in `sc-saas-frontend/src/main.ts`: any event whose `message` starts with `[webpack-dev-server]` is dropped (`return null`) before any other processing. Same pattern as the existing scrub filters already in that function.

## Blast radius
`sc-saas-frontend`, `main.ts` only. No application behavior change — purely a Sentry-side ingestion filter. Zero risk of dropping a real production event: the prefix is impossible outside a dev-server process.

## Verification
`npx tsc --noEmit -p tsconfig.app.json` clean.

## Rollout
Not resolving the 17 Sentry issues themselves (they're historical, already stale) — the fix prevents new ones. Linear tickets reassigned Nirmal Singh → Aman kabra; recommend closing all 17 as "won't recur" once this ships.

## Open questions
None.
