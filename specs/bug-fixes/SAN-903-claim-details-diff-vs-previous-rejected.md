---
id: SAN-903
title: "Claim Details — show diff vs. previous rejected claim on resubmission"
type: feature
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-903
sentry: []
repos: [admin, backend]
commit: sc-saas-backend@8f8c5408, sc-saas-admin@b33383f7 (branch ai_native_setup_vishali)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-903 — Claim Details diff on resubmission

## Requirement
When a startup's claim is rejected and they resubmit, the new claim's "Claim Details" modal should show what actually changed vs. the immediately-preceding rejected claim — Beneficiary Details field-by-field, and Documents — not just the new claim's data in isolation.

## Blocker found + resolved (see [SAN-904](https://linear.app/sanchiconnect/issue/SAN-904), `sc-saas-backend`, companion ticket)
Beneficiary Details was one row per startup, upserted in place — a rejected claim's original values were already gone by the time a resubmission existed to diff against. SAN-904 snapshots the 11 Beneficiary Details fields onto `operational_cost_claims` itself at submit time and has `getClaimDetails()` return the previous rejected claim (with its own snapshot + documents) as `previousRejectedClaim`. This ticket is the admin-side rendering of that data — it depends on SAN-904 having landed.

## Fix
`sc-saas-admin`'s proxy (`modules/operation_cost/claims.php`'s `details` route) needed **no change** — it's a pure pass-through of the backend's `data` object, so the new `previousRejectedClaim` field flows through automatically.

