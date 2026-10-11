---
id: SAN-938
title: "reading 'accountType' of undefined — events-calender profileData race"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-938
sentry:
  - SC-SAAS-FRONTEND-FP
  - SC-SAAS-FRONTEND-FH
  - SC-SAAS-FRONTEND-FG
repos: [frontend]
commit: sc-saas-frontend@b76ef5d7 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-938 — events-calender.component.ts profileData race

## Root cause
`events-calender.component.ts:265,296` read `this.profileData.accountType` in the
`allowedUserTypesToBook` filter. `profileData` can still be undefined if the platform-events response
resolves before the separately-loaded profile data does (4 users, 6 events combined across the 3
merged Sentry groups).

## Fix
Changed both sites to `this.profileData?.accountType`, matching the null-safe style already used
elsewhere in this component.

## Blast radius
None — a filter running before profile data loads now evaluates `undefined` (excludes the event from
the filtered set) instead of crashing, matching how the rest of the component already handles this
race.

## Verification
Committed in isolation from the unrelated SAN-941 fix that also touches this same function (see that
ticket's doc) — the two changes were split into separate commits so each is independently reviewable.
No automated test added — step 6 (tests-first) is blocked workspace-wide (no `guardian` skill);
substituted a direct code read.
