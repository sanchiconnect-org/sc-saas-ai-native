# SAN-1887 — form-management/versions.php has no login check

Linear: https://linear.app/sanchiconnect/issue/SAN-1887 · Repo: `sc-saas-admin` · Priority: Urgent (security) · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
`modules/form-management/versions.php` never called `checkLoggedIn()` (every sibling page does). Anonymous visitors could read a form's version history (incl. admin names) and POST `restoreForm` to overwrite `forms.fields`. `restoreForm` also loaded the `spa_admin_logs` row by `recordId` alone, so one form's snapshot could be restored onto another form.

## Evidence
- Confirmed on development by the sc-saas-e2e FT-006 P2 work (SAN-1880), against its own throwaway form only.
- Code: file started with `include common.php` then went straight to the `restoreForm` handler.
- `formFieldsPreview` in the same file was also reachable anonymously (same missing guard); it already scoped by `record_id` + module.

## Root cause
Missing auth call + missing ownership check on the log row.

## Fix (`sc-saas-admin` only)
`modules/form-management/versions.php`:
- `checkLoggedIn();` first line, same placement as `edit-form.php` / `manage.php` / `edit-form-final.php` (anonymous GET/POST now redirect to `/auth/login`; covers the history list, `restoreForm` and `formFieldsPreview`).
- `restoreForm` loads the log row with `id = recordId AND record_id = formId AND module = forms_management AND table_name = forms`; a miss returns "This version doesn't belong to the selected form." and writes nothing. IDs cast to int.
`modules/form-management/module.spec.md`: versions.php entry updated.

## Decision on ticket fix point 3 ("same permission check the form editor uses")
The form editor (`edit-form.php`) only uses `checkLoggedIn()` for its general actions; `checkRole("is_dev")` guards just the JSON-upload action. So no extra role gate was added to versions.php — any logged-in admin who can open the form editor can restore versions, as before. Flag if a stricter role is wanted.

## Verification
- `php -l modules/form-management/versions.php`: no syntax errors.
- Legit UI flow unaffected by inspection: Restore buttons send `formId = spa_admin_logs.record_id` of the same row, which satisfies the new check.
- NOT done: live anonymous GET/POST against a running admin, cross-form restore attempt, e2e. `sc-saas-admin` has no test framework (regression test not written, per bug-fix rule); the e2e regression test belongs in `sc-saas-e2e`.

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
