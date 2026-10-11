---
id: SAN-848
title: Rename sidebar nav link "Operational Cost" to "Schemes"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-848
repos: [frontend]
commit:
created: 2026-09-18
updated: 2026-09-18
---

# SAN-848 — rename sidebar nav link "Operational Cost" to "Schemes"

## Problem
Startup dashboard sidebar nav link showed "Operational Cost" (route `/operational-cost-reimbursement`); requested label was "Schemes".

## Fix
`sc-saas-frontend/src/app/shared/constants/navMenus.ts` — `operational-cost-reimbursement` menu entry: `title: 'Operational Cost'` → `title: 'Schemes'`. Route/id/page content unchanged, label-only.

Follow-up: `iconClass: 'fa fa-inr'` (rupee icon, fit "Operational Cost") → `iconClass: 'bi bi-award'` (fits "Schemes"), same entry.

## Verification
- `npx tsc --noEmit` — clean.
- No lint configured in this repo (per its CLAUDE.md).
- No regression test — static string label, not logic.
