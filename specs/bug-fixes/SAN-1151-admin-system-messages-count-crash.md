# SAN-1151 — count() TypeError on $this->systemMessages (admin dashboard)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1151
- **Repo:** sc-saas-admin · **Type:** Bug · **Priority:** Medium · **Assignee:** Sandeep
- **Classification:** CODE_ERROR

## Problem
Sentry `SC-SAAS-ADMIN-Q` — `TypeError: count(): Argument #1 ($value) must be of type
Countable|array, false given`, crashing the admin dashboard homepage. 3 events since
2026-09-07, production.

## Root cause
Third uncovered call site of the same defect class already fixed twice under SAN-982: Medoo's
`$database->select(...)` returns `false` (not `[]`) on a query error. `modules/index.php:197`
passes that result straight into `$tpl->systemMessages` with no guard, consumed unguarded at
`themes/default/html/index.php:661` (`count()`) and lines 671/1965 (`foreach`).

## Fix
`modules/index.php:198`:
```php
$tpl->systemMessages = $getSystemMessages ?: [];
```
Source-level guard (matches SAN-982's `getUserLevelConnectionMatrix()` fix) — all 3 consuming
sites in the template are covered without touching them individually.

## Verification
- `php -l modules/index.php`: clean
- No test framework in this repo (per its CLAUDE.md) — step 3 of the bug-fix loop skipped, noted
  rather than bootstrapping test infra as a side effect

## Commit
None yet — uncommitted, awaiting review.
