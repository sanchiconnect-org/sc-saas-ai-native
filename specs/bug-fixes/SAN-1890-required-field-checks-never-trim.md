# SAN-1890 — Required-field checks never trim (`trim(($_POST['x']) == "")`)

Linear: https://linear.app/sanchiconnect/issue/SAN-1890 · Repo: `sc-saas-admin` · Priority: Medium · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
Required-field validation was written `!isset($_POST['x']) || trim(($_POST['x']) == "")`. The parenthesis is misplaced: `$_POST['x'] == ""` is evaluated first and the boolean result is trimmed, so a value of only spaces passed as "present" and was saved (e.g. a round stored with an empty name).

## Evidence
- Ticket: `createProgramRound` with `roundTitle = "   "` created a round with an empty name on dev (sc-saas-e2e FT-006 P2, `test.fail()`).
- Repo scan: 981 occurrences of `trim((<expr>) <cmp> "")` in 148 files, all under `modules/`: 971 canonical `== ""`, plus 9 positive-sense `!== ""` / `!= ""` (e.g. `if (isset($_POST['emailAddress']) && trim((...) !== ""))`) and 1 `== ''`. The ticket counted ~975 with its narrower grep.

## Root cause
Misplaced parenthesis (comparison inside `trim()`), copy-pasted across the admin modules.

## Fix (`sc-saas-admin` only)
Scripted replace of every `trim(($_POST['x']) <cmp> "")` with `trim((string) $_POST['x']) <cmp'> ""` (`==` → `===`, `!=` → `!==`, `!==` stays), 981 replacements in 148 files, plus `modules/tax_management/module.spec.md` (it documented the bug).
- `(string)` instead of `?? ''` as the ticket suggested: the `isset` / `&&` guard in front is kept, and a posted array no longer throws a `TypeError` in `trim()`. **This turned out to be wrong for array-posted fields**: the cast emits "Array to string conversion", and that warning is printed in front of JSON responses (see SAN-1912 below).
- The 10 positive-sense variants (value "present") now treat a whitespace-only value as absent, the same direction as the required checks.

## Behaviour change
Only whitespace-only values change: they are now treated as empty. Throwaway harness, same POST value through old and new expression: `""` reject/reject, `"   "` accept → **reject**, `"\t\n"` accept → **reject**, `"Round 1"`, `"  Round 1  "`, `"0"` and an array unchanged (accept), unset unchanged (reject). Check for fields where a lone space is meaningful (separator/delimiter/password-type names): none found among the matches.

## Verification
- `php -l` on all 148 touched PHP files: 0 failures.
- Diff sanity: 981 removed lines, 981 added lines; reversing the substitution on every added line reproduces the removed line (only the intended change).
- `grep` for the old pattern across the repo (excl. vendor): 0 left. `php tests/auth-gates.php`: 941/941.
- NOT done: live form submits on dev (programs, rounds, events, admins), and any automated test (no harness for inline module handlers). A first scripted pass had an extra `)` that `php -l` caught; it was corrected before anything was committed.

## Notes
- The CFA `createProgramRound` handler (`application_management/submission-application-management.php:272`) now rejects `"   "` with `"Round Title is required"`. The ticket quotes "Round title is missing"; the existing message was not changed.
- `modules/table.php` carries both this change (6 lines) and the uncommitted SAN-1889 fix; commit them separately.
- Remaining ticket step: remove the `test.fail()` in sc-saas-e2e FT-006 P2 after deploy (repo not in this workspace).

## Follow-up: SAN-1912 (regression)
The blanket `(string)` cast broke AJAX handlers whose field is posted as an array (single Move to Round, drafts Move to Submitted). Fixed in `sc-saas-admin` commit `6a46fa8a` with an array-safe `isBlankInput()` helper on the 11 array-capable fields. Record: `specs/bug-fixes/SAN-1912-array-to-string-warning-breaks-json.md`. Lesson: a repo-wide scripted replace needs a check of what each field can carry (array vs scalar), not only `php -l`.

## Commit
Committed in `sc-saas-admin` (branch `ai_native_setup_sandeep`, `b9890246`); deployed 2026-10-14. Push is the user's.
