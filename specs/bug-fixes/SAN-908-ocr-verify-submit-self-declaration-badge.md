---
id: SAN-908
title: "OCR Verify & Submit — false Self-Declaration badge; can't handle a first claim on month 2+"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-908
repos: [backend, frontend]
commit: sc-saas-backend@3811fbc9, sc-saas-frontend@6b693825
created: 2026-09-22
updated: 2026-09-22
---

# SAN-908 — OCR Verify & Submit self-declaration bug

## Request

Startup-reported, via screenshots of `/schemes/operational-cost-reimbursement`: Month 1's "Apply" modal
correctly showed an empty Self-Declaration upload, but Month 2's "Verify & Submit" modal showed
"Self-Declaration (includes Shareholding Pattern) — Uploaded" with a green checkmark, even though the
startup had never submitted any claim at all. User's own words: *"startup not applied for any claim but for
month 2 showing Self-Declaration document uploaded. startup can apply any of month at any time if month
unlocked."*

## Root cause

Two layers, both traced to the same wrong assumption — that Verify & Submit (Month 2 onward) always has a
prior claim to carry category/documents forward from:

1. **Frontend (cosmetic symptom):** `OcrVerifySubmitFormComponent`'s template hardcoded the Self-Declaration
   row as unconditionally "Uploaded" — no `*ngIf` at all — unlike the already-correct
   `hasExistingBankChequeOrPassbook` pattern right next to it (fixed 2026-09-15 for a near-identical
   startup-reported bug on the bank cheque/passbook field, but never mirrored onto Self-Declaration).
2. **Backend (real functional bug, more serious):** `OperationalCostReimbursementService.verifySubmitClaim()`
   unconditionally required a prior claim (`priorClaims.length > 0`) to carry forward from, throwing
   `BadRequestException('No prior submission found to carry forward — submit Month 1 first.')` otherwise.
   Since a startup can apply for any unlocked month at any time (confirmed by the user, not just a UI
   nicety), a startup whose first-ever submission is month 2+ would see the false "Uploaded" badge and then
   get a confusing 400 on actual submit.

Presented the design question to the user (AskUserQuestion): when there's no prior claim, should Verify &
Submit (a) treat it as a fresh application (collect its own self-declaration/bank cheque, like Month 1's
Apply form), or (b) keep forcing Month 1 first and just fix the badge/messaging. User chose (a).

## Fix

### Backend (`sc-saas-backend`)

- `operational-cost-reimbursement.repository.ts` — new `hasDocumentOfType(claimIds, documentType)`.
- `operational-cost-reimbursement.service.ts`:
  - `getEligibility()` — added `hasSelfDeclarationOnFile`, computed by checking whether ANY of the startup's
    claims (any month/status) has a `SELF_DECLARATION` document, same pattern as the existing
    `hasBankChequeOrPassbookOnFile`. Set to `false` in the `unavailable`/`locked` early-return states, same
    as that field.
  - Extracted `uploadNewClaimDocuments()` (shared by `submitClaim()` and the new branch below) from
    `submitClaim()`'s inline upload logic — no behavior change there, pure refactor to avoid duplicating the
    "self-declaration lands as two document rows" logic (BRD §22).
  - `verifySubmitClaim()` — when `priorClaims.length === 0`, no longer throws. Instead requires a
    `selfDeclarationFile`, defaults `category` to `GENERAL` (mirrors `submitClaim()` and the 2026-09-17
    product decision removing category selection from the UI), and uploads a fresh document set via
    `uploadNewClaimDocuments()`. When a prior claim DOES exist, behavior is unchanged (carry-forward).
- `operational-cost-reimbursement.controller.ts` — `claims/:monthIndex/verify-submit` now also accepts an
  optional `selfDeclaration` file field (`FileFieldsInterceptor`), passed through to the service.

### Frontend (`sc-saas-frontend`)

- `core/domain/operational-cost-reimbursement.model.ts` — `IOcrEligibility.hasSelfDeclarationOnFile: boolean`;
  `IOcrVerifySubmitClaimPayload.selfDeclaration?: File`.
- `core/service/operational-cost-reimbursement.service.ts` — `verifySubmitClaim()` appends `selfDeclaration`
  to the multipart body when present.
- `operational-cost-reimbursement.component.ts` — `openVerifySubmitForm()` passes
  `hasExistingSelfDeclaration` through to the modal.
- `verify-submit-form/ocr-verify-submit-form.component.ts`/`.html` — new `@Input() hasExistingSelfDeclaration`,
  `selfDeclaration: File | null` state; template shows the read-only "Uploaded" row only when
  `hasExistingSelfDeclaration` is true, otherwise a required upload input (mirrors the bank cheque/passbook
  block). `onSubmit()` blocks with a toast if neither an existing nor a newly-chosen file is present.
  `onFileSelected()` now takes a `slot` param (`'bankChequeOrPassbook' | 'selfDeclaration'`), matching
  `OcrClaimFormComponent`'s existing two-file pattern.

## Verification

- Backend: `npx tsc --noEmit -p tsconfig.json` clean. `npx eslint` on the three touched files: 0 errors
  (only the repo's known pre-existing unused-import warnings from single-file lint invocation).
- Frontend: `npx tsc --noEmit -p tsconfig.json` clean, after also updating several pre-existing `*.spec.ts`
  fixture literals (`operational-cost-reimbursement.reducer.spec.ts`,
  `.selectors.spec.ts`, `.component.spec.ts`) that needed the new required `hasSelfDeclarationOnFile` field.
  No lint configured in this repo (per its own CLAUDE.md).
- No automated regression test added in either repo yet — both have working test frameworks (Jest / Jasmine),
  so per the bug-fix process a test should be proposed and only written on the user's go-ahead; not yet
  requested in this pass.

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-backend@3811fbc9`, `sc-saas-frontend@6b693825`.

## Open questions

None blocking — the one open design question (how Verify & Submit should behave with no prior claim) was
resolved via `AskUserQuestion` during implementation; see Root cause above.
