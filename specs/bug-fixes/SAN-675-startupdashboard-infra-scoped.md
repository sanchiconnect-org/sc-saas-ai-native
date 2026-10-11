---
id: SAN-675
title: "startupDashboard( ... 0 Unknown Error ) — re-confirmed infra-scoped (SAN-605)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-675
sentry:
  - SC-SAAS-FRONTEND-49
repos: [frontend]
commit: "none — infra-scoped, re-confirmed prior conclusion"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-675 — re-confirmed infra-scoped failure

## Root cause
`startup-dashboard.service.ts:38-68` (`getStartUpCompleteness()`), already-guarded status-0
passthrough. Matches prior triage `specs/bug-fixes/SAN-605-thub-profile-completeness-status-zero.md`
— same tenant, same conclusion (infra-scoped, not fixable via shared source).

## Fix
No fix needed/possible.

## Related
SC-SAAS-FRONTEND-3M (SAN-604).

## Verification
Cross-referenced against the SAN-605 triage doc; same tenant, same signature.
