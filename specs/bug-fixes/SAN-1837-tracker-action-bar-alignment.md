# SAN-1837 — Tracker export and reminder buttons misaligned, status message wraps badly

- Linear: https://linear.app/sanchiconnect/issue/SAN-1837 (Enhancement, milestone "Jury NDA Signing", Bug + Repo: Admin, Sandeep)
- Repo: sc-saas-admin only. Classification: CODE_ERROR (layout / CSS).

## Problem
On the Jury Allotment tab the export buttons (ZIP, CSV, Excel) and "Send reminder to selected" sat on different lines with different heights, and the message "Downloaded round_2_NDA_status_....xlsx." broke into the bar next to the buttons.

## Root cause
Inline buttons, a status span and a hint paragraph were spread over two loose blocks with no shared row, fixed height or wrapping rule.

## Fix
One flex row: the three exports on the left, the reminder button pushed right, all 34px high with icons; a second row under a thin divider holds the status message (green, red on error, hidden when empty) and the reminder hint. Wraps on narrow screens. Button ids and the message element are unchanged, so `jury-nda-export.js` and `jury-nda-reminder.js` needed no change.
Files (uncommitted unless noted): `sc-saas-admin/themes/default/html/application_management/edit_program_round.php`, `.../module.spec.md`.

## Verification
`php -l` clean. Not done: browser run; no automated test (admin has no test framework).
