---
id: SAN-890
title: "checkServiceAlreadySubmitted crashes reading user.startup when the caller has no startup profile"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-890
sentry:
  - SC-SAAS-BACKEND-38
repos: [backend]
commit: sc-saas-backend@5bc7a77e
created: 2026-09-22
updated: 2026-09-22
---

# SAN-890 — checkServiceAlreadySubmitted null user.startup

## Root cause

`startup-kit.service.ts:249-264` reads `user.startup.incubationStageId` (twice) and
`user.startup.approvalStatus` with no guard — crashes whenever the caller's `user.startup` relation
is null (e.g. a team member without a directly-linked startup row), same shape as SAN-751/SAN-625.

## Fix

Added `?.` to all three unguarded accesses. Also updated `startup-kit/module.spec.md`'s Invariants
section, which explicitly documents this exact `canApply` check, to note the null-safety fix.

## Blast radius

None.

## Verification

`tsc --noEmit` clean. No existing test suite for `startup-kit.service.ts`.

## Rollout

Committed and pushed `sc-saas-backend@5bc7a77e` to `ai_native_setup_aman` only, per explicit user
instruction (not `ai_native_setup` this round).
