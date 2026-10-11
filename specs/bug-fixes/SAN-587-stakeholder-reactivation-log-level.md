---
id: SAN-587
title: "Stakeholder-reactivation skip logged at warn instead of debug"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-587
sentry:
  - SC-SAAS-BACKEND-2H
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-587 — stakeholder reactivation skip log level

## Root cause

`payment.repository.ts`: on membership renewal, re-activation is intentionally skipped when the
stakeholder's approval status isn't `approved`/`limited_access` — correct, designed behavior. Logged
at `.warn`, which `CaptureConsole`/`SentryLoggerService` forwards to Sentry as noise, same pattern
already fixed in SAN-410/SAN-466.

Recurred once more (a different partner id) 10+ days after this fix shipped, confirming the deploy
gap rather than a broken fix.

## Fix

Downgraded to `.debug`, matching the established precedent for designed-skip logging. Left the
sibling "Missing profileId for membership..." warn untouched — that one is a genuine data anomaly,
not a designed skip.

## Blast radius

None — logging level only.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
