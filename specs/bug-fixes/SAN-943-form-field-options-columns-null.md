---
id: SAN-943
title: "dynamic-forms: Cannot read properties of null (reading 'map')"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-943
sentry:
  - SC-SAAS-FRONTEND-EJ
repos: [frontend]
commit: sc-saas-frontend@32cd4182 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-943 — form-field.component.ts null options/columns

## Root cause
`form-field.component.ts` called `.field.options.map(...)` (1 site) and `.field.columns.map(...)`
(4 sites) across the checkbox/radio-grid/checkbox-grid/textbox-grid/numberbox-grid mapping branches,
with no guard against `options`/`columns` being null for some field configs (1 user, 4 events).

## Fix
Guarded all 5 call sites with `|| []` (`(this.field.options || []).map(...)`,
`(this.field.columns || []).map(...)`).

## Blast radius
None — a field config missing `options`/`columns` now maps to an empty selection list instead of
crashing.

## Verification
Re-read the file after editing to confirm all 5 sites use the same guard consistently. No automated
test added — step 6 (tests-first) is blocked workspace-wide (no `guardian` skill); substituted a
direct code read.
