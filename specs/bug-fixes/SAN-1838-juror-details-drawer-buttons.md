# SAN-1838 — Juror Details drawer: View / Download vanish on hover and sit below the fold

- Linear: https://linear.app/sanchiconnect/issue/SAN-1838 (Enhancement, milestone "Jury NDA Signing", Bug + Repo: Admin, Sandeep)
- Repo: sc-saas-admin only. Classification: CODE_ERROR (CSS and layout).

## Problem
View, Download and Close looked like plain text and their label disappeared on hover; View and Download were in the Decisions list far down the drawer; the drawer looked flat (grey badge for every state, no section labels).

## Root cause
The buttons used the theme's `btn-outline-secondary`, whose hover state turns the text white, over an overriding white background; they were rendered per decision at the end of the list.

## Fix
Fixed colours in every state for View, Download, Retry signed copy and Close (hover and focus add only a light background); eye / download icons. View and Download now appear once on the status row at the top right (newest stored signed copy) and are gone from the Decisions list. Sticky header, uppercase section labels, label / value rows with dividers, quiet list cards, status badge coloured by state.
Side effect: older versions' copies are not reachable from the drawer; the ZIP export holds one copy per signed juror.
Files: `sc-saas-admin/themes/default/assets/js/jury-nda-drawer.js`, `.../edit_program_round.php`, `.../module.spec.md`.

## Verification
`php -l` and `node --check` clean. Not done: browser run; no automated test.
