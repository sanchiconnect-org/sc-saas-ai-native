---
id: SAN-942
title: "[Sentry] startupDashboard reports-page forEach crash — likely backend-origin (136 events, 48 users)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-942
related: SAN-959
sentry:
  - SC-SAAS-FRONTEND-EW
repos: [frontend]
commit: none (investigation-only ticket, no frontend code change)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-942 — investigation: startupDashboard forEach crash traced to backend (SAN-959)

## Investigation
The `startupDashboard(...)` console.warn label only exists in `startup-dashboard.service.ts`'s two
`catchError` blocks, and neither call site nor its consuming NgRx effect contains a `.forEach()`.
For the logged text to be a raw JS `TypeError` rather than a normal HTTP-failure string, the
backend's JSON error body must have carried an unhandled Node exception message verbatim — i.e. a
server-side crash whose raw message leaked through instead of being sanitized.

## Root cause (confirmed, backend)
`StartupRepository.getStartupProfileCompletenessReport()` — see [[SAN-959]] for the full root cause
and fix. Summary: an unguarded `.forEach()`/`.some()` on a relation array that a multi-collection
TypeORM join can leave `undefined` for some rows, with no try/catch around the call, so the raw
error reached the client.

## Outcome
No frontend code change needed under this ticket. Backend fix filed and applied under SAN-959
(`Repo: Backend`, uncommitted, pending user review).
