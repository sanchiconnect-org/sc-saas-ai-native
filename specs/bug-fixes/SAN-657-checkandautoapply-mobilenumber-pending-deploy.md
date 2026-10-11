---
id: SAN-657
title: "TypeError: Cannot read properties of undefined (reading 'mobileNumber') in checkAndAutoApply — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-657
sentry:
  - SC-SAAS-FRONTEND-6A
repos: [frontend]
commit: "sc-saas-frontend@f0484689 (SAN-482), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-657 — profileDetails-undefined crash, already fixed

## Root cause
`ProgramPublicApplyComponent.checkAndAutoApply()` read `this.profileDetails.mobileNumber` before the
profile store had emitted.

## Fix
Already fixed in commit `f0484689` (SAN-482, 2026-08-24) — added
`if (!this.profileDetails) { return }` guard at `program-public-apply.component.ts:216-218`. Fix
predates this issue's window (2026-08-27) by 3 days — consistent with prod deploy lag, not a live
regression.

## Related
SC-SAAS-FRONTEND-79 (SAN-665, same underlying fix, different component reusing the pattern).

## Verification
Confirmed the guard precedes the `.mobileNumber` read.
