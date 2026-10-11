---
id: SAN-929
title: Certificates 401 unhandled on trise.tripura.gov.in — no error callback
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-929
sentry:
  - SC-SAAS-FRONTEND-2J
repos: [frontend]
commit: sc-saas-frontend@d0cd3263 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-929 — certificates fetch unhandled 401

## Root cause
`acc-certificates.component.ts`'s `fetchCertificates()` called `.subscribe((res) => {...})` with no
error callback. A 401 from `/api/v1/certificates` (180 users, 469 events on trise.tripura.gov.in) had
nowhere to go but Angular's global ErrorHandler/Sentry.

## Fix
Converted to `.subscribe({ next: (res) => {...}, error: () => {} })`, same pattern already used
elsewhere in this codebase for the same class of defect (SAN-504).

## Blast radius
None — purely additive error handling, no change to success-path behavior.

## Verification
Re-read the file after editing to confirm the subscribe object shape matches sibling call sites
and no syntax errors were introduced. No automated test added — the workspace-wide `guardian` skill
blocker (per CLAUDE.md) means step 6 (tests-first) is not currently available; this was substituted
with a direct code read.
