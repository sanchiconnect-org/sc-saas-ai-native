---
id: SAN-609
title: "sendOTPFault(emailAddress must be an email) — program-apply modals let TLD-less emails reach send-OTP"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-609
sentry: [SC-SAAS-FRONTEND-CJ]
related: [SAN-624, SAN-707]
repos: [frontend]
commit: sc-saas-frontend@2a81647f (branch ai_native_setup_vishali)
created: 2026-09-28
updated: 2026-09-28
---

# SAN-609 — program-apply email validation matches backend @IsEmail()

## Root cause
Sentry CJ (production, 5 events / 4 users, last seen 2026-09-15) fires on `/programs/apply/:code/:slug`, not on the login/auth path the ticket originally assumed. That page's `ProgramPublicApplyModalComponent` (and its sibling `ProgramCheckStatusModalComponent`) validates the email with Angular's built-in `Validators.email` only. Angular's validator accepts addresses with no dotted domain (`john@gmail`, `name@localhost`); the backend's `SendOtpDTO.emailAddress` uses class-validator `@IsEmail()`, which requires a TLD. The Apply/Send-OTP button *is* gated on `dynamicFormGroup.valid`, so the only way a malformed address reaches `POST otp_verifications/send` is this validator mismatch. Result: the user gets a raw "emailAddress must be an email" toast after clicking Apply.

The earlier SAN-707 fix (claim-listing modal, same Sentry group in its commit message) covered a different entry point and does not touch this page.

## Fix
- `program-public-apply-modal.component.ts`: added `Validators.pattern(EMAIL_REGEX)` (the file's existing `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` constant) to the `email` control.
- `program-check-status-modal.component.ts`: same pattern added inline.
- Both templates: "Enter a valid email" hint now also shows for the `pattern` error, so the disabled button always has a visible reason.

The shared `EMAIL_PATTERN` in `shared/constants/regex.ts` was deliberately **not** reused — it is lowercase-only and would start rejecting `John.Doe@Gmail.com`, which the backend accepts.

## Blast radius
`sc-saas-frontend` only, two modals in `modules/programs/program-public-apply/`. No API/DTO/flag change. Strictly tightens client validation toward what the backend already enforces; no address the backend accepts is newly rejected. Pre-filled paths are unaffected: logged-in users bypass OTP with their already-validated profile email, and the localStorage-restored path disables the email control (disabled controls don't count toward validity).

## Verification
- `tsc -p tsconfig.app.json --noEmit` clean.
- Compared old vs new client check against backend `class-validator.isEmail` on samples: `john@gmail`, `name@localhost` now blocked client-side (backend rejects both); `john@gmail.com`, `John.Doe@Gmail.COM`, `a+b@x.co.in`, `user@sub.domain.org` still accepted.
- Residual known gap: single-letter TLD (`x@y.c`) still passes the client and is rejected by the backend — rare, and the existing error toast still handles it.
- No automated test added (workspace "guardian" skill not available). Manual check to do: open a program's public Apply modal logged out, type `test@gmail` → button stays disabled with "Enter a valid email"; type `test@gmail.com` → OTP sends.

## Open questions
None.
