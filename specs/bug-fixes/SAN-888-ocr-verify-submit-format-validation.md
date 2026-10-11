---
id: SAN-888
title: "OCR Verify & Submit — add inline format validation for IFSC Code, PAN Number, Beneficiary Email ID"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-888
sentry: []
repos: [frontend]
commit: sc-saas-frontend@523ab4a0 (branch ai_native_setup_vishali)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-888 — OCR Verify & Submit inline format validation

## Root cause
CODE_ERROR (missing validation, not broken behavior) — `panNumber`, `bankIfscCode`, and `beneficiaryEmail` on the OCR "Verify & Submit" form (`ocr-verify-submit-form.component.ts`) only had `Validators.required`; no format/pattern check existed, so any string (including one obviously not a valid PAN/IFSC/email) passed submit-time validation and reached the backend as-is. Confirmed via full read of the component: no `hasError()`/error-display convention existed anywhere in the OCR module (`ocr-verify-submit-form` or its sibling `ocr-claim-form`) to reuse, and no IFSC/PAN regex existed anywhere in this repo (grepped case-insensitively for `ifsc`/`PAN_`/`panPattern`/`ifscPattern` — zero hits beyond the field/control names themselves).

## Fix
Reused the app's existing shared-validator convention (`src/app/shared/constants/regex.ts`, already home to `EMAIL_PATTERN` and other `Validators.pattern(...)` constants, consumed by the signup flow's `account-information.component.ts`) instead of introducing a one-off implementation:

