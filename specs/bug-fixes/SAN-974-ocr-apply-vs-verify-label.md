---
id: SAN-974
title: OCR month cards — "Apply" on every month until the first claim, then "Verify & Submit" on every month
type: improvement
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-974
repos: [frontend]
assignee: Mahima Sharma
created: 2026-09-24
updated: 2026-09-24
---

# SAN-974 — OCR button label depends on "has the startup ever claimed", not on the month number

## Request

On `/schemes/operational-cost-reimbursement`, Month 1 always showed **Apply** and Months 2–12 always showed **Verify & Submit**. A startup that had never claimed anything saw "Verify & Submit" on Month 2+ with nothing to verify. Requested rule:
- No claim on any month → every unlocked month shows **Apply**.
- At least one claim (any month, any status) → every claimable month shows **Verify & Submit**, including Month 1.
- A Rejected month keeps **Re-apply**.

## Fix (sc-saas-frontend, label/title only)

- `operational-cost-reimbursement.component.ts`: new `hasAnyClaim(eligibility)` returns true if any `months[].claim` exists. `openClaimForm()` and `openVerifySubmitForm()` pass it to the modal as `hasAnyClaim`.
- `operational-cost-reimbursement.component.html`: the Month 1 and Month 2+ button labels both use `hasAnyClaim(eligibility) ? 'Verify & Submit' : 'Apply'`. The Re-apply label is unchanged.
- `claim-form/ocr-claim-form.component.ts/.html` and `verify-submit-form/ocr-verify-submit-form.component.ts/.html`: new `hasAnyClaim` input, and the modal title reads "Month N — Application" or "Month N — Verify & Submit" by the same rule.

Which form opens and which endpoint it calls are unchanged. Month 1 still uses `POST claims`, and Months 2–12 still use `POST claims/:monthIndex/verify-submit`. No API contract change.

## Verification

- `tsc --noEmit -p tsconfig.app.json` clean; `ng build --configuration development` compiles (templates included).
- The Karma suite can't compile because of old spec errors, so no automated tests ran.
- Manual check in the browser not done yet.

## Commit

Pending (not committed).
