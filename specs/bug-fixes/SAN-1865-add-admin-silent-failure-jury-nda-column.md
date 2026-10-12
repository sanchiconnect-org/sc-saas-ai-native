# SAN-1865: Add/Edit Admin silently fails when jury NDA is enabled

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1865
- **Repo:** sc-saas-admin
- **Priority:** High
- **Assignee:** Nirmal Singh
- **Classification:** CODE_ERROR
- **Found while:** creating the QA admin and jury accounts on `adm.thub.sanchidev.in` for SAN-1581

## Problem
On the Admins page, Add Admin created no account. Edit Admin saved nothing either. Neither showed an error.

## Evidence
- `addfd4a5` (2026-10-05, Jury NDA FA-010) added `data[can_view_jury_ndas]` to the Add/Edit **Admin user** form (`themes/default/html/auth/admins.php`, formerly line 1193-1209). It's rendered whenever `juryNdaPermissionColumnReady()` is true: tenant flag `jury_nda_enabled` on, and the `spa_admin_roles` column exists.
- That column exists on `spa_admin_roles` only. I compared every field the user form posts with `sc-saas-backend/src/modules/global/admin/spa_admin_users.entity.ts`, and `can_view_jury_ndas` is the only one missing.
- `addAdmin` and `editAdmin` (`modules/auth/admins.php`) pass `$_POST['data']` wholesale to `$database->insert/update`. The result is a MySQL unknown-column error.
- The DB connection uses `PDO::ERRMODE_SILENT` (`config/config.php`). `Medoo::exec()` (`core/db.php`) returns the statement even when `execute()` fails. So `if ($insertAdmin)` could even report success and send the credentials email for an account that was never saved.

## Root cause
A role permission was placed on the user form. On top of that, the save handlers didn't check for DB errors.

## Fix
- `themes/default/html/auth/admins.php`: removed the "Can View Jury NDAs?" select from the admin user form. The role form's select is unchanged.
- `modules/auth/admins.php`, in both `addAdmin` and `editAdmin`:
  - `can_view_jury_ndas` is unset before the write.
  - The DB error (`$database->error()[2]`) is read immediately after the write. In `editAdmin` that happens before the jury partner updates, which would overwrite it.
  - A failed write now shows an error message and writes an `error_log` entry, and no success message or credentials email is sent.
- `modules/auth/module.spec.md`: added a note that this is a role-only permission.

## Verification
- `php -l` passes on both PHP files.
- The repo has no test framework, so no regression test was added.
- **Still to do after deploy to dev:** add the QA admin on `adm.thub.sanchidev.in`, confirm the account appears and can log in, then run `sc-saas-e2e` `npm test` so the admin and jury tests go green.

## Commit
sc-saas-admin `3255e7d7` (ai_native_setup).
