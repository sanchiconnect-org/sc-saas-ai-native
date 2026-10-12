# SAN-1864: hardcoded fixed-OTP bypass replaced with an env-gated QA allowlist

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1864
- **Repo:** sc-saas-backend
- **Priority:** Urgent (security)
- **Assignee:** Ritu Raj
- **Classification:** CODE_ERROR
- **Related:** SAN-1581 and SAN-1575 (the QA tenant and the `sc-saas-e2e` suite need a fixed OTP for seeded accounts)

## Problem
`VerificationsService.sendOTP()` always issued the OTP `1234` for 5 hardcoded addresses (`PenetrationTestingEmails`: startup@, investor@, corporate@, mentor@ and sprovider@sanchiapp.com). Nothing restricted this to an environment, so it was live on every tenant deployment, production included. Anyone who knew one of those addresses could log in with `1234` wherever the account existed. Login goes through `sendOTP()` too, for both email and mobile logins, because a mobile login also carries the user's email.

## Evidence
- `src/modules/verifications/verifications.service.ts:63-66` (before the fix): `if (PenetrationTestingEmails.includes(sendOtpDTO.emailAddress)) generateCode = 1234;`
- `src/core/constants/enum.ts`: the hardcoded list.
- `src/modules/auth/auth.service.ts:182-193`: login builds `otpData` with `emailAddress` even for a mobile login, then calls `sendOTP`.

## Fix
- New `src/core/utils/qa-fixed-otp.ts`. `resolveQaFixedOtp(email, allowlistCsv, code)` returns the fixed code only when both env vars are set, the code matches `^[1-9]\d{3}$`, and the email is on the allowlist (case-insensitive). In every other case it returns `null`, and the service falls back to a random code.
- Two new env vars, both optional and blank-tolerant: `QA_FIXED_OTP_EMAILS` and `QA_FIXED_OTP`.
  - Read in `configuration.ts` (`qaFixedOtp`), exposed by `AppConfigService.qaFixedOtpEmails` / `qaFixedOtpCode`, and declared in `validation-schema.ts`.
  - Set **only on the QA tenant deployment**.
- `verifications.service.ts` uses the resolver for **email-type OTPs only**, so mobile and SMS never bypass.
- `PenetrationTestingEmails` is removed. Owner decision 2026-10-12: no legacy fallback; pen-testers get their addresses added via env on the deployment they test.
- `src/modules/verifications/module.spec.md` is updated.

Also changed: `sc-saas-e2e` `seed/api.ts` now sends `md5(code)` to `/otp_verifications/verify`, matching what the PWA sends; the backend compares against the stored hash. Its README documents the env vars. These changes are tracked under SAN-1581, not this issue.

## Verification
- `tsc --noEmit` passes (exit 0).
- eslint reports 0 errors on the touched files; the 5 warnings were already there.
- Prettier check passes.
- Regression test: `src/core/utils/qa-fixed-otp.spec.ts`, 14 tests passing. Related suites: 3 were already failing before this change (programs.repository, application-programs.repository, global-onboarding-design); partner-domain-access has a timing-flaky token-expiry test, unrelated.
- **Deploy note:** after this ships, the 5 `@sanchiapp.com` addresses get a random OTP like everyone else on every tenant.

## Commit
sc-saas-backend `4ee0b81c` (ai_native_setup); sc-saas-e2e seed fix committed separately.
