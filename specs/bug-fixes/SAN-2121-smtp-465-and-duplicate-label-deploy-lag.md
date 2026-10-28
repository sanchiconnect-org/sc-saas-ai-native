---
id: SAN-2121
title: "SMTP 'Greeting never received' on the 1:1-live email, and the duplicate-label warning opening a new group in prod"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2121
sentry: [SC-SAAS-BACKEND-65, SC-SAAS-BACKEND-68]
repos: [backend]
related: [SAN-1868, SAN-1987]
commit: none from this ticket; 65 fixed by 3rdparty-webservices@0bd7a44 (Nirmal Singh)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2121: both already fixed upstream

## BACKEND-65
* The error was not transient. Port 465 is implicit TLS, and the gateway created the nodemailer transport without `secure: true`, so it waited for a plain-text greeting that never came.
* Nirmal fixed it in sc-saas-3rdparty-webservices `0bd7a44` (`src/modules/ses/ses.service.ts:51-58`, `secure: port === 465`) at 2026-10-27 02:53 UTC, after the only event (00:15 UTC). The fix is on development and stagingdemo, not main. No retry is needed.
* Seen but not changed: backend `sendEmail` has no timeout, and `sendEventOneToOneLiveEmail` returns 500 to the admin when sending fails.

## BACKEND-68
* This is deploy lag; the fingerprint itself is correct. SAN-1868 (`3473722f`) reached main via `cc8fb88d` on 10-27, and the prod container started on 10-14.
* The only emitter (`user.service.ts:1451`) produces both substrings that `fingerprintDuplicateLabelWarning()` checks (`src/instrument.ts:193-203`).

## Open (ops)
Redeploy the prod backend from main, deploy gateway `0bd7a44` to prod, then merge the per-label Sentry groups.
