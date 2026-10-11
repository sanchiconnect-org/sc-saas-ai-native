---
id: SAN-550
title: "AuthService.login crashes when getUserProfile() returns undefined"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-550
sentry:
  - SC-SAAS-BACKEND-26
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-550 — AuthService.login null profile crash

## Root cause

`auth.service.ts`: `getUserProfile()` (`app.utils.ts`) is a switch over `user.accountType` returning
`user.startup`/`user.investor`/etc. directly, with no fallback for an unset relation. `login()` then
read `userProfile.isRejected` unconditionally — any user whose account-type sub-profile relation
isn't loaded crashed the entire login request instead of proceeding.

## Fix

`auth.service.ts:179` — `userProfile.isRejected` → `userProfile?.isRejected`.

## Blast radius

None — a missing profile now means "not rejected" (falls through), matching the safe default; no
change for users who do have a loaded profile.

## Verification

`tsc --noEmit` clean; existing suite `auth-partner-scoping.spec.ts` (23 tests) still passes. No
dedicated regression test added for a 1-line guard.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
