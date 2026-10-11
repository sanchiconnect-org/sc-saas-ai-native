---
id: SAN-975
title: OCR admin Claim Details — "Previous Submission" should be the same month's rejected claim
type: improvement
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-975
repos: [backend]
assignee: Mahima Sharma
created: 2026-09-24
updated: 2026-09-24
---

# SAN-975 — compare a re-application against that same month's rejected claim

## Request

Admin panel `/operation_cost/claims` → View Details. When a startup re-applies for a month after that month's claim was rejected, the admin should see that same month's rejected claim alongside the new data.

## Classification

Requirement change, not a code defect. SAN-903 deliberately picked the most recent rejected claim of **any** month. The user has now asked for the same month only.

## Fix (sc-saas-backend)

`operational-cost-reimbursement.service.ts` `getClaimDetails()`: the `previousRejectedClaim` filter adds `priorClaim.monthIndex === claim.monthIndex`. The response shape is unchanged, so sc-saas-admin needs no changes. Its "Previous Submission (Last Rejected)" tab and diff card (SAN-903/SAN-961) already render only when `previousRejectedClaim` is non-null.

## Open point

The reported dev claim (Vami Dummy, Month 9, TR26-ELMA2-000015) showed **no** Previous Submission tab even under the old any-month logic. It also showed no Beneficiary Details and no documents, which looks like a claim created via Migrate Offline Claim. So for that startup, the backend found no lower-id rejected claim at all. That needs a DB check of that startup's claims (id, month_index, claim_status, is_migrated) and couldn't be done here: no mysql client locally, and tenant DB config comes from the tenants API.

## Verification

- `tsc --noEmit` clean; eslint 0 errors (3 old warnings); OCR module jest 100/100 passing (existing tests; no new regression test yet).

## Commit

Pending (not committed).
