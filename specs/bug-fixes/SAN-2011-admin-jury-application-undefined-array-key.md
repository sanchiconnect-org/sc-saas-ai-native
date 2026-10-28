---
id: SAN-2011
title: "Jury application page prints PHP 'Undefined array key field_...' warnings (jury/_application_details.php:109)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-2011
repos: [admin]
related: [SAN-1681]
commit: admin@42064318 (branch ai_native_setup_sandeep, not pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2011: a missing dependency answer prints a PHP warning on the jury page

## Problem
On the jury's view of an allotted application (`/jury/round-applications/program/<id>/round/<id>/<submission uuid>`), a section prints `Warning: Undefined array key "field_bq0dAmZgh9"` (and `"field_vD6AqDIjLk"` twice) in `themes/default/html/jury/_application_details.php` on line 109. Development shows the PHP errors on the page; production probably only logs them.

## Evidence
* Found by the e2e suite, `tests/cfa/p5-jury-evaluation.spec.ts` (jury NDA test), on development, 2026-10-24, program 480, round 447. Reporter: Nirmal Singh.
* The section name "Other Details" in the report is a section title in program 480's form, not fixed text in the template.

## Root cause
* **Class:** CODE_ERROR.
* Line 109 is the visibility condition of a field (`$field["visiblity"]`: show this field only if another field's answer `is` / `is_not` a value). It read the controlling field's answer with `$this->formSubmission[$form["form_code"]][$field["visiblity"]["field"]]`, with no existence check.
* A submission from an earlier version of the form, or one where that answer was never saved, has no key for the controlling field, so PHP warned. The displayed field's own read (further down) was already guarded with `isset()`.

## Fix (`sc-saas-admin`, 1 template)
`themes/default/html/jury/_application_details.php`: inside the field loop, the controlling answer is read once into `$visiblityControlValue` with `?? null`, through a local copy of `$this->formSubmission` (sparkAdminTpl has no `__isset`). Both the `is` and the `is_not` comparisons use that variable. `display_errors` is untouched, as the issue asks.

## Blast radius / existing-flow impact
* `sc-saas-admin` only, template only. The same template is shared by `jury/round-applications.php` and the admin "Preview as juror" page (`jury_visibility_preview.php`), so both stop warning.
* Behavior is unchanged: a missing answer compared as `null` before (with a warning) and still does. An `is` rule on a missing answer hides the field; an `is_not` rule shows it.
* Not changed (outside this issue): the multi-record table in the same template (`$multiRecords[$field['key']]`, around lines 84-90) has the same unguarded read and may warn the same way.

## Verification
* `php -l themes/default/html/jury/_application_details.php`: No syntax errors detected.
* Real template rendered with the real `sparkAdminTpl` and mock data under `E_ALL` (script kept in the session scratchpad, not in the repo), one section with fields: no rule, an `is` rule on a missing answer, an `is_not` rule on a missing answer, an `is` rule on a present answer.
  * Before (HEAD): fields shown `Has answer, no rule | Depends(is_not) on MISSING | Depends(is) on present`; 2 warnings, `Undefined array key "field_missing1"` and `"field_missing2"`, both at line 109.
  * After (fix): the same fields shown; 0 warnings.
* `TZ=UTC bash scripts/gates.sh` (sc-saas-admin): composer, php-lint, auth-gates, ai-credit-writes, panel-hardening, sql-list-filters, xss-escapes all exit 0; phpstan and phpcs exit 127 (not installed on this machine), so the summary reads `FAILED: 2 required gate(s)`. `composer gates` itself does not start here ("Timezone database is corrupt").
* No automated test added: sc-saas-admin has no test framework for this.
* **Not verified on a running admin.** On development, open the jury page for program 480 / round 447 and check that "Other Details" shows no `Warning: Undefined array key`.

## Commit
`42064318` on `ai_native_setup_sandeep` in `sc-saas-admin` (local, not pushed). Also adds a "Watch out for" entry to `modules/jury/module.spec.md`.
