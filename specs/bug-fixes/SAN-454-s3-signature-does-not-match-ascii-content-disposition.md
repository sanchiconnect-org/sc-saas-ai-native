# SAN-454 — S3 upload `SignatureDoesNotMatch`; keep the signed ContentDisposition header pure ASCII

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-454 (Sentry SC-SAAS-BACKEND-9)
- **Repo:** sc-saas-backend · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (speculative), root cause INFERRED

## Evidence
SC-SAAS-BACKEND-9 S3 `SignatureDoesNotMatch` on uploads. Earlier analysis (SAN-406) attributed it to S3 endpoint / region / credentials configuration, not code.
`attachmentDisposition(fileName)` in `src/core/upload-module/amazon-s3.service.ts` interpolated the raw filename into the `ContentDisposition` header, which is covered by the SigV4 signature.

## Root cause (inferred, not proven)
aws-sdk v2 signs the raw header string while the HTTP transport may encode non-ASCII or control characters differently, so a filename with accented or Indic characters could produce a signature mismatch.
No failing event was confirmed to carry a non-ASCII filename, so this is a plausible contributing cause, not a demonstrated one.

## Fix
`attachmentDisposition()` keeps the header pure ASCII. ASCII-only names return exactly `attachment; filename="<name>"` as before (byte-identical). Non-ASCII names return an ASCII fallback (`filename="..."` with non-ASCII characters replaced by `_`)
plus an RFC 5987 `filename*=UTF-8''<percent-encoded name>`, so browsers still see the real name. Double quotes were already stripped; backslashes are replaced in the fallback.

## Not fixed
- If the real cause is endpoint / region / credentials config (the SAN-406 conclusion), nothing in this change addresses it and the error will recur.

## Contract impact
None. No controller or DTO change; only the S3 object's response-header metadata for non-ASCII filenames. Module spec updated: `sc-saas-backend/src/core/upload-module/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.json`: exit 0.
- No automated test added (guardian skill blocked). Not run against S3, so the signature behaviour was not exercised.

## Commit
sc-saas-backend `6b3f8945` on `ai_native_setup_aman`, pushed. NOT deployed.

## Sentry
SC-SAAS-BACKEND-9 resolved 2026-10-07 under the "fix in code => resolve" policy. Reopen on recurrence, then check the S3 endpoint, region and credentials configuration (the SAN-406 diagnosis) before touching code again.
