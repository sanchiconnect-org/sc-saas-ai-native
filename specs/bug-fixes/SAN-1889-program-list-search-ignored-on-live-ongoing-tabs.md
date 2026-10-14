# SAN-1889 — Program list search is ignored on the Live / Ongoing Evaluation tabs

Linear: https://linear.app/sanchiconnect/issue/SAN-1889 · Repo: `sc-saas-admin` · Priority: Medium · Assignee: Sandeep
Classification: **CODE_ERROR** (item 1). Items 2 and 3: see below.

## Problem (ticket)
On `{ADMIN_URL}/table/application_programs`: (1) search does nothing under the Live and Ongoing Evaluation tabs, (2) a re-opened program still appears under Ongoing Evaluation, (3) the last search sticks in `$_SESSION['query']`.

## Item 1 — root cause and fix (fixed)
`modules/table.php` built the search conditions as `$getRecordsQuery["OR"] = $newarayforsearch;` and then wrote the tab's deadline rule into the same `"OR"` array, so one OR group held `title LIKE ... OR description LIKE ... OR deadline >= today OR deadline IS NULL`. Every program matching the deadline rule matched, whatever the search term.

Fix: the tab rule now goes in its own named group `"OR #tab"` (Medoo ANDs top-level groups together), for both the records and the count query. Same block serves `application_programs`, `programs` and `vs_programs`, so all three lists are fixed.

Generated SQL (Medoo `whereClause()` from the repo's own `core/db.php`, no database):
- before, Live + "Alpha": `WHERE ((title LIKE '%Alpha%') OR (description LIKE '%Alpha%') OR deadline >= DATE(..) OR deadline IS NULL) AND (applications_closed = '0' AND status = '1')`
- after: `WHERE ((title LIKE ..) OR (description LIKE ..)) AND (deadline >= DATE(..) OR deadline IS NULL) AND (applications_closed = '0' AND status = '1')`
- Ongoing is the same shape; with no search the query is identical before and after (no regression).

## Item 3 — session term (not reproducible in code, no change)
`modules/table.php` runs `unset($_SESSION['query']);` unconditionally near the top of every request (line ~301), and only a non-empty `$_POST['q']` sets it again; the session handler (`core/session.php`) writes the whole session, so the unset persists. An empty search therefore shows the unfiltered tab. If it still reproduces on dev, a precise repro (request sequence) is needed.

## Item 2 — re-opened program under Ongoing (decision, no change)
Ongoing Evaluation = `application_closed_date < today OR applications_closed = 1`; Live = `deadline >= today OR deadline IS NULL` (with `applications_closed = 0`). Re-opening clears only `applications_closed`, not the deadline. A re-opened program whose deadline has already passed therefore still matches Ongoing (and not Live), which also matches what the PWA and (since SAN-1886) the backend do: it still refuses applications after the deadline. A re-opened program with no or a future deadline is not in Ongoing. Whether re-open should also move or extend the deadline is a product decision, so the tab rule was left alone.

## Files changed
- `modules/table.php`

## Verification
- `php -l modules/table.php`: clean. `php tests/auth-gates.php`: 941/941.
- SQL before/after harness (above). NOT done: a live run of the list page on dev, and an automated test (no harness for this inline module). The FT-006 P2 program-list tests can drop their no-match-search workaround after deploy (sc-saas-e2e is not in this workspace).

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
