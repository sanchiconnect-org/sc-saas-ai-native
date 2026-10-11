---
id: SAN-892
title: "startup_financials FK violation on funding_stage_id — root cause was sc-saas-admin, not backend"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-892
sentry:
  - SC-SAAS-BACKEND-B
repos: [admin]
commit: sc-saas-admin@ef1d46b9
created: 2026-09-22
updated: 2026-09-22
---

# SAN-892 — CSV import funding_stage_id FK violation

## Investigation

Initially filed against `sc-saas-backend` (this Sentry short ID, "B", previously covered an unrelated
already-fixed bug, SAN-405 — Sentry reuses group IDs on this project, same pattern seen with "C").
Traced every `fundingStageId` writer in the backend:

- `StartupService.editFinancials()` → validates via `FundingStagesRepository.checkFundingStageIdExist()`
  (`isActive: true`) before calling `updateFinancialsByStartupId()` — the only caller of that method.
- `AuditedUpdateService.update()` confirmed to run a genuine partial-column SQL `UPDATE`, not a stale
  full-entity re-save.

None of it could produce this FK violation — the backend's write path is validated and safe.

## Root cause (actually in sc-saas-admin)

`sc-saas-admin/modules/csv/import.php`'s bulk startup CSV import (~line 634) inserts
`startup_financials` directly via Medoo. A name→id resolution with auto-create fallback exists
earlier in the same import pass (~lines 413-433) and looks correct on its face, but something in
that two-pass row-building process was still letting an invalid/stale `funding_stage_id` reach the
insert, crashing the whole CSV row on the FK constraint — 293 occurrences in production.

## Fix

Added a re-verification directly at the insert site: look the id up in `funding_stages` again
immediately before inserting, and null it out if it no longer exists — rather than trusting the
earlier resolution unconditionally. Same protective pattern already used for `revenue_stage` two
lines above it in the same file.

## Blast radius

None — only prevents an invalid id from reaching the insert; a genuinely valid id is unaffected.

## Verification

`php -l` clean. No test suite in this repo (PHP, no npm build/test/CI per its own CLAUDE.md).

## Rollout

Committed and pushed `sc-saas-admin@ef1d46b9` to `ai_native_setup_aman` only, per explicit user
instruction (not `ai_native_setup` this round).

## Open questions

The exact trigger inside the two-pass row-building process (lines ~413-433) that let a stale id
through was not pinned down with certainty — the fix is a defensive backstop at the insert site
rather than a confirmed single root cause.
