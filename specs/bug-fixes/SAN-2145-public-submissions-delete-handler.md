---
id: SAN-2145
title: "sc-saas-admin public_submissions.php: unauthenticated, form-unscoped deleteSubmission handler (SAN-35 only partly fixed)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-2145
sentry: []
repos: [admin, tenants-admin]
related: [SAN-35, SAN-1563, SAN-1939, SAN-1970]
commit: sc-saas-admin 1cda4c08, sanchiconnect-saas-tenants-admin a037ecd (both on ai_native_setup_aman)
created: 2026-10-30
updated: 2026-10-30
---

# SAN-2145: the public share page could delete any submission

## Found by
The second-person verification of SAN-1563 (a re-read of the fixes on `origin/main`, 2026-10-30), then confirmed by reading the file.

## Investigation
* `modules/form_builder/public_submissions.php` is public on purpose (the "share responses" page). Since SAN-35 it finds the form only by `forms.public_share_token` (48 hex characters).
* Lines 86-115 still held a `deleteSubmission` POST handler: no `checkLoggedIn()`, no CSRF check, and `$database->delete("forms_submissions", ["id" => clean($_POST['submissionId'])])` with no `form_id` scope.
* Anyone holding one valid share link could therefore delete any submission of any form in the tenant by counting through ids.
* Nothing on the public page posts it: `grep deleteSubmission` finds the caller only in `themes/default/html/form_builder/submissions.php` (the logged-in page, which posts to `modules/form_builder/submissions.php`, whose own handler is behind the login). The handler was dead code with a live hole.

## Root cause
The handler was copied from the logged-in page when the public page was written, and SAN-35 secured the read side only.

## Fix
* sc-saas-admin `modules/form_builder/public_submissions.php`: handler removed, replaced by a `/* */` note. The page is read-only.
* Same change set, from the SAN-1939 / SAN-1563 hardening gap: `.htaccess` in sc-saas-admin and sanchiconnect-saas-tenants-admin now also returns 403 for `modules/`. `index.php` include()s module files server-side, so nothing needs them by URL; a direct request only produced a PHP fatal that leaked `/var/www/html/modules/...`. `themes/` is deliberately not denied (its css, js and images are served directly).
* Also corrected the `nosemgrep` rule id on `modules/partners/broadcast/create.php` to `php.lang.security.injection.tainted-sql-string.tainted-sql-string` (SAN-1598).

## Verification
* `php -l modules/form_builder/public_submissions.php` -> no syntax errors.
* `composer gates` in sc-saas-admin: platform, composer, php-lint, auth-gates, ai-credit-writes, panel-hardening, sql-list-filters, xss-escapes all exit 0. phpstan and phpcs exit 127 (not installed on the dev machine): CI is the full check. Same in tenants-admin.
* Not run: a live request.

## Open
* Not deployed yet: it has to reach `ai_native_setup`, then the release path to `main`, and be built.
* After deploy, paste on SAN-2145: a POST of `submitAction=deleteSubmission&submissionId=<id>` to a share link must delete nothing; `GET /modules/aws/ajax.php` on admin and `GET /modules/auth/login.php` on tenants-admin must return 403.
* Closed by someone other than the implementer.

## Spec updates made
* `sc-saas-admin/modules/form_builder/module.spec.md` (SAN-2145 note; the old "no authentication" paragraph marked superseded).
* `CLAUDE.md` guardrails in sc-saas-admin and sanchiconnect-saas-tenants-admin (`modules/` added to the denied folders).
