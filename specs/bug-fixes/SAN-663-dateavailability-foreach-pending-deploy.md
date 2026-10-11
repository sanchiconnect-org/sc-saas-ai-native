---
id: SAN-663
title: "Uncaught (in promise): dateAvailability.forEach is not a function — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-663
sentry:
  - SC-SAAS-FRONTEND-7P
repos: [frontend]
commit: "sc-saas-frontend@5b6385cc (SAN-596), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-663 — non-array API response crash, already fixed

## Root cause
`common-methods.ts`'s `calculateSlots()` called `dateAvailability.forEach(...)` assuming an array, but
a non-array API response could reach it.

## Fix
Already fixed in commit `5b6385cc` (SAN-596, 2026-09-04, for sibling issue SC-SAAS-FRONTEND-7A) —
added `const dateAvailabilityList = Array.isArray(dateAvailability) ? dateAvailability : [];
dateAvailabilityList.forEach(...)` at `common-methods.ts:300-301`. This issue's last-seen (6d ago)
predates that fix — pending deploy given prod lag.

## Verification
Confirmed the guard covers this exact call site.
