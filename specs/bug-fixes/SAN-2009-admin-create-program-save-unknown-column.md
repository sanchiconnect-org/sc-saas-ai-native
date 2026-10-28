---
id: SAN-2009
title: "Startup program edit page saves nothing: UPDATE fails on unknown column programs.application_target"
type: bug-fix
status: in-progress
linear: https://linear.app/sanchiconnect/issue/SAN-2009
repos: [admin]
related: [SAN-1484]
commit: not committed yet (branch ai_native_setup_sandeep)
created: 2026-10-23
updated: 2026-10-23
---

# SAN-2009: saving a startup program writes nothing

## Problem
On `/create-program/<id>/edit/<slug>` the admin fills Short Description/Tags, Application Deadline, Display Order and Description, clicks **Save**, and after the reload the values are gone. Not only the target field: no field of the program saves.

## Evidence
* Reported with a screenshot of the edit page on `adm.thub.sanchidev.in` (development), program 34.
* The `editProgram` reply is expected to be an empty body. **Not yet confirmed on a running server** (see Verification).

## Root cause
* **Class:** CODE_ERROR.
* `modules/create-program.php`, `submitAction=editProgram`, writes with `$database->update("programs", $postData, ...)`.
* SAN-1484 (commit `1d8a1762`, 2026-10-08) added an "Application target" field. Its guard asked `notifCentreHasColumn($database, "application_programs", "application_target")`. `application_programs` has the column, so the guard passed and `application_target` went into `$postData`.
* The `programs` table has **no** `application_target` column. In `sc-saas-backend` it exists only on `application_programs` (`application-programs.entity.ts`) and `challenges` (`challenges.entity.ts`); it is not in `programs.entity.ts` or the baseline migration. MySQL rejects the whole UPDATE ("unknown column"), so nothing is written.
* The tenant DB connection is `PDO::ERRMODE_SILENT` (`config/config.php`). The failed `update()` returns false with no exception, and `if ($updateRecord)` had no `else`, so the handler ended with no JSON. The admin saw no error.

## Fix (sc-saas-admin only)
* `modules/create-program.php`
  * Column guard now asks `programs`, the table that is written. Until a `programs.application_target` column exists, the target is not part of the UPDATE and the other fields save.
  * `editProgram` now logs `$database->error()` with `error_log()` and replies `{"error": true, "success": false, "errorMessage": "The program could not be saved. ..."}` when the UPDATE fails (output buffers flushed first, per the repo convention). The page's JS already shows `resp.errorMessage` in an "Oops..." dialog.
  * Sets `$tpl->programsHasApplicationTarget` for the template.
* `themes/default/html/create-program.php`: the "Application target" input is shown only when `programsHasApplicationTarget` is true, so the admin is not offered a field that cannot save. The save JS already sends `application_target` only when the input exists.
* `modules/program-management/module.spec.md`: "Watch out for" entry added.

## Blast radius / existing-flow impact
* `sc-saas-admin` only. No backend, flag, API or tenant-scoping change. The save request body and the success reply are unchanged.
* Visible change: the "Application target" input disappears from the startup program edit page (it never saved there).
* CFA programs (`application_management/program.php` writes `application_programs`) and challenges are not touched.
* Not decided here (open product question): should startup programs get an application target and health alert? That would be a backend migration + entity on `programs` and the program-health cron (`sc-saas-backend/src/modules/cron/repository/program-health.repository.ts`, which reads `application_programs` and `challenges` only). File separately if wanted.

## Verification
* `php -l modules/create-program.php`: No syntax errors detected.
* `php -l themes/default/html/create-program.php`: No syntax errors detected.
* `TZ=UTC bash scripts/gates.sh` (sc-saas-admin): platform, composer, php-lint, auth-gates, ai-credit-writes all exit 0; phpstan and phpcs exit 127 (not installed on this machine), so the summary reads `FAILED: 2 required gate(s)`. `composer gates` itself did not start here ("Timezone database is corrupt").
* No automated test added: sc-saas-admin has no test framework for this.
* **Not verified in a browser or against a database.** To check on development:
  1. Save a startup program with the four fields filled, reload: values stay.
  2. DevTools Network: `editProgram` replies `success: true`.
  3. The "Application target" input is no longer shown.
  4. `SHOW COLUMNS FROM programs LIKE 'application_target';` returns no row (confirms the cause).

## Commit
Not committed yet.
