---
id: SAN-965 (+ SAN-971)
title: OCR Month 1 Application re-asks for Self-Declaration / cheque already on file
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-965 , https://linear.app/sanchiconnect/issue/SAN-971
repos: [frontend, backend]
assignee: Mahima Sharma
created: 2026-09-24
updated: 2026-09-24
---

# SAN-965 / SAN-971 — Month 1 should show Self-Declaration as Uploaded when it's already on file

## Problem

A startup can claim any unlocked month first (SAN-908). After claiming Month 2 first, the Month 2+ Verify & Submit modal correctly shows "Self-Declaration — Uploaded". But the **Month 1 — Application** modal still showed "No file chosen — upload the signed copy" (required) and asked for the cheque/passbook again.

(SAN-965's first two items were fixed earlier in `sc-saas-frontend` commit `2f7d95c6`: Month 1 prefill of Beneficiary Details, and Download template on Month 2+. This record covers the third item, added 2026-09-24.)

## Classification

CODE_ERROR. Month 1 was built on the assumption that it's always a startup's first claim, which SAN-908 made false.

## Root cause

- Frontend `OcrClaimFormComponent` had no inputs for `IOcrEligibility.hasSelfDeclarationOnFile` / `hasBankChequeOrPassbookOnFile` and always required both uploads. `OcrVerifySubmitFormComponent` already honored both flags.
- Backend `submitClaim()` always threw 400 when the files were missing, so a frontend-only fix would have been rejected.

## Fix

**sc-saas-backend (SAN-971)** — `operational-cost-reimbursement.service.ts` `submitClaim()`:
- No new `selfDeclaration` → carry forward the SELF_DECLARATION + SHAREHOLDING rows from the most recent prior claim (same S3 `filePath`, no re-upload). Still returns 400 if none exists.
- No new `bankChequeOrPassbook` → reuse `operational_cost_bank_details.chequeOrPassbookImage`. Still returns 400 if none exists.
- `module.spec.md` updated.

**sc-saas-frontend (SAN-965)**:
- `ocr-claim-form.component.ts/.html/.scss`: new `hasExistingSelfDeclaration` / `hasExistingBankChequeOrPassbook` inputs. When set, the form shows the same read-only "Uploaded" row as Verify & Submit, and the upload isn't required. The cheque can still be replaced.
- `operational-cost-reimbursement.component.ts` `openClaimForm()`: passes both flags from eligibility.
- `operational-cost-reimbursement.model.ts`: `IOcrSubmitClaimPayload.selfDeclaration` / `bankChequeOrPassbook` made optional.
- `operational-cost-reimbursement.service.ts` `submitClaim()`: appends each file only when present.

## Contract impact

`POST api/v1/operational-cost-reimbursement/claims`: the two file fields change from always-required to required only when nothing is on file. Validation only gets looser, so callers that send both files see no change. The only consumer is the frontend OCR claim form (sc-saas-admin doesn't call it).

**Deploy order:** backend first. The new frontend omits the files when they're on file, and the old backend would reject that with 400.

## Verification

- Backend: `tsc --noEmit` clean; eslint shows 0 errors (3 old warnings, not on changed lines); OCR service spec passes 77/77 (existing tests; no new regression test written yet).
- Frontend: `tsc --noEmit -p tsconfig.app.json` clean. The Karma suite can't compile because of 16 old spec errors (CometChat specs, plus `operational-cost-reimbursement.component.spec.ts:80`), so no frontend tests ran. The repo has no lint setup.
- Manual repro in the browser not done yet.

## Commit

- sc-saas-backend: `32904885` on `ai_native_setup_vishali`. It was first pushed to `ai_native_setup` by mistake as `4401e911`; that was reverted by `557f1da9` and the commit was cherry-picked here.
- sc-saas-frontend: pending (not committed).
