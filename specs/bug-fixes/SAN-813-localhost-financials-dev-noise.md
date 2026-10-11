---
id: SAN-813
title: "localhost:4200 financials-information 500 — dev-only traffic, no code defect"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-813
sentry:
  - SC-SAAS-FRONTEND-Y
repos: [frontend]
commit: "none — not a code defect"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-813 — localhost dev-server traffic, not production

## Root cause
Not a code defect — the URL is `http://localhost:4200/...`, the Angular CLI dev server port, so this
is local development traffic (a developer's own machine hitting their local backend proxy), not
production. Not representative of real end-user impact despite the "11 users" count (each is likely a
distinct developer's local Sentry-DSN-enabled dev build).

## Fix
No code change. Consider a Sentry inbound filter for `localhost:4200` origins if this keeps crowding
out real production signal (same recommendation as SAN-446's "stop ingesting dev-build noise" effort).

## Verification
Confirmed the culprit URL is `localhost:4200`-scoped, not a production host.
