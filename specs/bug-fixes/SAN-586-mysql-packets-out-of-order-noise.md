---
id: SAN-586
title: "mysql2 packets-out-of-order driver warning reaching Sentry as noise (local dev only)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-586
sentry:
  - SC-SAAS-BACKEND-27
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-586 — mysql2 driver warning Sentry noise filter

## Root cause

mysql2 logs `Warning: got packets out of order...` via `console.error` when a pooled connection is
reused after a stale/cancelled query — a driver-level protocol warning from local dev, not an
application defect. All observed events were `environment: local`. Same category as the
already-fixed SAN-506 (TypeORM DB connection retry noise).

## Fix

Added `isMysqlPacketOrderWarning()` to `instrument.ts`'s existing `scrubEvent`/`beforeSend` hook,
same pattern as SAN-506's `isTypeOrmDbRetry` — drops any event whose message starts with
`Warning: got packets out of order`.

## Blast radius

None — only affects this exact message shape.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
