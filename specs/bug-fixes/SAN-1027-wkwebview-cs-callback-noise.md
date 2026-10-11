---
id: SAN-1027
title: "iOS in-app browser (null)('cs_<UUID>') Sentry noise"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1027
sentry: [SC-SAAS-FRONTEND-GC]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1027

## Root cause (ENV_ERROR)
WKWebView host app evaluates its own injected `cs_<UUID>` callback; zero first-party frames; no `cs_` callback in codebase. Same class as SAN-503.

## Fix
`src/main.ts` beforeSend regex filter for exactly that message shape.

## Existing-flow check
Sentry-only; plain `(null) is not a function` still reports.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
