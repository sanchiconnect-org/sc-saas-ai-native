# SAN-1836 — Program Manager cannot see the Jury NDA tracker

- Linear: https://linear.app/sanchiconnect/issue/SAN-1836 (Enhancement project, milestone "Jury NDA Signing", label Bug + Repo: Admin, assignee Sandeep)
- Repo: sc-saas-admin only
- Classification: CODE_ERROR (the scoping for PMs already existed, the entry check was too narrow)

## Problem
On the Jury Allotment tab the NDA tracker (tiles, NDA Status column, Details drawer, exports, reminders) shows for Super Admin and permission holders but not for the programme's Program Manager, who needs to follow signing progress.

## Root cause
`juryNdaCanViewNdas()` allows Super Admin, Developer or a role with `can_view_jury_ndas = 1`. `juryNdaTrackerAuthorise()` and the tracker block in `modules/application_management/edit_program_round.php` stopped there, so a PM role without that permission never reached `juryNdaManageScope()`.

## Fix
New `juryNdaIsProgramManagerRole()` (role code equals `program_manager_role_id` / `corporate_program_manager_role_id`; false for jury sessions and while `jury_nda_enabled` is off). The entry check of `juryNdaTrackerAuthorise()` and of the tracker block now accepts that role in addition to the old rule. `juryNdaManageScope()` is unchanged and remains the per-programme limit (PM must be in `program_managers`; corporate PM only their business challenge; partner only its own).

Files changed (uncommitted): `sc-saas-admin/includes/jury_nda_functions.php`, `sc-saas-admin/modules/application_management/edit_program_round.php`, `sc-saas-admin/modules/application_management/module.spec.md`.

## Verification
- `php -l` on both PHP files: no syntax errors.
- Throwaway CLI check (fake DB, outside the repo), flag on: PM listed on the programme passes; PM not listed gets 403; PM cannot use another programme's round; an admin role without the permission and not a PM stays 403; Super Admin passes; bad CSRF refused first; missing juror id is 400; round-level calls (exports, reminders) work for the PM. 10 of 10 pass. Flag off: the PM role is false and PM and Super Admin both get 404.
- NOT done: a real login as a Program Manager in the browser. No automated test added: sc-saas-admin has no test framework.

## Commit
Not committed (branch ai_native_setup_sandeep).
