---
id: SAN-904
title: "Snapshot Beneficiary Details per OCR claim (enables admin diff view)"
type: feature
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-904
sentry: []
repos: [backend]
commit: sc-saas-backend@2a7bc62e (branch ai_native_setup_vishali)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-904 — Snapshot Beneficiary Details per claim

## Why
Companion to [SAN-903](https://linear.app/sanchiconnect/issue/SAN-903) (`sc-saas-admin` diff view). `operational_cost_bank_details` is one row per startup (`startup_id unique: true`), upserted in place on every submission. Once a startup resubmits after a rejection, the rejected claim's original Beneficiary Details are already overwritten — there is nothing left in the DB to diff against, for any existing rejected claim. Design decision confirmed with the user: extend `operational_cost_claims` directly with the 11 Beneficiary Details fields, same convention already used there for `amount`/`category` — not a new snapshot table.

## Fix
1. **`operational-cost-claims.entity.ts`** — added the 11 fields (`companyName`, `companyAddress`, `panNumber`, `bankName`, `bankBranchName`, `bankAccountType`, `micrCode`, `accountNumber`, `ifscCode`, `beneficiaryEmail`, `beneficiaryMobileNumber`), all `nullable: true` (existing rows predate this, `synchronize: true` can't backfill a NOT NULL default against a non-empty table — same rationale already documented on `OperationalCostBankDetailsEntity`'s own additive fields). No migration file needed — this repo uses `synchronize: true` (confirmed via the claims entity's own doc-comment).
2. **Repository** (`operational-cost-reimbursement.repository.ts`):
   - `applyBeneficiaryDetails()`'s target type widened from `OperationalCostBankDetailsEntity` to a new `IBeneficiaryDetailsSnapshotTarget` interface — both the bank-details entity and the claim entity now structurally satisfy it (same field names), so one mapping function serves both without duplicating the DTO-field-name → entity-column-name mapping.
   - `submitClaimTransactionally()` now also calls `applyBeneficiaryDetails(claim, params.beneficiaryDetails)` before saving the claim — `params.beneficiaryDetails` was already always present, so no service-layer change was needed for Month 1.
   - `verifySubmitClaimTransactionally()` gained a new **always-present** `beneficiaryDetailsSnapshot: IBeneficiaryDetailsFields` param (distinct from the existing, conditionally-null `bankUpdate`) — the claim's own snapshot must reflect what was actually submitted this time regardless of whether it happens to equal the live `bank_details` row, so it can't reuse `bankUpdate`'s "only when changed" logic.
3. **`operational-cost-reimbursement.service.ts`**:
   - `verifySubmitClaim()` now builds the full 11-field `submittedBeneficiaryDetails` object once and reuses it for both `beneficiaryDetailsSnapshot` (always) and `bankUpdate` (conditionally, when `bankChanged`) — removes what would otherwise have been duplicated field-mapping.
   - `getClaimDetails()` now also looks up `priorClaims` (via the existing `getClaimsByStartupId()`, same ordering `verifySubmitClaim()`'s own carry-forward logic already relies on), finds the immediately-preceding claim with `claimStatus === REJECTED` (if any), and returns it as `previousRejectedClaim` — including its own snapshot (`null` if it predates this change) and its own documents (fetched + signed the same way the current claim's documents already are).

## Blast radius
- `operational_cost_bank_details`'s own behavior is unchanged — still the live, current-value source used for prefill (`ocr-verify-submit-form`'s `existingBeneficiaryDetails`, etc.). This is purely additive.
- Only the OCR module's own entity/repository/service files touched. No DTO, controller route, or other module affected.

## Verification
- `tsc --noEmit -p tsconfig.json`: clean.
- Full existing suite run: `operational-cost-reimbursement.service.spec.ts` (77/77 passing) and `.controller.spec.ts` (5/5 passing) — no regressions. Traced by hand beforehand why each test would still pass (none assert on the full `verifySubmitClaimTransactionally` call-args object, only specific sub-fields like `bankUpdate`; `getClaimDetails()` tests never trigger the new `previousRejectedClaim` branch since `getClaimsByStartupId` defaults to `[]` and none override it to include a rejected claim).
- No new regression test added — **explicitly deferred by the user** (2026-09-22): "leave the regression tests for now; we can add them separately if needed." Proposed tests (for later, if picked up): (a) `submitClaimTransactionally()`/`verifySubmitClaimTransactionally()` snapshot the 11 fields onto the saved claim; (b) `getClaimDetails()` returns `previousRejectedClaim` with its own snapshot when the immediately-preceding claim was rejected, `null` when there is none, and `bankDetails: null` (not a crash) when that prior claim predates this change. This is a deliberate choice, not an oversight — don't add them unprompted in a later session.
- Committed and pushed: `sc-saas-backend@2a7bc62e` (branch `ai_native_setup_vishali`), after user review. Not yet live anywhere `sc-saas-admin` can reach it — `api_url` for the local tenant is DB-configured per-tenant and needs to point at a locally-run instance of this repo (or the deployed branch needs to actually get deployed) before SAN-903's diff card has real backend support.
