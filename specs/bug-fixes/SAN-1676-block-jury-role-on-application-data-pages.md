# SAN-1676 — Block jury role on application-data pages (FA-011 P0)

**Repo:** sc-saas-admin · **Priority:** Urgent · **Class:** CODE_ERROR · **Status:** In Review (not committed)

## Problem
Admin pages that expose full application data only called `checkLoggedIn()`, so a jury-role user could open them and download every answer, file and AI screening (PDF, attachments, bulk exports, analysis upload/thesis generation).

## Root cause
No role check on `application-submission-detail.php`, `form-submission-detail.php`, `submission-application-management(.php|-tableview.php)` and `analysis_form.php`.

## Fix
- New `denyJuryRoleAccess()` in `includes/core_functions.php`: jury role (`$_SESSION['admin_roles']['code'] == jury_role_id`) → redirect to `/jury/dashboard` (GET) or 403 JSON (POST/AJAX), then `exit`.
- Called right after `checkLoggedIn()` in the five files above.
- `application_management/module.spec.md` updated.

## Verification
- `php -l` clean on all 6 changed PHP files.
- CLI harness of the helper: ADMIN GET → passes through; JURY GET → redirect (exit); JURY POST → `403 {"success":0,"message":"Access denied."}`; no session → passes through (checkLoggedIn handles it).
- Not done: a live jury-session browser check on staging; automated test coverage was not added (no test framework in sc-saas-admin).
- Note: `/check-isolation` is N/A (no new queries).

## Commit
Not committed yet — awaiting confirmation of the diff.
