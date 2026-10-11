---
id: SAN-809
title: "\"HTTP/1.1 Overhead\" performance issue on / — no code defect, no action needed"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-809
sentry:
  - SC-SAAS-FRONTEND-DK
repos: [frontend]
commit: "none — not a code defect"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-809 — Sentry performance category, not a JS error

## Root cause
Not a code defect — this is a Sentry performance-monitoring flag about HTTP/1.1 connection overhead on
the root route (`http_client` category), not an exception. No user-impact signal (0 users).

## Fix
No code change. Consider a Sentry inbound filter for this performance-issue category if it keeps
generating alert noise. An actual fix (e.g. HTTP/2 on the origin/CDN) would be an infra change outside
this repo's scope.

## Verification
Confirmed via Sentry issue category (`http_client`) that this is a performance flag, not an error.
