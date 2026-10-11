---
id: SAN-1018
title: "metrics/all 403 Forbidden unhandled"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1018
sentry: [SC-SAAS-FRONTEND-74]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1018

## Root cause (CODE_ERROR)
`metricsService.getMetrics()` subscribers without error callback: public-layout-sidebar, growth-matrics, growth-matrics-print. 403 already toasted by service/interceptor.

## Fix
Error callbacks added (growth-matrics also resets `loading`).

## Existing-flow check
Success paths untouched. Whether this role should get 403 on metrics/all is a backend permission question — not changed.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
