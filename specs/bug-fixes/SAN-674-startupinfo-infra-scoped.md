---
id: SAN-674
title: "startupinfoFault( ... 0 Unknown Error ) — re-confirmed infra-scoped (SAN-604)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-674
sentry:
  - SC-SAAS-FRONTEND-3M
repos: [frontend]
commit: "none — infra-scoped, re-confirmed prior conclusion"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-674 — re-confirmed infra-scoped failure

## Root cause
`startup.service.ts:96-113` (`getStartUpInfo()`), already-guarded status-0 passthrough. Matches prior
triage `specs/bug-fixes/SAN-604-thub-startupinfo-status-zero.md` — same tenant (thub.sanchidev.in),
same "0 Unknown Error", already concluded infra/tenant-deployment-scoped, no fixable frontend or
backend code bug found.

## Fix
No fix needed/possible — re-confirmed prior conclusion.

## Related
SC-SAAS-FRONTEND-49 (SAN-605, same tenant/pattern).

## Verification
Cross-referenced against the SAN-604 triage doc; same tenant, same signature.
