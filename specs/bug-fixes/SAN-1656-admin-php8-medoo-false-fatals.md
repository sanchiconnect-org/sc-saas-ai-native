# SAN-1656 — Admin fatals on PHP 8: Medoo `select()` false, non-numeric `number_format`, empty `tmp_name`

- **Linear:** SAN-1656 (SC-SAAS-ADMIN-G, -10, -J, -M, -N)
- **Repo:** sc-saas-admin · **Assignee:** Aman kabra · **Classification:** CODE_ERROR

## Problem
Medoo `select()` returns `false` (not `[]`) when a query fails, and PHP 8 made `count()`/`foreach`/`number_format()` on the wrong type fatal.
- G: `fetchProgramData()` — `foreach`/`count()` on a failed select or a non-array `json_decode` result.
- 10: `modules/table.php` — `count($get_records)` after a failed select.
- J: `modules/facilities/dashboard.php` — unchecked `select()` results `count()`ed by the template.
- M: `startup-detail.php` — `number_format()` given non-numeric strings (empty, `1,00,000`).
- N: `settings_management.php` — `mime_content_type('')` when a file name is present but the upload failed (empty `tmp_name`).

## Fix
Type guards at each site (a failed select is treated as an empty result, and the DB error is logged where it was not), a tolerant
`safe_number_format($value, $decimals = 0)` in `includes/core_functions.php` (wrapped in `function_exists`) used at all 8 call sites, and an
upload-error check before `mime_content_type`. No success-path change.

## Not fixed
The root cause — `PDO::ERRMODE_SILENT` making a failed query read as an empty result — is SAN-1631 (Mahima Sharma, Backlog).

## Contract impact
None. Admin-only; no API, flag, tenancy (per-tenant DB selection untouched) or auth change.

## Verification
`php -l` clean on all 6 files (PHP 8.2); `safe_number_format()` run against 9 inputs. The other guards are plain type checks and were not run
against a database or in a browser. No automated test (none exists in this repo).

## Commit
sc-saas-admin `9990ccce` on `ai_native_setup_aman`. Not deployed.
