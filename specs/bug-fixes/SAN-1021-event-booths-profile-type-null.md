---
id: SAN-1021
title: "event_booths insert never sets profile_type — NOT NULL violation"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1021
sentry: [SC-SAAS-BACKEND-B]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1021 — event_booths profile_type NOT NULL violation

## Root cause
`SC-SAAS-BACKEND-B` is the same Sentry short-ID that previously conflated an "Unknown column NaN" bug and a `startup_financials` FK-violation bug (SAN-478/892) under one issue due to weak fingerprinting on generic `QueryFailedError`s. Now that the fingerprint fix (SAN-478) is live, this short-ID correctly split into a genuinely new, third bug: `Column 'profile_type' cannot be null`, 198 events, production.

Same cross-repo pattern as SAN-892: the Sentry error is tagged `sc-saas-backend`, but the actual write is in `sc-saas-admin`, which writes to the shared tenant MySQL DB directly via Medoo. `sc-saas-admin/modules/events/edit/exhibitors.php`'s "saveBooth" handler builds its insert `$data` array without ever including `profile_type` — the column isn't even present in this file's own defensive `CREATE TABLE event_booths` guard, suggesting whoever built this admin feature wasn't aware the real production table has this column (added via the backend's `EventBoothsEntity`, `enum NOT NULL, default: 'startup'`). That TypeORM-level default never helps here since the admin's raw Medoo insert bypasses the backend/TypeORM entirely.

The separate "allocateBooth" handler in the same file already correctly sets `profile_type` in both its branches (existing stakeholder → their real `account_type`; custom stakeholder → posted value or `'startup'` fallback) — only the initial booth-creation insert was missing it.

## Fix
`sc-saas-admin/modules/events/edit/exhibitors.php`, "saveBooth" insert branch only: added `$data['profile_type'] = 'startup';` before the insert. Scoped to create only (not update) — the allocate handler is the one that should change this value afterward, not every booth edit.

## Blast radius
Single file, insert-only branch. No change to booth updates or the allocate/deallocate flows.

## Verification
`php -l` clean. No test suite exists for this repo.

## Rollout
Sentry issue marked resolved — genuine root-cause fix, not just observability.

## Open questions
None.
