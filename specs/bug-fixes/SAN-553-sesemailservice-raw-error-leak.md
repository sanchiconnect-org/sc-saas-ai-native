---
id: SAN-553
title: "SESEmailService.sendEmail leaks raw upstream error body via InternalServerErrorException"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-553
sentry:
  - SC-SAAS-BACKEND-2G
  - SC-SAAS-BACKEND-2B
  - SC-SAAS-BACKEND-11
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-553 — SESEmailService raw error leak

## Root cause

`ses-email.service.ts`'s `sendEmail()` catch block threw `InternalServerErrorException(error.response?.data)`
verbatim — same anti-pattern as SAN-549. SC-SAAS-BACKEND-2B's literal `<html>` message body is direct
proof: the email gateway's raw HTML error page was forwarded straight to the API caller.
SC-SAAS-BACKEND-11 ("No recipients defined") was the same bug reached via a different caller
(`sendAdminAccountCreatedEmail`) and was seen firing in production with the pre-fix code, confirming
the fix hadn't deployed yet at the time.

## Fix

Sanitizes into `Failed to send email (HTTP <status>): <message>` before throwing, matching the
SAN-549 pattern.

## Blast radius

None — only the error message shape changes.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
