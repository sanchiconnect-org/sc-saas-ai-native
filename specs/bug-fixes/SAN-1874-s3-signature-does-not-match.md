---
id: SAN-1874
title: "S3 SignatureDoesNotMatch still firing after SAN-454 (SC-SAAS-BACKEND-9)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1874
sentry: [SC-SAAS-BACKEND-9]
repos: [backend]
commit: sc-saas-backend@1ad29b33 (branch ai_native_setup_vishali, pushed)
created: 2026-10-12
updated: 2026-10-12
---

# SAN-1874: S3 SignatureDoesNotMatch

**Classification:** ENV_ERROR (credentials, region or endpoint on some deployment or client).

## Evidence
* 157 events since 2026-07-29, about 1–2 a day. It is intermittent, so this is not a globally dead credential.
* The events have no first-party frames.
* SAN-454 was closed without the prod AWS check ever being done.

## Fix (diagnostic only)
`sc-saas-backend/src/instrument.ts`: new `attachAwsSignatureError()` in `beforeSend`. It tags `aws_region`, `aws_hostname`, `aws_status` and `app_domain` on `SignatureDoesNotMatch` events. Never the key, credentials or StringToSign. Grouping is unchanged.

Clock skew would surface as `RequestTimeTooSkewed`, so that cause is ruled out.

## Verification
* The touched file compiles clean. The only `tsc` error is pre-existing and unrelated (`@aws-sdk/client-sesv2` is not installed locally).
* ESLint shows no new findings.
* The real `beforeSend` was exercised in a scratch script:
  * S3 events get the tags.
  * `accessKeyId` is never attached.
  * Other AWS, axios and plain errors are untouched.
  * Nothing throws.
* The full Jest suite shows no regression against the original code.

## Still needed
After deploy, someone with prod AWS access checks the tagged `app_domain`/hostname env against the bucket's credentials and region.
