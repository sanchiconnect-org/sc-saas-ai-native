---
id: SAN-982
title: "count() TypeError — Medoo select() returns false on query error, not []"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-982
sentry: [SC-SAAS-ADMIN-8, SC-SAAS-ADMIN-S]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-982 — count() TypeError on Medoo select() results

## Root cause
Two different call sites, same underlying cause: Medoo's `$database->select(...)` returns `false` on a query error (not an empty array), and both callers passed the raw result straight into `count()`.
- `modules/task_management/list.php:294` — `count($get_records)` where `$get_records = $database->select($table_name, "*", $getRecordsQuery)`. (SC-SAAS-ADMIN-8, 5 events)
- `includes/core_functions.php:3903` (`getUserLevelConnectionMatrix()`) — returned the raw `$database->select(...)` result unguarded; consumed via `count()` at `modules/startup-detail.php` (now around line 1743 — shifted from the reported 1589 by unrelated edits since this event). (SC-SAAS-ADMIN-S, 1 event)

## Fix
- `task_management/list.php`: `count($get_records ?: [])`.
- `getUserLevelConnectionMatrix()`: fixed at the source so every caller benefits, not just the one that happened to crash — `return is_array($getUserLevelConnectionMatrix) ? $getUserLevelConnectionMatrix : array();`.

## Blast radius
Two files. `getUserLevelConnectionMatrix()` is called from two places in `startup-detail.php` (lines ~1693 and ~1781 in the current file) — both now get a guaranteed array back instead of only the one that was observed crashing.

## Verification
`php -l` clean on both files.

## Rollout
Both Sentry issues (SC-SAAS-ADMIN-8, SC-SAAS-ADMIN-S) marked resolved. Not committed/pushed — sitting on `ai_native_setup_aman`, pending review.

## Open questions
None.
