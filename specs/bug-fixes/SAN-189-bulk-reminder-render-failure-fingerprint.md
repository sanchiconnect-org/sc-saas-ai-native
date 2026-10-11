---
id: SAN-189
title: "PENDING_CONNECTION_REMINDER Handlebars parse error — stable fingerprint to stop Sentry issue-ID flood"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-189
sentry: [SC-SAAS-BACKEND-43, SC-SAAS-BACKEND-3V, SC-SAAS-BACKEND-3S, SC-SAAS-BACKEND-3Q, SC-SAAS-BACKEND-46, SC-SAAS-BACKEND-45, SC-SAAS-BACKEND-3Y, SC-SAAS-BACKEND-47, SC-SAAS-BACKEND-44, SC-SAAS-BACKEND-42, SC-SAAS-BACKEND-41, SC-SAAS-BACKEND-4A, SC-SAAS-BACKEND-49, SC-SAAS-BACKEND-48, SC-SAAS-BACKEND-3Z, SC-SAAS-BACKEND-3X, SC-SAAS-BACKEND-3W, SC-SAAS-BACKEND-3T, SC-SAAS-BACKEND-3R, SC-SAAS-BACKEND-4B]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-189 — bulk reminder render-failure fingerprint

## Root cause
This ticket (opened 2026-08-03) already correctly diagnosed a malformed `{{#each connections}}` Handlebars block in the `PENDING_CONNECTION_REMINDER` email template, but was never actually fixed (data problem, sat in Backlog). Separately, SAN-403 (2026-09-24) fixed this function's error *logging* (previously serialized to an uninformative `{}`). That fix worked exactly as intended and made the real parse error visible — but as a side effect, revealed a new, unrelated observability gap: because this is a message-type Sentry event (not an exception with a stack trace), Sentry's default fingerprint hashes the raw message text. The exact error text Handlebars reports varies slightly per occurrence (line 23 vs 24, different truncation points), so every single occurrence was creating a brand new Sentry issue ID — 20 distinct issue IDs within about 5 hours on 2026-09-28.

## Fix
Added `fingerprintBulkReminderRenderFailure()` to `sc-saas-backend/src/instrument.ts`'s `beforeSend` chain — any message-type event containing `sendBulkPendingConnectionReminderEmail() - failed to render for recipient` gets a fixed, stable fingerprint (`['bulk-pending-connection-reminder-render-failure']`) regardless of the exact trailing error text. All future occurrences of this message class now group into one issue.

## Blast radius
`sc-saas-backend`, `instrument.ts` only. No application behavior change — purely a Sentry-side grouping change.

## Verification
`tsc --noEmit` clean.

## Rollout
Marked all 20 fragmented Sentry issues (SC-SAAS-BACKEND-43/3V/3S/3Q/46/45/3Y/47/44/42/41/4A/49/48/3Z/3X/3W/3T/3R/4B) resolved, since none of those specific IDs will recur under the new stable fingerprint. **Does not fix the underlying broken template** — that's a data-content problem in `sc-saas-admin`'s email template management (PENDING_CONNECTION_REMINDER, malformed block helper around line 23-24), left open on this ticket for whoever has that access.

## Open questions
Someone with `sc-saas-admin` email-template access needs to open PENDING_CONNECTION_REMINDER (Developer → Email Management) and fix the malformed `{{#each connections}}` block.
