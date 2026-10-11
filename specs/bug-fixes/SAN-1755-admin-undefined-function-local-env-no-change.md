# SAN-1755 — admin "Call to undefined function" events are local-environment only (no change)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1755 (Sentry SC-SAAS-ADMIN-11 / -12) · **Repo:** sc-saas-admin · **Priority:** Urgent · **Assignee:** Aman kabra · **Classification:** NOT_A_BUG (developer machine)

## Evidence
- Both groups: `environment=local` (observed in Sentry); no production event.
- `zenxaiConfig()` is no longer defined anywhere: the Zenx integration was removed by SAN-1739 (`77437530`) (observed in git). A stale local checkout or cached page calling it is the likely source (inferred).
- `juryVisibilityRoundColumns()` is defined in `includes/jury_visibility_functions.php`, which `index.php:40` loads (observed in code); the local event predates or lacks that include (inferred).

## Root cause
A local dev checkout out of sync with the repo (inferred). No defect on the committed branch.

## Fix
No code change.

## Not fixed
Nothing to fix. A recurrence with `environment=production` would mean a deploy missing `includes/jury_visibility_functions.php` or an include-order problem.

## Contract impact
None.

## Verification
Code reading only (grep for both definitions and the include). Nothing run.

## Commit
None.

## Sentry
Resolved as local-environment noise; reopen if it appears with `environment=production`.
