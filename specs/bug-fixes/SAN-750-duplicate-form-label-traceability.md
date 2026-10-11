---
id: SAN-750
title: "Duplicate form-label conflict warnings enriched with formId/submissionId/email for traceability"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-750/sentry-duplicate-form-label-conflicts-with-genuinely-different-values
sentry: [SC-SAAS-BACKEND-2F, SC-SAAS-BACKEND-2J, SC-SAAS-BACKEND-2K, SC-SAAS-BACKEND-2M, SC-SAAS-BACKEND-2N, SC-SAAS-BACKEND-2P, SC-SAAS-BACKEND-2Q, SC-SAAS-BACKEND-34]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-750 / SAN-899 — duplicate form-label conflict traceability

## Root cause
Not a code defect — a real tenant form has a duplicated field block (most likely a copy-pasted "Applicant" + "Nominee/Co-founder/Reference" section never relabeled), so two fields legitimately share one label but hold different values. `user.service.ts`'s `getProfileDataByEmailOfGuestUser` (SAN-402/453 fix) already handles this correctly — keeps the first non-empty value and warns rather than silently overwriting. The warning itself, however, logged only the label text, with no way to trace which tenant/form/submission triggered it — so the ticket had been sitting as "no DB/admin access to identify the specific tenant/form" with no way forward.

## Fix
Enriched the warn log in `getProfileDataByEmailOfGuestUser` (`src/modules/user/user.service.ts`, ~line 1361) to include `formId` (`submission.formId`), `submissionId` (`submission.id`), `email` (`submission.email`), and the conflicting field's `key`, alongside the existing label. The next time this fires in Sentry, whoever has `sc-saas-admin` access can go straight to that `formId` in Form Management and rename the duplicated field — no reverse-engineering required.

## Blast radius
`sc-saas-backend` only. Log-content change only; no change to the keep-first-value behavior, return shape, or any consumer of `getProfileDataByEmailOfGuestUser`.

## Verification
`npx tsc --noEmit` clean. No test suite exists for this method; behavior unchanged, only the warn message's content.

## Rollout
Does not fix the underlying duplicated form field — that's a data-content fix in `sc-saas-admin`'s Form Management, requiring DB/admin access this agent session doesn't have. Next occurrence's Sentry event now carries enough detail (`formId`) for someone with that access to act immediately.

## Open questions
Which tenant/form is actually affected is still unknown as of this fix — will be answered by the `formId` in the next Sentry occurrence rather than requiring a fresh investigation.
