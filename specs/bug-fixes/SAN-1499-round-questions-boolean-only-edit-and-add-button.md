# SAN-1499 — Edit Round › Questions: "Boolean Only" missing in Edit dropdown + "Add question" button on Edit panel

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1499
- **Repo:** sc-saas-admin (branch `ai_native_setup_mahima`)
- **Type:** Bug + Improvement (CODE_ERROR)
- **Assignee:** Sandeep · **Milestone:** Enhancement › Application Round Settings

## Problem
1. Editing a **Boolean Only** question opened the Edit panel with "Answer field type" empty, and Submit then failed with "Answer field type is missing".
2. The Edit question panel had no way to start a new question except Cancel.

## Root cause
The Edit dropdown `#editAnswerFieldType` listed boolean, text, upload and numeric, but not `boolean_only`. The Add dropdown `#questionFieldType` has it. So `.val("boolean_only")` in the `.editQuestion` handler matched no option.

## Fix
Applied in both `themes/default/html/application_management/edit_program_round.php` and `themes/default/html/edit_program_round.php`:
- Added `<option value="boolean_only">Boolean Only (Yes/No)</option>` to `#editAnswerFieldType`.
- Added a `#showAddQuestion` "+ Add" button at the right end of the Edit question card header.
- JS handler for the button: clears the Add form (title, description, field type, min/max, mandatory off), hides `#editQuestionBox` and shows `#addQuestionBox`. Saving goes through the existing `#addQuestion` → `add_question` flow.

View-only change. No module, API, flag or schema change.

## Verification
- `php -l` passes on both files.
- No automated tests: sc-saas-admin has no test framework. Manual QA against the acceptance criteria in the Linear issue is pending.

## Commit
_pending_
