---
id: SAN-2112
title: "createMembership() for application_programs orders inserts a null profile_type (root cause behind SAN-2026)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2112
sentry: [SC-SAAS-BACKEND-66]
repos: [backend]
related: [SAN-2026, SAN-1561, SAN-1021, SAN-1152]
commit: backend@e46b7042 (branch ai_native_setup_vishali, pushed)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2112: call-for-applications memberships have no profile type

## Root cause
* 66: `createMembership() failed … moduleType: application_programs … Column 'profile_type' cannot be null` (order 186, dev).
* `prepareOrderForCaller → bindMembershipData` (`payment.repository.ts` ~:548, SAN-1561 `21435b70`) handles call-for-applications (CFA) orders with `profileId = submissionId` and `profileType = sent.profile_type ?? null`. The profile type comes from the client.
* The PWA sends `profile_type: this.passData.activeUser.accountType ?? null` (`sc-saas-frontend/.../checkout/checkout.component.ts:501`). For CFA, `activeUser` comes from localStorage `application-<uuid>` (`modal-handler.service.ts:72`). That key only holds `{countryCode,email,name,mobileNumber,code,companyName}` (`application-program-management-dynamic-form.component.ts:505`) and has **no accountType**.
* So every CFA membership order carries `profile_type: null`, and the insert into NOT NULL `memberships.profile_type` (`memberships.entity.ts:31`) always failed. SAN-2026 only made the failure get logged.

## Fix
In `createMembership` (`payment.repository.ts:1907-1922`), when `profile_type` is missing the method warns `createMembership() skipped: order has no profile_type to grant the membership to` (orderId, moduleType, profileId) and returns, instead of raising a raw DB error.

**Not done, on purpose:** filling in a value. The only candidate, `membership_types.profile_type`, is nullable. A CFA row is also keyed on the submission id, not a profile id, and `memberships/last|history/:profileType/:profileUUID` look up by `(profileType, profileId)`. Writing `'startup'` would attach the membership to whichever startup has `id == submissionId`.

## Blast radius / existing-flow impact
Backend only. The outcome is unchanged, since no row was ever created for these orders. Regular membership and programs orders always get `profile_type = session.accountType`, so they are unaffected. No API or DTO change.

## Verification
* `npx tsc --noEmit` → 0
* `npx jest src/modules/payment-management src/modules/cron` → 16 suites passed, 193 tests passed (SAN-2026 and SAN-1561 specs included)
* `npm run gates`: every gate except lint → 0. Lint fails only locally, because this machine's `core.autocrlf=true` checkout is CRLF.

## Decision pending
**Product / dev lead:** what should a CFA-purchased membership belong to?
1. The applicant's real profile (needs a submission → profile link).
2. A dedicated application profile type.
3. No membership row at all (the CFA gate already reads the paid order).
