---
id: SAN-1899
title: "program-public-apply status-0 warnings + applicant email leaked into Sentry"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1899
sentry: [SC-SAAS-FRONTEND-EX]
repos: [frontend]
commit: sc-saas-frontend@ebde31ce4 (branch ai_native_setup_vishali, pushed)
created: 2026-10-14
updated: 2026-10-14
---

## Root cause
`applicationProgramManagementApplicationDetails()` warned on every non-404 failure with `error.message`, which `captureConsoleIntegration` forwards to Sentry.
1. Status 0 (client network drop) is not actionable. This is the same class SAN-567/569/615 stopped reporting.
2. `HttpErrorResponse.message` contains the request URL `…/check_application_status/<email>/details`. Sentry scrubbed the title, but the raw email was stored in `extra.arguments`.

## Fix
Skip the warn for `status === 0` too. For the remaining warnings, log `status` + `error.error?.message || statusText` instead of `error.message`, so no URL and no email.

## Blast radius
Logging only, in `program-public-apply.component.ts`. Control flow is unchanged: the method still returns early on any failure.

## Verification
`tsc` + eslint clean. No automated test added. Not checked in a browser.
