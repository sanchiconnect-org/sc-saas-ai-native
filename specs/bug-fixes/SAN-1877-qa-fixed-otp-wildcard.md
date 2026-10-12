# SAN-1877: QA_FIXED_OTP_EMAILS accepts a local-part wildcard

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1877
- **Repo:** sc-saas-backend (consumer: sc-saas-e2e)
- **Type:** Improvement, Medium
- **Assignee:** Ritu Raj
- **Related:** SAN-1864 (env-gated fixed OTP), SAN-1576 journey 2

## Why
The e2e register journey must sign up a new email every run. The SAN-1864 allowlist only matched exact addresses, so a fresh address got a random OTP the test couldn't know.

## Change
In `src/core/utils/qa-fixed-otp.ts`, an entry may use `*` in the local part, e.g. `sc_reg_*@yopmail.com`. `*` matches `[a-z0-9._%+-]*`.

The following entries are ignored, because they would open a whole domain:
- `*` in the domain
- a local part made only of `*`

Exact entries are unchanged. Unset or blank still means no bypass anywhere.

## Verification
- 14 new Jest tests, 28 in total, all passing. They cover lookalike domains (`…@yopmail.com.evil.io`) and regex metacharacters in entries.
- eslint and tsc pass.
- e2e dry run against dev, with the backend change not yet deployed: the register wizard reached the OTP step and the OTP was rejected. That's the expected behaviour until the change is deployed and `sc_reg_*@yopmail.com` is added to the dev backend's `QA_FIXED_OTP_EMAILS`.

## Commit
- sc-saas-backend `a1b17093` (ai_native_setup)
- sc-saas-e2e `4cafc67` (main)
