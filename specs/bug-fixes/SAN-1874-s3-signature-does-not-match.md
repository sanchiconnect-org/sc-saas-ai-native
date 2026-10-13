---
id: SAN-1874
title: "S3 SignatureDoesNotMatch still firing after SAN-454 (SC-SAAS-BACKEND-9)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1874
sentry: [SC-SAAS-BACKEND-9]
repos: [backend]
commit: sc-saas-backend@1ad29b33 (diagnostic, branch ai_native_setup_vishali, pushed). The root-cause fix is sc-saas-backend@6b3f8945 (SAN-454, in main since 2026-10-07)
created: 2026-10-12
updated: 2026-10-13
---

> **Update 2026-10-13: deploy lag, not an open defect.** Re-triage found the
> root cause was already fixed by `6b3f8945`. Every event since that fix came
> from a process started before it. See "Re-triage 2026-10-13" at the end.

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

## Re-triage 2026-10-13
* **The events are not random infra noise.** They arrive in bursts on one host, 3 to 12 events within minutes (for example, 12 on 09-27 between 13:39 and 14:14). That is one user retrying an upload that fails every time, so the failure is deterministic per input. Rotated keys or clock skew would not produce this pattern.
* **Mechanism:** multer decodes `file.originalname` as latin1, so UTF-8 filenames (accented, Indic, curly quotes) contain characters outside ASCII. `ContentDisposition: attachment; filename="<name>"` is a signed header. Node writes those characters as latin1 bytes while SigV4 signs their UTF-8 encoding, so S3 rejects the upload with SignatureDoesNotMatch. S3 keys are `md5(...)`, so they are always ASCII. The only filename-derived header is `ContentDisposition`, set in `uploadFile` and `uploadInvoiceFile`.
* **Already fixed:** `6b3f8945` (Aman, SAN-454) routes both sites through `attachmentDisposition()`, which returns a pure-ASCII header and carries the real name in RFC 5987 `filename*`. It merged to main in PR #2010 at 2026-10-07 06:18 UTC. A scratch check of the helper confirmed that latin1-decoded `résumé.pdf`, an Indic name and `Founder’s plan.docx` all produce ASCII-only headers, and that ASCII names are unchanged.
* **No event on a fixed build:**
  * The 2026-10-07 17:27 event (host .136) has the same per-process trace ID (`60a049…`) as that host's 2026-10-03 events, so it came from the same pre-fix process.
  * The 2026-10-11 events (host .177) report `app_start_time` 2026-10-03.
  * This matches SAN-1875: production was still running a 10-03 build.
* **No further code change.** Close once the backend is redeployed from main and SC-SAAS-BACKEND-9 stays quiet, for example for 7 days. If it recurs on a post-10-07 build, the `1ad29b33` diagnostic tags (`app_domain`, `aws_hostname`, `aws_region`) give the env check a target. That diagnostic is only on `ai_native_setup_vishali` and needs merging to reach production.
* **Out of scope, pre-existing:** `filename*` carries the latin1-mojibake name (multer's decoding), so a non-ASCII download name can look garbled. It is cosmetic and has no effect on signing.
