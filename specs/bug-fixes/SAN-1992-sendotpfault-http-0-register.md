---
id: SAN-1992
title: "sendOTPFault( HTTP 0 ) on thub auth/register (SC-SAAS-FRONTEND-HP) — handled network drop"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1992
sentry: [SC-SAAS-FRONTEND-HP]
repos: [frontend]
related: [SAN-470, SAN-624, SAN-690, SAN-1930]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1992: sendOTPFault( HTTP 0 )

## Investigation
* **The event:** one event, one user, `thub.sanchidev.in/auth/register` (dev server, environment tag `local`), release `b82c99a52` (2026-10-19, on `ai_native_setup_vishali`). So it is current code.
* **Where it comes from:** `SignUpService.sendOTP()` (`core/service/sign-up.service.ts:36`) warns `sendOTPFault( HTTP 0 )`. The SAN-470 `httpFaultMessage` fallback adds the status when the body is empty, then the service re-throws.
* **The effect catches it:** `sign-up.effect.ts:24` dispatches `SendOtpFault(httpFaultMessage(err, 'Please try again.'))`. The effect does not die and nothing is thrown unhandled.
* **What the user sees** (`register.component.ts:543-550`):
  * toast "OTP sent fail Please try again.";
  * `otpSentFlag = false`, `disableContinueButton = false`, `stepCount = 1`.
  * They can retry right away. No stuck spinner.
* This is a status-0 network drop (connection reset, offline, CORS-level failure) on a dev server, already handled in the UI.

## Fix
None.

## [DESIGN DECISION PENDING]
* **The question:** should network-level `( HTTP 0 )` / `( … 0 Unknown Error )` console.warn echoes be dropped in `src/main.ts` `beforeSend`?
* This is the filter SAN-1930 recommended, under "Recommended Sentry filter", and it is still not implemented.
* It is a product/dev-lead call because it also hides real reachability signal.
* Until it is decided, this class of event will keep opening one-event issues.

## Blast radius / existing-flow impact
None (no change).

## Verification
Code read only. The event's release `b82c99a52` is on `ai_native_setup_vishali` (`git merge-base --is-ancestor b82c99a52 HEAD` → yes), so the code read is the code that ran.

## Recommended close
Close as expected-condition noise (handled in the UI). Track the filter decision under SAN-1930's recommendation.
