---
id: SAN-945
title: "/api/v1/certificates: 0 Unknown Error (network-level) unhandled — 3 call sites"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-945
sentry:
  - SC-SAAS-FRONTEND-EG
repos: [frontend]
commit: sc-saas-frontend@ebf12ba7 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-945 — unhandled getCertificates() failures (3 sites)

## Root cause
Found 4 total unguarded `profileService.getCertificates()` call sites across the codebase. 3 had no
error callback: `certificate-viewer-modal.component.ts`, `startup-public-profile-v2.component.ts`, and
`dashboard-v2.component.ts` (1 user, 2 events on this Sentry group). A network-level failure
(status 0) at any of them reached Sentry as an unhandled subscribe failure. The service itself already
toasts on failure before re-throwing.

## Fix
Converted all 3 sites to `.subscribe({ next: (res) => {...}, error: () => {} })`.

## Not in scope
A 4th call site, `acc-certificates.component.ts`, already had an error handler — left untouched here
and fixed separately under SAN-929 (same underlying Sentry group, different symptom: a 401 rather
than a network-level failure).

## Blast radius
None — purely additive error handling, no change to success-path behavior at any of the 3 sites.

## Verification
Re-read all 3 files after editing to confirm consistent `{next, error}` shape. No automated test
added — step 6 (tests-first) is blocked workspace-wide (no `guardian` skill); substituted a direct
code read.
