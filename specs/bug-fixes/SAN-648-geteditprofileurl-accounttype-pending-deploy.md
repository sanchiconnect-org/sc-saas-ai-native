---
id: SAN-648
title: "TypeError: Cannot read properties of null (reading 'accountType') in ProfileService.getEditProfileUrl — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-648
sentry:
  - SC-SAAS-FRONTEND-BH
repos: [frontend]
commit: "sc-saas-frontend@467e1979 (SAN-591), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-648 — profileData-null crash, already fixed

## Root cause
`ProfileService.getEditProfileUrl()` read `this.profileData.accountType` without checking `profileData`
was loaded yet.

## Fix
Already fixed in commit `467e1979` (SAN-591, 2026-09-04) — added
`if (!this.profileData) { return profileEditPageUrl; }` at `profile.service.ts:492-494`. Fix postdates
this issue's last-seen (2026-08-28) — pending deploy given prod lag.

## Verification
Confirmed the guard precedes the `.accountType` read.
