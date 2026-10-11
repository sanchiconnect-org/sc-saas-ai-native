---
id: SAN-885
title: "Verify & Submit shows \"Self-Declaration Uploaded\" with no prior claim ever made"
type: bug-fix
status: reverted — not currently applied to the working tree
linear: https://linear.app/sanchiconnect/issue/SAN-885
sentry: []
repos: [frontend]
commit: none — implemented and reverted twice now, never committed (branch ai_native_setup_vishali)
created: 2026-09-21
updated: 2026-09-22
---

> **⚠️ STATUS AS OF 2026-09-22: NOT APPLIED.** This fix has now been implemented, then reverted, TWICE, without ever being committed. The bug described below is still live in the actual codebase. Before assuming this is fixed (from this doc's own past tense, or from Linear's description), verify `operational-cost-reimbursement.component.ts`'s `openVerifySubmitForm()` directly — if it opens the modal unconditionally with no prior-claim check, the bug is still present.

# SAN-885 — Verify & Submit false "Uploaded" badge

## Root cause
CODE_ERROR — confirmed by reading both `sc-saas-frontend` and `sc-saas-backend`:
1. **The "Uploaded" badge is hardcoded UI, not bound to any real state.** `ocr-verify-submit-form.component.html`'s Documents step renders the confirmation row (`Self-Declaration (includes Shareholding Pattern) — ✓ Uploaded`) unconditionally — there is no underlying "has this ever actually been uploaded" check.
2. **The frontend never gated "Verify & Submit" on any prior month having been claimed.** `isMonthClaimable()` (`operational-cost-reimbursement.component.ts`) only looks at the CURRENT month's own state, so a Month 2+ card can be "claimable" and open the Verify & Submit modal even when the startup has never submitted anything before.
3. **The backend rejects the actual submission anyway, silently as far as the user can tell.** `sc-saas-backend`'s `verifySubmitClaim()` throws `BadRequestException('No prior submission found to carry forward — submit Month 1 first.')` when there's no prior claim at all — but the user never sees this until after filling in the entire Beneficiary Details form and clicking Submit.

## Design decision (confirmed with the user)
The backend's carry-forward source is "the startup's most recent prior claim, of **any** status" — not specifically Sanctioned. Decision: keep that backend rule as-is; fix the frontend only, by making the UI accurately reflect the rule instead of hardcoding "Uploaded" or letting a doomed submission reach the backend.

## Fix
`operational-cost-reimbursement.component.ts` — `openVerifySubmitForm(eligibility, monthIndex)` now checks `eligibility.months.some((month) => !!month.claim)` before opening the modal at all. If there's no prior claim anywhere, it shows an error toast (`'No prior submission found to carry forward — submit Month 1 first.'`) and returns without opening `OcrVerifySubmitFormComponent` — so the misleading "Uploaded" row is never shown for a startup with nothing to actually carry forward. A prior claim of ANY status (including Rejected) still lets the modal open, matching the backend's own rule. No change to `ocr-verify-submit-form.component.html`'s Documents row itself (per the design decision above), `isMonthClaimable()`, or Month 1's own submission flow (`ocr-claim-form.component.ts`).

### History note (updated — reverted a second time, 2026-09-22)
This fix has now gone through this cycle twice:
1. Implemented in an earlier session, then reverted per a direct request for review — but neither the fix nor the revert was ever committed, so the working tree silently carried the ORIGINAL broken behavior into the next session with no trace in git.
2. The user reproduced the exact same bug live again (screenshot, today), which is what surfaced that the fix had never actually landed the first time. Re-implemented — identical logic — and this time also fixed the pre-existing broken test file (see below) and added tests for the guard.
3. Immediately after, asked to revert again ("leave it revert code"). Reverted via `git restore` on both `operational-cost-reimbursement.component.ts` and its `.spec.ts` — nothing had been committed, so this cleanly restored the pre-fix state. **The fix described in this doc is NOT currently in the working tree.**

No reason was given for either revert request — if/when this is picked up again, confirm with the user whether there's a design concern with the fix itself (e.g. the toast-and-block UX, or the "any prior claim, any status" carry-forward rule) before re-implementing a third time, rather than assuming it's just review timing again.

### Side-defect found and fixed while implementing (pre-existing, unrelated to this bug itself)
`operational-cost-reimbursement.component.spec.ts` did not compile under `tsconfig.spec.json` (confirmed via `tsc -p tsconfig.spec.json --noEmit` before touching anything):
- The component is instantiated with 6 constructor args against the real 8-arg constructor — `route: ActivatedRoute` (added during SAN-882) and `publicApi: PublicApiService` were both missing, and every arg after `router` had silently landed one parameter position early (e.g. the `siteMetadataService` test double was actually being bound to the `route` parameter). This meant `ngOnInit()` would have thrown immediately in a real test run (`this.siteMetadataService.setTitle` resolving to a double with no such method) — this file could never have actually passed if `ng test` had been runnable. Fixed by adding `route` and `publicApi` mocks in the correct constructor positions.
- Two stale `component.openClaimForm([])` calls (`openClaimForm()` takes no arguments since the 2026-09-17 category-selection removal) — fixed to `component.openClaimForm()`.

## Blast radius
- Only `operational-cost-reimbursement.component.ts` (production) and its own `.spec.ts` were touched. `ocr-verify-submit-form.component.ts/.html` (the modal itself), `isMonthClaimable()`, and `ocr-claim-form.component.ts` (Month 1) are untouched.
- The guard only affects Month 2+'s Verify & Submit entry point; Month 1's `openClaimForm()` has no such carry-forward requirement (it doesn't need a prior claim to exist) and is unaffected.

## Verification
- `tsc -p tsconfig.app.json --noEmit` and `tsc -p tsconfig.spec.json --noEmit` both clean for every file touched here (confirmed the spec file's pre-existing arity/stale-call errors are gone, and introduced no new ones).
- Updated 3 existing `openVerifySubmitForm()` tests (modalRef wiring, beneficiaryDetails passthrough, hasBankChequeOrPassbookOnFile passthrough) to include a prior claim in their fixtures, since the new guard would otherwise block them — they test other behavior, not the guard itself.
- Added 2 new tests for the guard itself: blocks opening + shows the toast when there's no prior claim at all; still opens for a prior claim of ANY status (e.g. Rejected), matching the backend's own carry-forward rule.
- **Could not run the actual Karma/Jasmine suite** (`ng test`) — it fails to compile app-wide due to several pre-existing, unrelated broken spec files across the repo (dashboard/investors/jobs/startups components missing named exports, a directive/pipe constructor-arg mismatch, the vendored CometChat kit's typo'd import) — confirmed once again today, unrelated to this change, out of scope here.
- Reverted, not committed — see history note above. The bug is currently still live.
