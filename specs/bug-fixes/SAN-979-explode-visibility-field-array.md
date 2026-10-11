---
id: SAN-979
title: "explode() TypeError on visibility field — value sometimes already an array"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-979
sentry: [SC-SAAS-ADMIN-W, SC-SAAS-ADMIN-R]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-979 — explode() TypeError on visibility field

## Root cause
Two files carry the exact same "section visibility" evaluator, copy-pasted:
```php
$xplodedValues = explode(", ", $this->formSubmission[$form["form_code"]][$section["visiblity"]["field"]]);
```
- `themes/default/html/jury/round-applications.php` (~line 355) — SC-SAAS-ADMIN-W, 23 events
- `themes/default/html/application_management/form-submission-detail.php` (~line 144) — SC-SAAS-ADMIN-R, 2 events

A multi-select form field's stored submission value is sometimes already a PHP array (not a comma-separated string) — `explode()` only accepts a string as its second argument, and PHP 8 rejects the mismatch with a `TypeError` instead of silently coercing.

## Fix
In both files: read the field value into a local var first, and only `explode()` it when it isn't already an array:
```php
$visiblityFieldValue = $this->formSubmission[$form["form_code"]][$section["visiblity"]["field"]];
$xplodedValues = is_array($visiblityFieldValue) ? $visiblityFieldValue : explode(", ", $visiblityFieldValue);
```
The immediately-following `if (is_array($xplodedValues))` check (already present) now actually reflects reality in both branches.

## Blast radius
Two template files. No behavior change for the string case; the array case now works instead of crashing the whole form-submission-detail/round-applications page.

## Verification
`php -l` clean on both files.

## Rollout
Both Sentry issues (SC-SAAS-ADMIN-W, SC-SAAS-ADMIN-R) marked resolved. Not committed/pushed — sitting on `ai_native_setup_aman`, pending review.

## Open questions
None — worth checking whether any other module has this same copy-pasted visibility-evaluator block, since it's clearly been duplicated at least twice already.
