---
id: SAN-961
title: Claim Details modal — "Changes Since Last Rejected Claim" diff card shown on wrong tab
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-961
project: Operational Cost Reimbursement — Slices 1-2 (Tripura)
repos: [admin]
commit: sc-saas-admin@3053cb17 (branch ai_native_setup_vishali, pushed)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-961 — OCR Claim Details diff card on wrong tab

## Classification
CODE_ERROR (step 2a). Single-repo, `sc-saas-admin` only — matches the issue's `Repo: Admin` label,
no other repo touched.

## Root cause
`sc-saas-admin/themes/default/html/operation_cost/claims.php` — the "Changes Since Last Rejected
Claim" diff card (`#ocrDetailDiffTable`) was placed inside `#ocrPreviousSubmissionView` (the
Previous Submission tab's markup), so it only ever rendered while that tab was active, showing a
"previous vs current" diff underneath the *previous* claim's own read-only detail — the diff belongs
with the submission it's evaluating (Current), not the historical one being compared against.

The diff itself was always populated correctly (`populatePreviousSubmissionView()` already compares
`previous.bankDetails` against `data.bankDetails`, i.e. current) — this was a DOM-placement bug only,
not a data bug.

## Fix
Moved the diff card's markup (`#ocrDetailDiffTable` / `#ocrDetailDiffTableBody` / `#ocrDetailDiffDocuments`,
same IDs, same jQuery population code untouched) from the right column of `#ocrPreviousSubmissionView`
into the right column of `#ocrCurrentSubmissionView`, after the Beneficiary Details card. No JS
changes were needed: `populatePreviousSubmissionView()` selects these elements by ID regardless of
where they sit in the DOM, and `resetDetailsModal()` already hides the table by default each time the
modal opens — so a claim with no previous rejected submission (or one predating the SAN-904
bankDetails snapshot) still shows no diff card, same as before, just now correctly absent from a tab
that no longer contains it rather than a tab that now doesn't render it.

### Follow-up (same session): empty header still showing for claims with no previous rejection
User caught a second bug live in the browser (screenshot: startup "maya", first-time SANCTIONED claim,
no prior rejected submission): the outer `.ocr-detail-card` wrapper (header + body) was never itself
hidden — only the inner `#ocrDetailDiffTable`/`#ocrDetailDiffDocuments` were toggled via `resetDetailsModal()`
/ `populatePreviousSubmissionView()`. So a claim with nothing to diff still rendered an empty
"CHANGES SINCE LAST REJECTED CLAIM" card with just a header and no content.

Fix: gave the card itself an id (`#ocrDetailDiffCard`, `style="display:none"` by default) and toggled
the whole card, not just its inner table: `resetDetailsModal()` now hides `#ocrDetailDiffCard` too, and
`populatePreviousSubmissionView()` shows it alongside `#ocrDetailDiffTable` only when a previous
rejected claim with `bankDetails` exists. The early-return guard (no previous claim / no bankDetails)
already exits before touching either element, so the card correctly stays fully hidden in that case.

## Blast radius
Low, admin-only, single template file. No API/DTO, flag, or tenant-scoping surface touched — no
`/audit-contract`, `/trace-flag`, or `/check-isolation` applicable to this change.

## Verification
- Re-read the edited file to confirm the moved HTML block is well-formed (matching open/close divs
  in both the Current and Previous view columns).
- `php -l` via the local XAMPP PHP binary — no syntax errors (re-run after the follow-up fix too).
- No automated test — `sc-saas-admin` has no test framework (per the bug-fix flow's step 3, this gap
  is noted rather than bootstrapping test infra as a side effect).
- The follow-up (empty card) was caught by the user's own live click-through in the browser
  (`admin.localhost/operation_cost/claims`), not by this session — user confirmed the fix before it
  was committed and pushed.

## Commit
`sc-saas-admin@3053cb17` on `ai_native_setup_vishali`, pushed to origin.
