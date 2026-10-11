---
id: SAN-891
title: "bulkSanctionClaims logs an expected per-claim rejection at error level"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-891
sentry:
  - SC-SAAS-BACKEND-37
repos: [backend]
commit: sc-saas-backend@5bc7a77e
created: 2026-09-22
updated: 2026-09-22
---

# SAN-891 — bulkSanctionClaims log level

## Root cause

`operational-cost-reimbursement.service.ts`'s `bulkSanctionClaims()` deliberately processes each
selected claim independently — `assertSanctionable()` throws per-claim if it's not Under Process
(e.g. already sanctioned by someone else in the meantime), and the outcome is correctly reported to
the caller via the `results` array without aborting the batch. But the per-claim catch logged via
`.error`, which `SentryLoggerService`/`CaptureConsole` forwards to Sentry — same noise pattern
already fixed in SAN-410/SAN-466/SAN-587.

## Fix

Downgraded to `.debug`, matching the established precedent for designed, already-reported rejections.

## Blast radius

None — logging level only; the `results` array reporting is unchanged.

## Verification

`tsc --noEmit` clean; existing suite `operational-cost-reimbursement.service.spec.ts` (77 tests,
including the exact "reported as a per-claim FAILURE" case) still passes.

## Rollout

Committed and pushed `sc-saas-backend@5bc7a77e` to `ai_native_setup_aman` only, per explicit user
instruction (not `ai_native_setup` this round).
