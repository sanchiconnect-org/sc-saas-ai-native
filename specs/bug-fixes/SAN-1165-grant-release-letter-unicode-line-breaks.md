# SAN-1165 — Grant Release Letter: text runs together from Unicode line breaks in the template

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1165
- **Repo:** sc-saas-admin · **Assignee:** Nirmal Singh · **Related:** SAN-787, SAN-966, SAN-967
- **Classification:** CODE_ERROR

## Problem (production report)
A generated letter rendered with every line run together ("ToThe DirectorDirectorate of Information
Technology…"). The template's newline handling only normalised `\r\n`/`\r`, not the Unicode line terminators
(U+2028, U+2029, U+0085) that rich-text sources leave behind when pasted into the plain Settings Management
textarea. `nl2br()` and `explode("\n")` don't recognise them either.

## Fix (`893a269d`)
- A shared `normalizeLineBreaks()` helper in `includes/core_functions.php`.
- It's applied at **render** time (`modules/application-submission-detail.php`), which self-heals values already stored.
- It's also applied at **save** time (`modules/developer/settings_management.php`, scoped to
  `startup_grant_release_letter_template`) to clean the stored value going forward.

## Verification
- `php -l` clean. sc-saas-admin has no automated tests.

## Commit
sc-saas-admin `893a269d` (on `ai_native_setup`). Note: the commit message carries no SAN id; linked here and on Linear.
