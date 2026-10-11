---
id: SAN-989
title: "sendEventSpeakerRegistrationEmail crashes uncaught on malformed template"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-989
sentry: [SC-SAAS-BACKEND-3H]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-989 — unguarded template render in sendEventSpeakerRegistrationEmail

## Root cause
`ses-email.service.ts`'s `sendEventSpeakerRegistrationEmail()` had no try/catch around its Handlebars compile/render, unlike its sibling `sendBulkPendingConnectionReminderEmail()` (already fixed for this exact class of bug). `handlebars.compile()` is lazy — it doesn't parse the template until the returned function is first invoked with data — so a malformed saved template throws at the render call (`template(attributesToMap)`), not at `compile()`. The actual template (`EVENT_SPEAKER_REGISTRATION`) has an unclosed block helper around line 72 (`Expecting 'OPEN_INVERSE_CHAIN', 'INVERSE', 'OPEN_ENDBLOCK', got 'EOF'`). Called from `AdminActionsController.sendEventSpeakerRegistrationEmail`, so this surfaced as a raw 500 with an internal Handlebars parser stack trace on an admin action button click.

## Fix
Wrapped the compile+render in try/catch. On failure: logs the real error message server-side, throws `InternalServerErrorException('Event speaker registration email template has a syntax error - contact support')` instead of letting the raw parser error propagate.

## Blast radius
Single function. No behavior change for a valid template.

## Verification
`tsc --noEmit` clean.

## Rollout
Does not fix the underlying broken template content — that's a data problem in the `EVENT_SPEAKER_REGISTRATION` template, editable via `sc-saas-admin`'s email template management, not something this code change touches. The endpoint will still fail until that template is corrected, just with a clear message instead of a crash. Sentry issue left open/unresolved for that reason.

## Open questions
Whoever manages email templates needs to open `EVENT_SPEAKER_REGISTRATION` in `sc-saas-admin` and fix the unclosed block helper.
