# SAN-1653 — Logged-in applicants saved without company name (Kanban shows the person)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1653
- **Repo:** sc-saas-frontend · **Priority:** High · **Assignee:** Nirmal Singh · **Classification:** CODE_ERROR

## Problem
On TRISE POC Grant (program 6, form 14), the Kanban cards show the applicant's name, not the company, even though
"Enable Company/Entity name field?" is on. Every submission has `forms_submissions.company_name = NULL`, and row 596's
`data` holds `"companyName": null`. The admin card reads `application.company_name` and falls back to the person's
name when it's empty (`themes/default/html/application_management/submission-application-management.php` ~2438).

## Root cause
`ProgramPublicApplyComponent.checkAndAutoApply()` (`src/app/modules/programs/program-public-apply/program-public-apply.component.ts`)
handles **logged-in** applicants (`?autoStatusCheck=true` / `?fromRegister`). It writes the applicant details from the profile
(email, name, country code, mobile) to `localStorage['application-<uuid>']`, which skips the apply modal. The modal is
the only place `companyName` is collected, and the shortcut never set it, so every logged-in applicant was submitted
with `companyName: null`. The form's custom "Company Name" text field (`field_8qgJoE1a7m`, `field_type: custom`,
`db_column_name: null`) is stored only in `data` JSON and never fills the column. The admin's Company Name Migration
tool can't help, because it only reads fields wired with `db_column_name = company_name`.

## Fix
With `companyNameField` on, a startup's `companyName` comes from its own profile (`StartUpService.getStartUpInfo()`,
trimmed). If none is found, or the account isn't a startup, the shortcut is skipped so the apply modal asks for it,
following the same rule as the existing mobile-number check. Programs without the company field are unchanged.

## Existing data (per tenant DB, TRISE form 14)
```sql
UPDATE forms_submissions
SET company_name = TRIM(JSON_UNQUOTE(JSON_EXTRACT(data, '$.field_8qgJoE1a7m')))
WHERE form_id = 14 AND (company_name IS NULL OR company_name = '')
  AND JSON_UNQUOTE(JSON_EXTRACT(data, '$.field_8qgJoE1a7m')) <> '';
```

## Verification
- `tsc` clean for `tsconfig.app.json` and `tsconfig.spec.json`.
- 3 new unit tests in `program-public-apply.component.spec.ts`: the profile company is copied (trimmed); a missing company
  falls back to the modal; there's no lookup when the program has no company field.
- They could **not be executed**: `ng test` compiles every spec, and several unrelated specs already fail to compile
  (`search/pages/startups`, `startups/pages/dashboard`, `number-format.directive`, `incomplete-step-forward.guard`,
  several pipes, the CometChat confirm dialog), so karma runs 0 tests.

## Commit
sc-saas-frontend `32d6e52c` (on `ai_native_setup`)
