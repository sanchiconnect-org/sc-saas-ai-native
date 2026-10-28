---
id: SAN-2114
title: "Deleting a partner that still has users fails with FK 1451 — admin reported success and sent the raw SQL error to Sentry"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2114
sentry: [SC-SAAS-ADMIN-19]
repos: [admin]
related: [SAN-2122]
commit: admin@1b3774bf (branch ai_native_setup_vishali, pushed; shared with SAN-2122)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2114: delete_record never checked whether the delete happened

## Root cause
* 19: `SQL error 23000 (1451) in DELETE partners: … FOREIGN KEY ("partner_id") REFERENCES "partners"`, 3 events, `/ajax/spa_actions`.
* The generic `case "delete_record"` in `modules/ajax/spa_actions.php` deleted each record and then always answered `records_deleted`. When `users.partner_id` still pointed at the partner:
  * MySQL refused the delete;
  * `core/db.php reportQueryError()` sent the raw error to Sentry;
  * the operator was told "Deleted successfully", and the row faded out on the single-delete path.
* No "still has linked records" pattern existed anywhere in the repo.

## Fix
* `core/db.php`: new `expectErrors(array $codes)`. `reportQueryError()` skips any code the caller says it will handle itself.
* `spa_actions.php`: new `spaDeleteBlockedMessage()`.
  * It reads the linked table and column from MySQL's own 1451 text (restricted to `[A-Za-z0-9_]`) and counts the linked rows on the tenant's own connection.
  * The operator sees "This record still has N user account(s) linked. Remove or reassign them before deleting."
  * The delete loop marks 1451 as expected only for the loop and sorts records into deleted, blocked and failed.
  * When everything is deleted, the response is still `records_deleted`, exactly as before.
* `themes/default/html/table.php` (bulk) and `detail.php` show `data.message`, with the old text as fallback. The bulk path now hides the loader on error and reloads if some records were deleted.
* No cascade and no schema change: nothing linked is deleted or modified.

## Blast radius / existing-flow impact
Admin only, generic delete path. A delete that fails for any other reason used to report success; it now answers "could not be deleted" and is still reported to Sentry. That change is deliberate.

## Verification
* `php -l` (XAMPP PHP 8.2.12) → 0 on all 4 files
* `scripts/gates.sh`: platform, php-lint, auth-gates, ai-credit-writes, panel-hardening, sql-list-filters and xss-escapes all 0. composer, phpstan and phpcs → 127 because they aren't installed locally; CI runs them.
* Medoo resets `errorInfo` on every execute (`core/db.php:331`), so the per-record check is reliable.
* Not run against a DB. Manual check: delete a partner with users, one without, and a mixed bulk selection.