`themes/default/html/operation_cost/claims.php`:
1. New card "Changes Since Last Rejected Claim" in the Claim Details modal's Beneficiary Details column, `display:none` by default — only shown when `data.previousRejectedClaim` is present.
2. `renderClaimDiff(currentBankDetails, currentDocuments, previous)` (new JS function):
   - Shows the previous claim's rejection date + reason as context.
   - If `previous.bankDetails` is `null` (pre-SAN-904 claim, no snapshot), shows "prior data unavailable" instead of a false/empty diff.
   - Otherwise, walks the same 11 fields the Beneficiary Details card itself renders (same `{label, key}` list, same order — so the diff reads as a direct companion, not a re-derived list that could drift), shows `old → new` only for fields that actually differ, and "No Beneficiary Details changed" when none did.
   - Documents diff: compares `originalFileName` per `documentType` between the two claims (added/removed/changed) — filename is the only practical comparison signal available client-side, since no raw storage key is ever sent to the browser and the signed `url` is freshly re-signed on every load (can't be compared directly).
3. Wired into the existing `loadClaimDetails()`/`resetDetailsModal()` flow: reset hides/clears the new card; `renderClaimDiff()` runs after the current claim's own Beneficiary Details and Documents are already populated (it compares against them).

### Follow-up — show the full previous submission, not just changed fields (2026-09-22)
Admin-reported feedback after seeing it live: a changed-fields-only list didn't give enough context to judge what was actually wrong in the rejected submission. Redesigned `renderClaimDiff()`'s field rendering: now lists **all 11** Beneficiary Details fields (was: only the ones that differed), one `ocr-detail-row` per field — same label-left/value-right layout the main Beneficiary Details card itself uses, so it reads as "the last submission, in full" rather than a derived list. A changed field shows the old value struck through (red) → the new value bolded (green); an unchanged field shows its value once, plainly. The meta line now also summarizes "N fields changed" / "no Beneficiary Details changed". HTML: replaced the `<ul id="ocrDetailDiffFields">` + separate "no change" message with a single `<div id="ocrDetailDiffFieldRows">` container built entirely in JS. The "prior data unavailable" fallback (claims predating the SAN-904 snapshot) is unchanged.

### Follow-up — two-tab redesign: full "Previous Submission" view + a real diff table (2026-09-22)
Reference mockup supplied directly by the user: a **Current Submission / Previous Submission (Last Rejected)** tab pair, each tab showing the complete claim detail (Status Timeline, Claim Details, Documents, Beneficiary Details) for that specific submission — not just an inline card appended to the current view. Rebuilt accordingly:

**Backend** (companion change to [SAN-904](https://linear.app/sanchiconnect/issue/SAN-904)): `getClaimDetails()`'s `previousRejectedClaim` now also returns `monthIndex`, `periodStart`, `periodEnd`, `category`, `amount`, `claimStatus`, and its own `timeline` (built via a new shared `buildTimeline()` helper, extracted from the inline logic already used for the current claim) — everything needed to render that claim's own full detail cards, not just a Beneficiary Details diff. Full existing suite re-verified: 82/82 passing (77 service + 5 controller), no regressions from this expansion.

**Admin** (`themes/default/html/operation_cost/claims.php`):
- New `<ul class="nav nav-tabs">` pair above the existing two-column layout — "Current Submission" (default) and "Previous Submission" with a "Last Rejected" badge, the second tab hidden entirely unless `data.previousRejectedClaim` exists.
- Wrapped the existing Current-tab markup in `#ocrCurrentSubmissionView` (unchanged internals).
- New `#ocrPreviousSubmissionView` mirrors that same card structure (Status Timeline/Claim Details/Documents/Beneficiary Details) with its own element IDs (`ocrPrevDetail*`), populated from `previousRejectedClaim` by a new `populatePreviousSubmissionView(data, previous)` function that replaces the old `renderClaimDiff()`. A banner at the top reads "Last Submitted Claim — [date] · Status: Rejected — '[reason]'".
- The Beneficiary Details diff moved into a real `<table>` (Field / Change Status / Previous Value / Current Value, per the mockup) inside the Previous tab, alongside a plain full-value listing (`#ocrPrevDetailBankRows`) so the tab reads as "the last submission, in full" AND shows the diff.
- Delegated click handlers toggle the two view containers; `resetDetailsModal()` extended to reset every new element and default back to the Current tab on each modal open.

**Known, accepted gap**: the previous claim's Documents card can't show a Bank Cheque/Passbook entry — that file reference lives on the per-startup `bank_details` row, not snapshotted per claim (SAN-904 only covers the 11 non-file fields), so it isn't recoverable for a prior claim. Self-Declaration/Shareholding ARE already claim-scoped and show normally. Not silently worked around — just genuinely unavailable, same category of limitation as the "prior data unavailable" case.

### Follow-up — backend piece pushed; clarified the null-bankDetails confusion (2026-09-22)
User tested live and saw `previousRejectedClaim.bankDetails: null` in the actual API response, plus a Previous tab missing month/timeline — asked why. Two separate things, both expected:
1. `bankDetails: null` for that specific claim is correct — it was rejected 17 Sep, before the SAN-904 snapshot code existed anywhere live, so nothing was ever recorded for it. Not recoverable, already the confirmed-acceptable behavior.
2. The `monthIndex`/`timeline`/etc. expansion (this doc's previous follow-up) was still sitting uncommitted locally — not live on whatever backend served that response. Pushed now: `sc-saas-backend@8f8c5408`.

To see a REAL working diff (not "prior data unavailable"), the test needs a claim pair created entirely after `sc-saas-backend@2a7bc62e` (the original SAN-904 snapshot commit) went live wherever this is being tested — e.g. reject the "submitted" claim from today, then have it resubmitted; that resubmission's `previousRejectedClaim` should have a real, non-null `bankDetails` snapshot.

### Follow-up — UI polish: documents alignment, diff table density, tab style (2026-09-22)
Three small fixes after live review:
1. **Documents row alignment**: `.ocr-detail-documents li` used `justify-content: space-between` across 3 flex children (icon, label, View link) — this spread BOTH gaps evenly, drifting the label away from its own icon instead of sitting flush against it. Changed to `justify-content: flex-start` + `margin-left: auto` on `.ocr-doc-view`, so icon+label stay tight on the left and only the View link gets pushed right.
2. **Diff table too large**: `#ocrDetailDiffTable` inherited the modal's ~14-15px default text. Added scoped CSS: 12px body text, 11px uppercase headers, 10px badges — matching the modal's other compact text (`.ocr-detail-documents` is already 13px).
3. **Tab bar restyled**: replaced Bootstrap's default boxed `nav-tabs` look with a flat underline style per a direct reference mockup — single hairline under the whole bar, inactive tab in gray, active tab in primary-color text with its own bold underline. The "Last Rejected" badge switched from an undefined `badge-light-danger` class to this module's own already-styled `ocr-pill ocr-pill-danger` (same small red pill used elsewhere on this page), rather than introducing an unverified new class.

### Follow-up — hide the Previous Submission tab entirely when there's no real data (2026-09-22)
**Supersedes** the "do not hide it" note in the Design notes section above — that caution was against silently hiding/backfilling unprompted; this is a direct, explicit user instruction: "jiska preview data nhi h usko preview tab nhi show hogi" (a claim with no preview data shouldn't show the preview tab at all). `populatePreviousSubmissionView()`'s guard changed from `if (!previous)` to `if (!previous || !previous.bankDetails)` — the tab (and its "Last Rejected" badge) now only ever appears when there's a real snapshot to show, never leading into an "unavailable" dead end. Removed the now-unreachable `#ocrPrevDetailBankUnavailable`/`#ocrDetailDiffUnavailable` elements and their reset/populate code entirely (dead code, not just hidden) — including from the HTML, not just the JS.

## Design notes / limitations (confirmed acceptable with the user before building, RE-CONFIRMED 2026-09-22 after seeing it live, UPDATED again same day — see hide-tab follow-up above)
- Diff only works going forward from SAN-904 landing — existing already-rejected claims have no snapshot. Originally shown as "prior data unavailable" inside the tab; **now the tab itself is hidden entirely for these claims** (see follow-up above) — not recoverable, no diff possible, so nothing to show a tab for.
- Documents diff is by filename, not byte-for-byte content — a re-upload of a file with the identical name would not show as "changed". Judged acceptable; over-engineering a content-hash comparison wasn't asked for and the backend doesn't currently store one.

## Blast radius
Only the Claim Details modal (its tab bar + the two view containers + their JS). No change to the claims list/table, filters, counters (SAN-902), bulk actions, or the Reject/Sanction action bar.

## Verification
No PHP linter available locally — reviewed the diff by hand at every step: HTML tags balance, JS braces/parens balance (also confirmed via `new Function()` on the extracted, PHP-tag-stripped script block after each round), reuses existing CSS classes/variables (`ocr-detail-card`, `ocr-detail-documents`, `ocr-doc-label`, `ocr-pill-danger`, `--primary`/`--gray-*`) rather than introducing unverified ones. No test framework exists in this repo. Depends on SAN-904's backend response shape — verified against that ticket's actual `getClaimDetails()` return shape, not guessed. Committed and pushed: `sc-saas-admin@b33383f7` (branch `ai_native_setup_vishali`), after user review.
