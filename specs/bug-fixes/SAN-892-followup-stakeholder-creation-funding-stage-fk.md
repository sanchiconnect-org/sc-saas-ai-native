---
id: SAN-892-followup
title: "startup_financials FK violation recurring on fresh tenants — second, unguarded write path found"
type: bug-fix
status: done
linear: [SAN-1012]
sentry: [SC-SAAS-BACKEND-4C, SC-SAAS-BACKEND-4D]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-29
updated: 2026-09-29
---

# SAN-892 follow-up — second startup_financials.funding_stage_id write path

## Root cause
SAN-892 (2026-09-22) found and fixed one write path for this FK violation: `sc-saas-admin/modules/csv/import.php`'s bulk CSV import inserted `startup_financials` rows without re-verifying `funding_stage_id` still existed in `funding_stages` at insert time. That fix (`sc-saas-admin@ef1d46b9`) is confirmed present and correct in the current codebase.

Despite that, the exact same Sentry group (`SC-SAAS-BACKEND-B`) produced two brand-new occurrences on two different tenant databases (`sc_saas_cii`, `sc_saas_firstwings`, 10-14 hours before this investigation) — after the CSV-import fix had already been live for a week. This meant a *second*, previously-unfound write path had to exist.

Found it: `sc-saas-admin/includes/stakeholder_account_creation_funcs.php:1575` — the stakeholder-account-creation flow (converting an approved application into a full startup record) does its own independent `startup_financials` insert, and copied `$recordData["funding_stage_id"]` (stored application-submission data, which can go stale between submission and this later insert if the funding stage was deactivated/removed in the interim) straight into the insert with zero verification. This path was never covered by SAN-892's investigation, which only traced the CSV-import and sc-saas-backend write paths.

## Fix
Added the same defensive re-verification pattern SAN-892 already established for the CSV import: right before the `startup_financials` insert, look `funding_stage_id` up in `funding_stages` again, and null it out if it no longer exists, rather than trusting the stored application data unconditionally.

## Blast radius
Single file, single insert site. No change to any other field or to the CSV-import path (already fixed separately).

## Verification
`php -l` clean (via PowerShell — no `php` binary in the Bash environment). No test suite exists for this repo.

## Rollout
`SAN-1012` (the Linear ticket auto-created for these new occurrences, same Sentry group as SAN-892) closed as a duplicate/continuation of this fix rather than a new investigation.

## Open questions
None — but worth a wider one-time grep for `$database->insert(` sites writing any other FK column sourced from stored/stale data, in case a third path exists. Not done in this pass; flagging for later if this recurs a third time.
