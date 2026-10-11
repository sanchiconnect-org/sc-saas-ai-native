---
id: SAN-889
title: "findRequiredFields crashes on multi-value form sections with no fields array — 1,543 events, escalating"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-889
sentry:
  - SC-SAAS-BACKEND-36
repos: [backend]
commit: sc-saas-backend@5bc7a77e
created: 2026-09-22
updated: 2026-09-22
---

# SAN-889 — findRequiredFields multi-value section crash

## Root cause

`app.utils.ts`'s `findRequiredFields()`: for a form section with `multi_value` truthy and a positive
`multi_value_minimum`, the code unconditionally did `sectionData.fields.forEach(...)` — nothing
guaranteed `sectionData.fields` exists for a multi-value section. Any custom form with such a
section crashed `getStartupProfileCompleteness()` on every call — 1,543 events since 2026-09-15,
escalating, the highest-volume issue found in this triage round.

## Fix

Added `sectionData.fields && sectionData.fields.length` to the existing condition before iterating,
same guard style already used one level up (`formData.fields && formData.fields.length`).

## Blast radius

None — sections without a `fields` array are now skipped instead of crashing the whole
profile-completeness check.

## Verification

`tsc --noEmit` clean project-wide. No existing test suite for `app.utils.ts`.

## Rollout

Committed and pushed `sc-saas-backend@5bc7a77e` to `ai_native_setup_aman` only, per explicit user
instruction (not `ai_native_setup` this round).
