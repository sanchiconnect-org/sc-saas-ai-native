---
id: SAN-976
title: OCR Claim Details hides the "Previous Submission" tab when the rejected claim has no Beneficiary Details snapshot
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-976
repos: [admin]
assignee: Mahima Sharma
created: 2026-09-24
updated: 2026-09-24
---

# SAN-976 — always tell the admin the month was rejected before

Companion to SAN-975 (backend now returns only the **same month's** previous rejected claim).

## Problem

Admin `/operation_cost/claims` → View Details. When a startup re-applied for a month that had been rejected, the admin often saw no sign of the earlier rejection. Reported case: Vami Dummy, Month 9, TR26-ELMA2-000015, on dev.

## Classification

CODE_ERROR.

## Root cause

`populatePreviousSubmissionView()` in `themes/default/html/operation_cost/claims.php` returned early when `previousRejectedClaim.bankDetails` was null, which hid the whole "Previous Submission" tab. `bankDetails` is null for any rejected claim without a Beneficiary Details snapshot: rows created by **Migrate Offline Claim**, and claims submitted before SAN-904.

## Fix (sc-saas-admin, `themes/default/html/operation_cost/claims.php`)

- The tab now shows whenever `previousRejectedClaim` exists. When there's no snapshot, Beneficiary Details reads "not recorded for this claim", and the diff card stays hidden because there's nothing to compare. With a snapshot, behavior is unchanged.
- New red notice at the top of the **Current Submission** view: "Month N was previously rejected on <date> — "<reason>". See the Previous Submission tab for details." This way the admin sees it without opening the tab. It's cleared in `resetDetailsModal()`.

## Follow-up (2026-09-24, after dev check)

Once deployed, the notice showed correctly, but the user wanted the rejected claim's **details** in the same view, without switching tabs. Added a "Previously Rejected Claim — Month N" card right under the notice on the Current Submission view (`populatePreviousInlineCard()`). It shows the rejected claim's status timeline, rejection reason, documents, and Beneficiary Details, or "Not recorded for this claim" when there's no snapshot. The notice text now says "Its details are shown below." The Previous Submission tab and the diff are unchanged.

## Verification

- No `php` binary locally, so `php -l` couldn't run. The page's inline JS was extracted (PHP tags stubbed out) and passes `node --check`.
- sc-saas-admin has no test framework.
- Manual check in the browser not done yet. It needs the SAN-975 backend deployed too.

## Commit

- sc-saas-admin `4de7468a` (notice + tab visibility) on `ai_native_setup_mahima`.
- Inline-details follow-up: pending (not committed).
