---
id: SAN-1033
title: "createTransaction 400 retried blindly on payment/success"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1033
sentry: [SC-SAAS-FRONTEND-F5]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1033: createTransaction 400 retried blindly on payment/success

## Classification
CODE_ERROR

## Root cause
`PaymentSuccessComponent.createTransaction()` retries every error 3 times, 2s apart, and logged `createTransaction failed (attempt n/3)... 400` on each retry, which is what Sentry recorded. Its final "Payment Already Processed" card also never called `setSessionExpiredLinks()`, so its links pointed at the default.

**The retry on 400 is intentional. Do NOT restrict it to 5xx.** The backend returns 400 for transient capture/verify races right after the gateway redirect: Razorpay `No captured payment found for this order` / `No payments found`, Easebuzz `payment not successful` while verify lags, PayU `verification failed`. The Sentry evidence (only attempts 1/3 and 2/3 logged) shows the third attempt succeeded. A first draft of this fix stopped retrying on 4xx; I reverted it during review because it would have skipped post-payment actions (membership activation / application submit) for exactly these users.

## Fix
Removed the per-attempt `console.warn` (Sentry noise), and the retries-exhausted path now calls `setSessionExpiredLinks(orderObj.moduleType)`. Retry behaviour is unchanged.

## Files changed
- `src/app/modules/payment/payment-success/payment-success.component.ts`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
Retry behaviour is unchanged: the 3 retries, including on 400, are kept on purpose (see Root cause). Only the per-attempt `console.warn` is removed, and the retries-exhausted card now gets the correct links. The settled, failed and pending branches are untouched.

## 10-step process (SanchiConnect Developer Guide)
1. **Orient:** read the Sentry issue, event details and breadcrumbs. Done.
2. **/from-linear:** the Linear issue was created from Sentry and filed in the *Production Defects* project, assigned to Mahima. Done.
3. **Spec:** narrowly scoped, single-repo fix, so the lightweight `/bug-fix` path was used (this record) instead of a feature spec. Done.
4. **Design questions:** none pending. Data/ops follow-ups (if any) are listed above and not invented here.
5. **Contract check:** frontend-only. No controller, DTO, flag or tenant-scoped query changed, so `/audit-contract`, `/trace-flag` and `/check-isolation` don't apply. Backend code was only read, never edited.
6. **Tests first:** blocked workspace-wide (no guardian skill). As a substitute, `npx tsc -p tsconfig.app.json --noEmit` is clean and the `ng build --configuration development` AOT build exited 0. No automated regression test has been added; one is proposed and waiting for Mahima's go-ahead.
7. **Branch:** the working tree is `sc-saas-frontend` on `ai_native_setup_mahima`. No new branch was created. (CLAUDE.md names `ai_native_setup`; Mahima decides.)
8. **Implement:** done, see Fix.
9. **Verify:** existing-flow check above, bug-fix record written, Linear moved to In Review with a root-cause comment.
10. **Commit/push:** **not done, on purpose.** Waiting for Mahima's manual verification. Linear moves to Done only after that.
