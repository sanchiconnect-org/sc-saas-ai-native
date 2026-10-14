# SAN-1891 — After "Import fields from form", the form's Current version card shows the pre-import fields

Linear: https://linear.app/sanchiconnect/issue/SAN-1891 · Repo: `sc-saas-admin` · Priority: Low · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
`submitAction=importFieldsFromForm` (`modules/form-management/edit-form.php`) wrote its `spa_admin_logs` snapshot from the form's previous fields, before the import. The version history's "Current" card (the newest log row) therefore showed the old fields.

## Evidence
Seen on dev by the sc-saas-e2e FT-006 P2 form-builder tests. Code: the handler read `forms.fields`, logged it, then overwrote `forms.fields` with the selected form's fields and never logged the result. `saveForm` and `uploadFieldsJson` update first and log the new sections.

## Root cause
The only log call ran before the update and carried the old fields. Second defect in the same call: it passed `$formData['fields']`, a JSON string, to `createAdminLogs()`, which json_encodes it again, so the row was double-encoded and `versions.php` (preview and restore need `json_decode` to give an array) could not read it ("unreadable"). So restoring "Current" after an import errored rather than undoing it.

## Fix (`sc-saas-admin` only)
- `modules/form-management/edit-form.php`, `importFieldsFromForm`: still logs the pre-import snapshot (so the import can be undone from the history, even for a form that had no earlier snapshot) but now passes the decoded array, and after a successful update logs a second row with the imported fields (decoded). The newest row, "Current", now equals the form's fields.
- `modules/form-management/module.spec.md`: documents the snapshot rule.

## Verification
- `php -l`: clean. `php tests/auth-gates.php`: passes.
- Throwaway harness of the stored rows. Before: one row, shows the old section, unreadable by the restore guard; Current = old. After: two rows (old, then imported), both restorable; Current = imported. Empty form before import: the before-row stores `null`, as before.
- NOT done: a live import on dev and a look at the real version panel; no automated test (no harness for inline module handlers).

## Not changed
- Existing double-encoded rows already in `spa_admin_logs` from earlier imports stay unreadable (no data migration).
- Importing leaves two rows per import; when the previous state was already the newest snapshot, the before-row duplicates it.

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
