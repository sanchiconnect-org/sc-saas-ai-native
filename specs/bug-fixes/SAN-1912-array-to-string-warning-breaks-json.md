# SAN-1912 — "Array to string conversion" warning in front of the JSON breaks Move to Round and drafts Move to Submitted

Linear: https://linear.app/sanchiconnect/issue/SAN-1912 · Repo: `sc-saas-admin` · Assignee: Sandeep
Classification: **CODE_ERROR** (regression from SAN-1890)

## Problem
Single "Move to Round" (row button) and drafts "Move to Submitted" return success but the page does not reload.

## Evidence
- SAN-1890 (deployed 2026-10-14) rewrote required checks to `trim((string) $_POST['x']) === ""`.
- `submission-application-management-tableview.php:377` and `draft_applications.php:164` run that on `applicationId`, which these buttons post as an array. `(string)` on an array raises "Array to string conversion"; the warning is printed before the JSON, so the client cannot parse the response.
- Same pattern on every field in the cause list below.

## Root cause
Blanket `(string)` cast on fields that can be posted as arrays.

## Fix (`sc-saas-admin` only, commit `6a46fa8a`)
- New `isBlankInput($value)` in `includes/core_functions.php`: array = blank when it has no entries; scalar = `trim((string) $value) === ""` (whitespace-only still rejected, SAN-1890 intent kept).
- Used in place of the cast for 11 fields (71 lines, 38 files): `applicationId`, `startupId`, `individualId`, `mentorId`, `adPositions`, `dashboardPositions`, `documentTypes`, `faqPositions`, `formPositions`, `questionPositions`, `sectionPositions`. Each was confirmed in code as an array (`foreach`, `is_array(...)`, `count(...)` on the same key).
- Deliberately unchanged: `applications` (comma-separated string, `explode`d) and `email` (scalar in every trim check). The other ~900 text fields keep `trim((string) ...)`.

## Verification
- `php -l` on all 38 touched files: clean. Throwaway CLI check of the helper: `[]` blank, `["1"]` not blank, `"  "` blank, `"a"` not blank, `null` blank.
- NOT done: live Move to Round / Move to Submitted on a tenant, and any automated test (no test framework in sc-saas-admin). The array-field list comes from a heuristic scan; a field that was missed would still show the warning.

## Commit
`6a46fa8a` on branch `ai_native_setup_sandeep` (sc-saas-admin). Not pushed.
