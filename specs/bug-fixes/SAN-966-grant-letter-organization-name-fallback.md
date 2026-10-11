---
id: SAN-966
title: "Grant release letter shows blank organization name for forms without explicit Company Name field wiring"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-966
repos: [admin]
commit: sc-saas-admin@5464ce9b
created: 2026-09-23
updated: 2026-09-23
---

# SAN-966 — Grant release letter blank organization name

## Request

The "Download Grant Release Letter" feature (Tri-Seed Fund / Tripura Start-Up Policy) rendered "We, , are
recognized under the Tripura Start-Up Policy..." with a blank organization name for a real production
application (#APP04485, company "Book Store").

## Root cause

`application_program_submission_rounds_view.company_name` (a passthrough of `forms_submissions.company_name`)
is only populated when a form's Company Name question is explicitly wired with `db_column_name=company_name`
in the form builder, or via a manual one-off "Company Name Migration" tool run per program. Neither is
guaranteed for every program. Some forms additionally have a SEPARATE custom "Company/Entity Name" question
with no DB-column wiring at all, so even a naive fallback restricted to the wired field could still come back
empty.

## Fix

`modules/application-submission-detail.php`'s `download_grant_letter` handler now resolves the organization
name in two fallback passes when the view's column is empty: (1) the field explicitly wired via
`getFormDetails()`'s `company_name_fields` (mirrors the existing `company_name_migration.php` tool's own
logic), then (2) if still empty, a broader label-based scan of every field on the form for one whose label
contains "name" plus company/entity/organization/organisation (matches labels like "Company/Entity Name" that
don't contain the literal phrase "company name"). Keeps scanning past a matched-but-empty field instead of
stopping at the first label match.

## Verification

`php -l` clean. Manually verified against the real form-field JSON for the affected program (a form with both
a custom "Company/Entity Name" field and an unrelated wired-but-blank system "Company Name" field) and against
two real applications' redownloaded PDFs, confirmed to now show the correct organization name.

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-admin@5464ce9b`.

## Open questions

None blocking.
