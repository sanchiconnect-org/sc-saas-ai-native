---
id: SAN-927
title: set-availability-modal crashes reading 'times' off a malformed day/date row
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-927
sentry:
  - SC-SAAS-FRONTEND-FT
repos: [frontend]
commit: sc-saas-frontend@13731806 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-927 — set-availability-modal.component.ts unguarded d.times.forEach

## Root cause
`set-availability-modal.component.ts` called `d.times.forEach(...)` at 5 sites (load path for
days/dates, save path for days/dates, and the new-date-form path) with no guard against a day/date
row missing a `times` array (1 user, 1 event).

## Fix
Guarded all 5 call sites with `(d.times || []).forEach(...)`.

## Blast radius
None — a row with no `times` now behaves as if it had zero time slots, instead of crashing the whole
availability load/save flow.

## Verification
Re-read the file after editing to confirm all 5 sites use the same guard consistently. No automated
test added — step 6 (tests-first) is blocked workspace-wide (no `guardian` skill); substituted a
direct code read.
