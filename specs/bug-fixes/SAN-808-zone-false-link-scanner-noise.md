---
id: SAN-808
title: "reading 'false' in zone addEventListener — mail link-scanner bot noise"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-808
sentry: [SC-SAAS-FRONTEND-3G]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-808

## Root cause (ENV_ERROR)
All events: headless Chrome 126 from Azure IPs (mail link scanner) whose injected script calls `__zone_symbol__addEventListener` directly, so zone reads `zoneSymbolEventNames[type]['false']` of undefined.

## Fix
`src/main.ts` beforeSend drops events with exactly that message AND a `__zone_symbol__addEventListener` frame.

## Existing-flow check
Sentry-only, no runtime change; same message with other frames still reports.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
