---
id: SAN-2019
title: "Dev gateway in GATEWAY_KEY_MODE=enforce with no GATEWAY_INTERNAL_API_KEY: every email fails on dev"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2019
sentry: [SC-SAAS-BACKEND-60, SC-SAAS-BACKEND-61, SC-SAAS-BACKEND-62, SC-SAAS-BACKEND-63, SC-SAAS-BACKEND-64, SC-SAAS-FRONTEND-HX]
repos: [3rdparty-webservices, backend]
related: [SAN-1952, SAN-1953, SAN-1954]
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2019: dev gateway is enforcing a key it doesn't have

## Investigation
* All six issues first seen 2026-10-26 04:27-04:40 UTC, `environment: local`, dev Docker host, node v16.20.2.
* BACKEND-62: `InternalServerErrorException` in `SESEmailService.sendEmail` from `VerificationsController.sendOTP` (login OTP). BACKEND-60: `sendJuryNdaNotificationEmail()` recipient failed. BACKEND-61/63/64: the jury NDA retry cron for acceptance 43 (`NDA-R447-000043`) gave up after `MAX_ATTEMPTS=3`.
* FRONTEND-HX is the `loginFault( ... )` console.warn echo of the same backend error on `thub.sanchidev.in/auth/login`. It is not a frontend bug.
* The message is thrown only at `sc-saas-3rdparty-webservices/src/core/guards/gateway-key.guard.ts:73-76`. That branch runs only when `GATEWAY_KEY_MODE` resolves to `enforce` **and** `GATEWAY_INTERNAL_API_KEY` is empty. `parseGatewayKeyMode` treats anything else as `log`, so `enforce` was set on dev on purpose.
* Where the key comes from:
  * The guard is from `a31f761` (SAN-1952).
  * The backend sends the `x-internal-api-key` header from `process.env.GATEWAY_INTERNAL_API_KEY` (`sc-saas-backend/src/core/utils/gateway-key.ts`, SAN-1953).
  * The admin sends it from `$_ENV` (SAN-1954).
  * All three are on `development` / `ai_native_setup*`, not on main.

## Root cause
Dev gateway configuration, not code.
* Failing closed in `enforce` mode is correct.
* Failing the OTP request when the email can't be sent is also correct: `verifications.service.ts:139-172` doesn't save an OTP row the user could never receive.

## Fix
None in code.

## Blast radius / existing-flow impact
None from this ticket. While the gateway is misconfigured, every call to it from dev fails: email, SMS, chat, video, short links and document conversion, from both backend and admin.

## Verification
Read-only investigation; evidence above.

## Ops follow-ups
1. Set the same `GATEWAY_INTERNAL_API_KEY` on the dev gateway, every dev backend job and dev sc-saas-admin. Restart backend and admin first, then the gateway. If only the gateway has the key, callers get 401s.
2. Immediate unblock: set `GATEWAY_KEY_MODE=log` on the dev gateway. Switch back to `enforce` once the gateway log shows no "no x-internal-api-key" lines.
3. Resend jury NDA acceptance 43 from the admin tracker.
4. Before SAN-1952 reaches staging or prod, set the key on those environments first.
5. Optional hardening (dev lead): make the key Joi-`required()` when the mode is `enforce`, so a missing key fails at boot instead of at login.
