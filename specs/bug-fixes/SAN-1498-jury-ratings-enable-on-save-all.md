# SAN-1498 — Edit Round › Rating Criteria: enable jury ratings only on "Save all", default No

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1498
- **Repo:** sc-saas-admin (branch `ai_native_setup_mahima`)
- **Type:** Improvement (CODE_ERROR: the toggle saved its state before any criteria existed)
- **Assignee:** Sandeep · **Milestone:** Enhancement › Application Round Rating Criteria

## Problem
On the "Enable jury ratings in this round?" radios, a click saved `is_rating_required` straight away via the `updateIsRoundRequiredForRound` AJAX call. "Save all" only saved the criteria rows. So an admin could click Yes, close the modal without adding criteria, and the round stayed "ratings enabled" with zero criteria. When the flag was NULL, neither radio was selected.

## Fix
Applies to both screens: Application Management (`application_program_rounds` / `application_program_submission_rating_criterias`) and Startup Programs (`program_rounds` / `startup_rating_criterias`).

- `modules/application_management/edit_program_round.php`, `modules/edit_program_round.php`
  - `update_rating_criteria`: rejects an empty criteria list. After saving, sets `is_rating_required = 1` and writes an admin log entry.
  - `delete_rating_criteria`: when the last active criterion is removed, resets `is_rating_required = 0`.
  - Edit page: computes `rating_enabled = is_rating_required == 1 && active criteria exist`.
- `themes/default/html/application_management/edit_program_round.php`, `themes/default/html/edit_program_round.php`
  - The radios, the criteria section's show-on-load and the Q/A Settings card are driven by `rating_enabled`. No is the default.
  - Clicking Yes only shows the section. Clicking No still saves `0` immediately.
  - Save all blocks an empty list on the client side.

No API, feature flag or schema change. Tenant scoping is unchanged: the admin uses the per-tenant DB.

## Known limitation
Legacy rounds with `is_rating_required = 1` and no criteria now show **No** in admin. Their DB value stays 1 until an admin saves criteria or the data is cleaned up, so the jury-side pages (`modules/jury/round-*.php`) still treat them as rating rounds. A one-off cleanup could fix them, for example `UPDATE application_program_rounds r SET is_rating_required = 0 WHERE is_rating_required = 1 AND NOT EXISTS (SELECT 1 FROM application_program_submission_rating_criterias c WHERE c.program_round_id = r.id AND c.is_active = 1)`, plus the same for `program_rounds`.

## Verification
- `php -l` passes on all 4 touched files.
- No automated tests: sc-saas-admin has no test framework. Manual QA against the acceptance criteria in the Linear issue is pending.

## Commit
_pending_
