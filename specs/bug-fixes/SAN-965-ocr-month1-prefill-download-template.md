---
id: SAN-965
title: OCR flow — Month 1 missing prefill on Verify & Submit + Download template hidden for Month 2+
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-965
project: Operational Cost Reimbursement — Slices 1-2 (Tripura)
repos: [frontend]
commit: sc-saas-frontend@2f7d95c6 (branch ai_native_setup_vishali, pushed)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-965 — OCR Month 1 prefill + Download template parity

## Classification
CODE_ERROR (step 2a) for both. Single-repo, `sc-saas-frontend` only — matches the issue's
`Repo: Frontend` label, no other repo touched. Both are genuine implementation gaps, not a design
ambiguity or environment issue — the codebase already has an established pattern (eligibility-driven
prefill from SAN-757's 2026-09-15 startup feedback, and Month 1's own "Download template" button)
that simply wasn't extended to the sibling component/form in each case.

## Root cause

**1. Month 1 missing prefill on reopen.** `OperationalCostReimbursementComponent.openVerifySubmitForm()`
(Month 2+) passes `eligibility.beneficiaryDetails` into `OcrVerifySubmitFormComponent.
existingBeneficiaryDetails`, which prefills the Beneficiary Details form fields. `openClaimForm()`
(Month 1) had no equivalent `@Input` at all — `OcrClaimFormComponent`'s form was always built with
hardcoded empty defaults (`ocr-claim-form.component.ts` `ngOnInit()`), so Month 1 could never show
previously-saved beneficiary details even when they already existed on the account (e.g. because
Month 2 was claimed first, per SAN-908's "a startup can claim any unlocked month at any time" rule).

**2. Download template missing for Month 2+.** `OcrClaimFormComponent` (Month 1) has always had a
"Download template" button next to its self-declaration upload. When `OcrVerifySubmitFormComponent`
(Month 2+) was built, its self-declaration step falls back to a real required upload whenever
`!hasExistingSelfDeclaration` (SAN-908 — this modal can legitimately be a startup's first-ever
submission) — but that upload state was never given a matching "Download template" control/output,
so a startup uploading self-declaration for the first time from Month 2+ had no in-app way to get the
template.

## Fix

- `claim-form/ocr-claim-form.component.ts` — added `@Input() existingBeneficiaryDetails:
  IOcrBeneficiaryDetails | null`; `ngOnInit()` now seeds every Beneficiary Details form control from
  it (`existing?.companyName ?? ''`, etc.), mirroring `OcrVerifySubmitFormComponent`'s existing
  pattern exactly. Still fully editable — this only seeds initial values.
- `operational-cost-reimbursement.component.ts` — `openClaimForm()` now takes `eligibility:
  IOcrEligibility` (the same object already available where `openVerifySubmitForm()` is called from
  the template) and sets `existingBeneficiaryDetails` on the opened modal instance.
- `operational-cost-reimbursement.component.html` — Month 1's `(click)="openClaimForm()"` →
  `(click)="openClaimForm(eligibility)"`.
- `verify-submit-form/ocr-verify-submit-form.component.ts` — added `@Output() downloadTemplate` +
  `onDownloadTemplate()`, mirroring `OcrClaimFormComponent` exactly.
- `verify-submit-form/ocr-verify-submit-form.component.html` — added the same "Download template"
  button/markup inside the existing `*ngIf="!hasExistingSelfDeclaration"` branch (the only state where
  there's actually a file left to collect).
- `operational-cost-reimbursement.component.ts` — `openVerifySubmitForm()` now also subscribes
  `componentInstance.downloadTemplate` to the same `downloadSelfDeclarationTemplate()` the Month 1
  modal already uses.

Deliberately NOT changed: Month 1's self-declaration upload stays unconditionally required (never made
optional/prefillable) — that's a different behavior than what was reported, and out of scope for a
narrowly-scoped fix. `IOcrEligibility.beneficiaryDetails`'s own doc comment (`operational-cost-
reimbursement.model.ts:107-114`) says it reflects "Month 1's submission, or a later Verify & Submit
edit" — this is backend-owned data (`sc-saas-backend`, out of scope for this frontend-labeled issue);
the fix here only makes the frontend actually consume whatever the backend already returns.

## Blast radius
Low, frontend-only, one feature module (`operational-cost-reimbursement`). No API/DTO, flag, or
tenant-scoping surface touched — no `/audit-contract`, `/trace-flag`, or `/check-isolation` applicable.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` — clean, no errors.
- `npx tsc --noEmit -p tsconfig.spec.json` — no *new* errors from these changes. This repo's spec
  suite already has pre-existing, unrelated compile errors across ~14 files, including this
  component's own spec (`operational-cost-reimbursement.component.spec.ts` instantiates
  `OperationalCostReimbursementComponent` with 6 constructor args when it now takes 8 — a drift
  predating this fix, unrelated to `openClaimForm()`'s signature). Existing `openClaimForm()` call
  sites in that spec were updated (mechanically, to pass an `eligibility` arg) to match the new
  signature so they don't add a *second*, unrelated compile error on top of the pre-existing one.
- No automated test run was possible given that pre-existing drift — noted rather than fixed here
  (separate housekeeping concern, out of this issue's scope). A regression test was proposed (not yet
  written, pending user go-ahead per the bug-fix flow's step 3): `ocr-claim-form.component.spec.ts` —
  assert `ngOnInit()` seeds `form.value` from a provided `existingBeneficiaryDetails` `@Input`, and
  `operational-cost-reimbursement.component.spec.ts` — assert `openClaimForm(eligibility)` passes
  `eligibility.beneficiaryDetails` through to the opened modal's `componentInstance`, and that
  `openVerifySubmitForm()` wires `componentInstance.downloadTemplate` the same way `openClaimForm()`
  already does.
- `npx ng build --configuration local` — full production build, exit 0, no `ERROR in` lines. This
  runs Angular's AOT template compiler (catches template-binding errors `tsc` alone can't see),
  covering both edited templates (`operational-cost-reimbursement.component.html`'s
  `openClaimForm(eligibility)` binding, `ocr-verify-submit-form.component.html`'s new button).
- Confirmed no other file in the repo references `openClaimForm`, `OcrClaimFormComponent`, or
  `OcrVerifySubmitFormComponent` outside this module — the signature change has no other call sites.
- Manual in-browser verification still pending (user will check both flows locally).

## Commit
`sc-saas-frontend@2f7d95c6` on `ai_native_setup_vishali`, pushed to origin.
