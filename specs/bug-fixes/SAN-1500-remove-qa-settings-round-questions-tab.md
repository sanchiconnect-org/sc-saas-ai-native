# SAN-1500 — Remove "Q/A Settings" section from round Questions tab (Add & Edit Round)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1500
- **Repo:** sc-saas-admin
- **Type:** Improvement (requested UI removal; not a code defect)
- **Priority:** Low
- **Assignee:** Sandeep

## Problem
The Questions tab of the round modal showed a **Q/A Settings** card with an **Allow to Edit Jury Answer** toggle. Product asked for it to be removed from both the Add Round and Edit Round flows.

## Evidence
- `themes/default/html/application_management/edit_program_round.php` — the card (rendered when `rating_enabled != 1`) and its JS save handler `.editable_jury_answers input` → POST `submitAction=editable_jury_answers`.
- Add Round reuses the same template: after creation it opens `edit_program_round/<newRoundId>` (`modules/application_management/submission-application-management.php:319`).
- `themes/default/html/edit_program_round.php` (legacy Startup Programs round template) — same card, no JS handler (toggle was inert).

## Fix (files changed)
- `sc-saas-admin/themes/default/html/application_management/edit_program_round.php` — removed the Q/A Settings card and the now-dead `.editable_jury_answers input` click handler.
- `sc-saas-admin/themes/default/html/edit_program_round.php` — removed the Q/A Settings card.

Not touched: `editable_jury_answers` column, server handler in `modules/application_management/edit_program_round.php:350`, and the jury-side reads (`themes/default/html/jury/round-applications.php`, `round-startups.php`). Rounds already saved with `editable_jury_answers = 1` keep allowing jury answer edits; there's no admin UI to turn it off now.

## Verification
- `php -l` clean on both templates; `grep` confirms no remaining `Q/A Settings` / `editable_jury_answers` references in either template.
- No automated test added — sc-saas-admin has no test framework.
- Manual check: run admin locally (http://admin.localhost/), open a program → Add/Edit Round → Questions tab; the Q/A Settings card should be gone.

## Commit
_pending — Mahima commits_
