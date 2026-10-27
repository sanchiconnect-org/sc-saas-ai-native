# SAN-2055 — Edit Round › Questions: no loader after Add a question / Edit question submit

Linear: https://linear.app/sanchiconnect/issue/SAN-2055 · Repo: `sc-saas-admin` · Priority: Medium · Assignee: Sandeep · Labels: Repo: Admin, Improvement
Classification: **CODE_ERROR** (missing UI feedback; the requirement is clear, no spec question)

## Problem
In the Application Management round modal (Edit Round › Questions), pressing Submit on **Add a question** or **Edit question** shows nothing while the request runs. An admin can click Submit again (duplicate question) or think the click did nothing.

## Evidence
- Reporter screenshot: Edit Round R1 → Questions tab on `adm.thub.sanchidev.in`.
- `themes/default/html/application_management/edit_program_round.php`: the `#addQuestion` handler (`submitAction: "add_question"`) and the `#editQuestionBtn` handler (`submitAction: "edit_question"`) called `$.post(...)` with no loader and no error handler. Delete question (`.deleteQuestion`) and other round-settings actions in the same file already use the project's `#loaderOverlay`.

## Root cause
The two handlers were written without the loader the sibling handlers use, and without a `.fail` branch.

## Fix (`sc-saas-admin`, one file)
`themes/default/html/application_management/edit_program_round.php`, both handlers:
- Right before the `$.post`: ignore the click if a busy flag is set, set it, `$("#loaderOverlay").show()`. The buttons are `<btn>` elements, so a `disabled` property would do nothing; a `data("busy")` flag is used instead, and the overlay also covers the page.
- Success: behaviour unchanged (Add reloads the page; Edit shows the toast, then reloads after 500 ms), so the overlay stays until the reload.
- Edit, server says not successful: hide the overlay, clear the busy flag, show the same error toast as before.
- Both: new `.fail(...)` hides the overlay, clears the flag, and shows "Something went wrong. Please try again."
- Validation (missing title / field type) returns before the loader, as before.

Not changed: the same Questions tab in the sibling round modals (`modules/edit_program_round.php`, `venture_studio_edit_program_round.php`, `mentor_application_edit_round.php`, `edit_program_round2.php`). Decide with the reporter if they should get the same change.

## Verification
- `php -l themes/default/html/application_management/edit_program_round.php`: No syntax errors detected.
- Diff reviewed: only the two handlers changed (+23 lines, no deletions).
- NOT done: a run in the browser on development (Add and Edit, success, forced failure, double click). No automated test added: sc-saas-admin has no test framework.

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
