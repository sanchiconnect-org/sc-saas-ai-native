---
id: SAN-843
title: "Allow admin to edit the Recognition Generated date on startup detail"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-843
repos: [admin]
commit: sc-saas-admin@ba5c9be0 (ai_native_setup)
created: 2026-09-17
updated: 2026-09-17
---

# SAN-843 — Recognition Generated date manual edit

## Request

The Startup/MSME detail page's existing Recognition ID/Year manual-edit widget (`themes/default/html/startup-detail/startup-detail.php`)
let an admin correct `recognition_id`/`recognition_year` but showed `recognition_generated_at` ("Generated: ...") as plain
read-only text, by explicit original design ("serial_no/suffix/generated_at stay read-only display only — this action never
touches them"). Explicit follow-up request: let the admin edit the Generated date too.

## Why this needed care, not just a quick field add

`recognition_generated_at` is not a cosmetic display field — `sc-saas-backend`'s OCR eligibility-month calculation
(`operational-cost-reimbursement.service.ts`) reads this exact column as the scheme's start date to compute the 12 monthly
claim windows. The sibling column `recognition_regenerated_at` must NEVER be used as a fallback for this (it's null on a
startup's first recognition — a real bug already hit and fixed earlier this same week in the OCR feature itself). Editing
this field here therefore directly shifts which OCR claim months are unlocked for that startup, which is why both the
backend handler's own comment and the UI's helper text now say so explicitly.

## Fix

**Backend** (`modules/startup-detail.php`, `submitAction: updateStartupRecognitionId`):
- Reads a new optional `recognitionGeneratedAt` POST field. Blank leaves the existing value untouched (same "blank = leave
  untouched" convention already used for Year), so an admin correcting just the ID/Year isn't forced to also retype a
  timestamp they don't want to change.
- Validates via `strtotime()`; a value that doesn't parse returns a clear error rather than silently storing garbage.
- Stores normalized as `Y-m-d H:i:s`.
- Includes the old/new value in the existing `createAdminLogs()` audit-log call.
- Returns the new value in the JSON response so the UI can update its view-mode display without a full reload.

**Template** (`themes/default/html/startup-detail/startup-detail.php`):
- Added a "Generated" text input (`YYYY-MM-DD HH:MM:SS` placeholder) to the existing edit-mode row, alongside Recognition ID
  and Year.
- Gave the view-mode "Generated:" text a stable `id` (`srIdViewGeneratedAt`) so it can be updated live on save, matching how
  ID/Year already worked.
- Extended the existing JS two-state (view/edit) toggle: remembers the last-saved value for Cancel, sends it in the same
  `$.post()` call, and updates the view display from the response.

Same role gate as the existing widget (`srIdCheckRole()` — Super Admin/Owner or Developer Admin only) — no new gating
introduced.

## Blast radius

Two files in `sc-saas-admin`, one existing endpoint extended (backward compatible — omitting the new field behaves exactly
as before). No entity/DTO change, no new endpoint, no change to any OTHER consumer of `recognition_generated_at`
(`sc-saas-backend`'s OCR eligibility logic reads whatever value is in the column regardless of how it got there — this
feature doesn't change that logic, just who can set the value and how).

## Verification

`php -l` clean on both touched files. No automated test suite exists for this repo (documented workspace-wide
limitation) — manual QA substitutes: with the role gate satisfied, opened the widget, entered a new Generated date,
saved, confirmed the view-mode text and the audit log both reflect the new value; left the field blank on a
separate edit and confirmed the existing value was untouched.

## Rollout

Committed and pushed as `sc-saas-admin@ba5c9be0` ("feat: allow admin to edit Recognition Generated date on startup detail")
on `ai_native_setup`.

## Open questions

None blocking. Product/ops should be aware that backdating this field for a startup with existing OCR claims can retroactively
change which months were ever unlocked — no reconciliation of already-submitted claims happens automatically when this field
changes after the fact.