1. **`shared/constants/regex.ts`** — added two new constants, following the file's existing naming/export convention:
   - `IFSC_CODE_PATTERN = Validators.pattern(/^[A-Za-z]{4}0[A-Za-z0-9]{6}$/)` — standard RBI IFSC shape (4 letters, literal `0`, 6 alphanumeric = 11 chars), case-insensitive.
   - `PAN_NUMBER_PATTERN = Validators.pattern(/^[A-Za-z]{5}[0-9]{4}[A-Za-z]$/)` — standard Indian PAN shape (5 letters, 4 digits, 1 letter), case-insensitive.
   - `beneficiaryEmail` reuses the existing `EMAIL_PATTERN` (same one signup's account-information step already uses) — no new email regex.
2. **`ocr-verify-submit-form.component.ts`** — added the corresponding pattern validator alongside the existing `Validators.required` for all three controls (`ngOnInit()`'s `fb.group({...})` call). No other controls, `onSubmit()`'s existing `form.invalid` gate, or the dispatched payload shape were touched — new validators flow into `form.invalid` automatically, same as any other reactive-forms validator.
3. **`ocr-verify-submit-form.component.html`** — added the app's existing signup-page `is-invalid`/`is-valid` (`[ngClass]`, keyed off `.valid` + `.touched`/`.dirty`) + `invalid-feedback` span convention (copied from `account-information.component.html`'s email field) to the three fields' inputs, so invalid format shows inline on blur/input, before submit — this was the first per-field error-display UI introduced into the OCR module (none existed there before), but it matches what's already standard elsewhere in the app rather than inventing a new pattern.

Format validation only — no OTP/existence check, no external verification call, per the ticket's own scope.

### Existing-test fixture fix (required to avoid breaking currently-passing tests)
`ocr-verify-submit-form.component.spec.ts`'s `fullFormValue()` fixture used `bankIfscCode: 'HDFC0001'` — only 8 characters, which does **not** match a real 11-character IFSC and would fail the new `IFSC_CODE_PATTERN`, silently breaking 3 already-passing tests that rely on `fullFormValue()` producing a valid form (`dispatches VerifySubmitClaim...`, `includes a new cheque/passbook file...`, `does not resubmit while a submission is already in flight`). Fixed by changing the fixture to `'HDFC0001234'` (a realistic, pattern-valid IFSC) — test-data-only change, no assertions altered. The PAN fixture (`'ABCDE1234F'`) and email fixture (`'finance@acme.test'`) already satisfied the new patterns and needed no change.

### Follow-up — same fix extended to Month 1 (`ocr-claim-form`), 2026-09-22
Re-requested to cover the ticket's own scope note that this is a Month-2+-only fix — Month 1's `ocr-claim-form` component has the exact same three fields with the same `Validators.required`-only gap (it's the form `ocr-verify-submit-form` explicitly mirrors). Applied the identical change:
- `ocr-claim-form.component.ts` — same `PAN_NUMBER_PATTERN`/`IFSC_CODE_PATTERN`/`EMAIL_PATTERN` imports and validators added to `panNumber`/`bankIfscCode`/`beneficiaryEmail` in `ngOnInit()`'s `fb.group({...})`. No change to `onSubmit()`'s `form.invalid` gate, `validateDocuments()`, or the dispatched payload.
- `ocr-claim-form.component.html` — same `is-invalid`/`is-valid` + `invalid-feedback` convention added to the three fields.
- `ocr-claim-form.component.spec.ts` — same fixture bug found and fixed: `fullFormValue()`'s `bankIfscCode: 'HDFC0001'` (8 chars) would have broken 3 already-passing tests (`allows submission without a disability certificate`, `dispatches the full Beneficiary Details field set`, `does not resubmit while a submission is already in flight`); changed to `'HDFC0001234'`.

### Follow-up — inline required-field errors for every field, both forms, 2026-09-22
Re-requested: clicking Submit with any field blank should visibly show an error for that field, not just the 3 pattern-validated ones. `onSubmit()` in both components already called `form.markAllAsTouched()` when invalid (unchanged, pre-existing), but only `panNumber`/`bankIfscCode`/`beneficiaryEmail` had any `is-invalid`/error-message UI — the other 8 required fields (`companyName`, `companyAddress`, `bankName`, `bankBranchName`, `bankAccountType`, `micrCode`, `bankAccountNumber`, `beneficiaryMobileNumber`) went touched-but-invisible on submit.

Extended the same `is-invalid`/`is-valid` + `invalid-feedback` convention to all 11 Beneficiary Details fields in **both** `ocr-verify-submit-form.component.html` and `ocr-claim-form.component.html` (identical treatment, same field set in both forms):
- Each field's input/textarea/select gets the same `[ngClass]` valid/invalid binding keyed off `.valid` + `.touched`/`.dirty`.
- Each gets a `hasError('required')` message ("X is required"). The 3 pattern-validated fields additionally keep their existing `hasError('pattern')` message (pattern and required are mutually exclusive in practice — Angular's built-in `Validators.pattern` returns no error on an empty value, so an empty pattern-validated field shows only the required message).
- No change to `onSubmit()`, `form.invalid` gating, or `markAllAsTouched()` in either component — this is template-only, surfacing validity state that already existed.

### Follow-up — inline required error for the Self-Declaration upload (Month 1 only), 2026-09-22
`selfDeclaration`/`bankChequeOrPassbook` are plain component properties backing native `<input type="file">`s, not reactive-forms controls — they had no `touched`/`dirty` state to gate an inline message the way the other fields' `markAllAsTouched()` does, and their only existing feedback was a toast from `validateDocuments()` inside `onSubmit()`. Added a `submitAttempted` boolean (`ocr-claim-form.component.ts`), set `true` on every Submit click, gating a `border border-danger` on the upload button plus an `invalid-feedback` span under it in `ocr-claim-form.component.html` — reusing the exact `[ngClass]` + boolean-flag convention this app already uses elsewhere for non-form-control required fields (`growth-matrics-share-modal.component.html:44`, `dynamic-forms/event-forms/form-field.component.html:783`), not a new one-off pattern.

Also restructured `onSubmit()` so `validateDocuments()` runs unconditionally (previously it returned immediately on `form.invalid`, before ever checking the documents) — so on the very first Submit click, a blank form now surfaces both the field-level `markAllAsTouched()` errors AND the self-declaration/cheque-passbook errors together, instead of only showing the document error after every text field was already fixed. The existing toast for missing documents is unchanged/kept (still fires); this only adds the inline message alongside it and makes it appear earlier. Scoped to Month 1 only — Month 2+'s `ocr-verify-submit-form` shows documents as a read-only "Uploaded" confirmation row (BRD §16.2), not an editable upload, so there's nothing to validate there.

Traced all of `ocr-claim-form.component.spec.ts`'s existing assertions by hand against the restructured `onSubmit()` (couldn't run the real suite — see the pre-existing `ng test` compile failure noted above) — every existing pass/fail expectation still holds.

### Follow-up — same for Month 2+'s Cancelled Cheque/Passbook upload, 2026-09-22
Extended to `ocr-verify-submit-form` (Month 2+). Unlike Month 1's Self-Declaration (always required), this upload was previously **entirely unvalidated in code** — `onSubmit()` just sent `bankChequeOrPassbook: this.bankChequeOrPassbook || undefined` unconditionally, regardless of whether one was already on record. Added the same `submitAttempted` flag + `validateDocuments()` (mirroring `ocr-claim-form`'s), but the requirement is **conditional**: required only when `!hasExistingBankChequeOrPassbook` (no carried-forward file already on record) — leaving it blank is legitimately valid when one already exists, per this form's own "leave blank to keep it" copy. Template: added a conditional `*` to the label (`*ngIf="!hasExistingBankChequeOrPassbook"`), the same `border border-danger` + `invalid-feedback` treatment as Month 1, and restructured `onSubmit()` the same way (document check runs even when the form itself is also invalid).

**Existing-test fixture fix required**: `ocr-verify-submit-form.component.spec.ts`'s `dispatches VerifySubmitClaim...` test called `onSubmit()` with a full valid form but no file and no `hasExistingBankChequeOrPassbook` set (defaults `false`) — this new required-check would have blocked it. Fixed by setting `component.hasExistingBankChequeOrPassbook = true` in that test, simulating the carried-forward-file case its own title already describes ("no documents" = no *new* upload needed, not no file at all). All other tests in this file either already provide a file or exit before the document check is ever reached (`submitting`-guard tests) — traced by hand, unaffected.

## Blast radius
- `shared/constants/regex.ts` is imported app-wide; the two new exports are additive only (no existing export changed), so no other consumer is affected.
- `ocr-verify-submit-form` (Month 2+) and `ocr-claim-form` (Month 1) both now carry the same three pattern validators, the same full-form inline error UI, and equivalent (conditional vs. always-required) document validation — the only two OCR form components with these fields, so no other component in this module is affected.

## Verification
- `tsc -p tsconfig.app.json --noEmit` clean after every edit.
- Manually verified both new regexes against the exact fixture values in the spec file (`node -e` regex test): `'HDFC0001'` → fails IFSC (confirms the fixture bug above), `'HDFC0001234'` → passes, `'ABCDE1234F'` → passes PAN, `'finance@acme.test'` → passes `EMAIL_PATTERN`.
- **Could not run the actual Karma/Jasmine suite** (`ng test --watch=false --browsers=ChromeHeadless`) — it fails to compile for the whole app due to several pre-existing, unrelated broken spec files (mismatched constructor args in `incomplete-step-forward.guard.spec.ts`/`check-service.pipe.spec.ts`/`imagekit-url-appender.pipe.spec.ts`/`truncate.pipe.spec.ts`, and a typo'd import name in the vendored CometChat UI kit's `cometchat-confirm-dialog.component.spec.ts`). This is a pre-existing workspace-wide issue, unrelated to this change and out of scope here — flagging it rather than silently working around it.
- No automated test coverage was added for the new pattern validators themselves (per this workspace's standing rule to propose a regression test and wait for go-ahead before writing it) — proposed: new `it()` cases in both `ocr-verify-submit-form.component.spec.ts` and `ocr-claim-form.component.spec.ts` asserting `component.form.get('bankIfscCode').hasError('pattern')` / `panNumber` / `beneficiaryEmail` for a few invalid values, plus one asserting a validly-formatted `fullFormValue()` has no `pattern` errors. Not yet written — awaiting go-ahead.
- Committed and pushed: `sc-saas-frontend@523ab4a0` (branch `ai_native_setup_vishali`), after user review.
