# SAN-1160 / SAN-1161 — SMTP password in email_data, OTPs in service_usage

**Repo:** sc-saas-backend · **Parent:** SAN-1562 (secret rotation) · **Class:** CODE_ERROR (both)

## SAN-1160 — problem and root cause
On custom-SMTP tenants, `SESEmailService.sendEmail()` set `reqBody.smtpServerSettings`, including the SMTP password, on the caller's object. Callers save that same object as `ses_email_queue.email_data` after sending. There are five save sites (~1723, 2937, 3587, 5497, 8257), not just the three named in the issue.

## SAN-1161 — problem and root cause
`sendEmail()` passed the raw `reqBody.subject` to `auditServiceUsage()`, so the default OTP subject ("... OTP: {{ otp }}") stored every OTP next to its recipient in `service_usage`. The FA-009 masking only covered the `ses_email_queue` row.

## Fix (`src/core/services/ses-email.service.ts`)
- The SMTP settings now go only on a shallow copy (`payload`), and that copy is what gets POSTed to the gateway. `reqBody` never carries `smtpServerSettings`, so all five save sites are covered by one change. Any stale `smtpServerSettings` already on an incoming object (for example, an old queue row being re-sent) is removed, and the settings are rebuilt from the current tenant config.
- The FA-009 subject-masking loop is extracted into `redactSubject()`, which is now used for both the `ses_email_queue` row and the `service_usage` audit.

## Verification
`tsc --noEmit` clean. The 7 existing `ses-email.service*.spec.ts` suites pass (84 tests). ESLint shows 4 prettier errors that were already there and are not on lines touched here. No regression test added yet (proposed, awaiting go-ahead).

## Data cleanup (not yet run — per tenant DB)
```sql
UPDATE ses_email_queue SET email_data = JSON_REMOVE(email_data, '$.smtpServerSettings')
 WHERE JSON_CONTAINS_PATH(email_data, 'one', '$.smtpServerSettings');
```
Clean up the OTPs already stored in `service_usage` as well (the subject column holds them).

## Follow-up (not code)
Rotate the SMTP password on every custom-SMTP tenant (SAN-1562).

**Commit:** sc-saas-backend@f173ecb7 (ai_native_setup)
