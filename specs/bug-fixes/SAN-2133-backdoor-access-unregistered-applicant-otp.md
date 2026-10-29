# SAN-2133 — Backdoor Access for an unregistered applicant asks for email OTP

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-2133 (High, `Bug`, `Repo: Admin`, Sandeep)
- **Repo / branch:** `sc-saas-admin` / `ai_native_setup`
- **Related:** SAN-2127 (introduced it), SAN-1959 / SAN-2002 (applicant-token flow)
- **Classification:** CODE_ERROR. SAN-2127's acceptance criterion said "No matching user: unchanged", and the code changed it.

## Problem

On dev, **Backdoor Access** on application 1595 (`backdoor-testing`) opened the PWA's "Verify Your Email → Send OTP" modal instead of the application. The applicant `gufraddeulacra-3396@yopmail.com` has no `users` row. The landing URL had `?applicationEmail=…&isBackdoor=true` and no `#applicantToken=` fragment.

## Root cause

SAN-2127 (`2adcbbb1`) added a branch to `modules/application_management/view_as_applicant.php`. For an admin session with no matching `users` row, it redirected to the plain pre-SAN-1959 link without asking the backend for an applicant token. Since SAN-1959, the PWA ignores `isBackdoor=true` without a token (`program-public-apply.component.ts`, `ensureApplicantToken()`) and prompts for the guest OTP. This happens in every `APPLICANT_TOKEN_MODE`.

## Fix

- `view_as_applicant.php`: removed the plain-link branch. An unregistered applicant now takes the applicant-token flow again: the backend mints a token, and the PWA receives it in the `#applicantToken=` fragment.
- Unchanged: the registered-applicant dashboard redirect (SAN-2127), and partner sessions, which keep the token flow for their own program only.
- `modules/application_management/module.spec.md`: updated the SAN-2127 paragraph.

## Verification

- `php -l modules/application_management/view_as_applicant.php`: no syntax errors.
- `composer gates`:
  - 0 for platform, composer, php-lint, auth-gates, ai-credit-writes, panel-hardening, sql-list-filters and xss-escapes;
  - 127 for phpstan and phpcs, which aren't installed locally. CI runs both.
- No `//` comments added.
- No automated test: sc-saas-admin has no test framework for page flows.
- To do after the dev deploy: Backdoor Access on application 1595 should open the form with no OTP prompt.

## Production note

Production is a separate problem. The production admin (26 Oct) calls `admin/applicant-token`, which the old production backends don't have yet: IEEMA's returns 404, shown as "This application or its program could not be found". It's fixed by building each production backend from `main`, as planned for SAN-1939.

## Commit

`03376424` on `sc-saas-admin` `ai_native_setup` (pushed 2026-10-29).
