---
id: SAN-849
title: "Duplicated \"from\" + literal <b> tag in 1:1 meeting \"Scheduled - To Sender\" email"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-849
repos: [backend]
commit: sc-saas-backend@1bf8db8a (branch ai_native_setup_vishali, pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-849 — meeting-scheduled-to-sender organization_name template fix

## Problem
The "[Meeting] Scheduled Meeting - To Sender" email (sent to whoever scheduled a 1:1 meeting) renders broken text whenever the other party has an organization name set:

> You have scheduled a meeting with **Ritu Raj** from   from &lt;b&gt;phone fix&lt;/b&gt;,

Evidence: screenshot of a real email via a temp-mail inbox, subject "Meeting Scheduled", Sep 18th 2026, meeting with Ritu Raj, org "phone fix".

## Root cause
CODE_ERROR — a template/data-contract mismatch between two places:
- `sc-saas-backend/src/modules/meetings/meetings.service.ts` (`sendMeetingScheduledToSenderEmail` call, ~line 430-438) builds `organization_name: orgName ? \` from <b>${orgName}</b>\` : ''` — a self-contained HTML fragment that already starts with " from " and wraps the name in `<b>`.
- The `meeting-scheduled-to-sender` template body in `sc-saas-backend/src/modules/global/admin/spa_email_templates.repository.ts` (~line 385) independently hardcoded `<strong> </strong>from &nbsp;<strong>{{ organization_name }}</strong>` — its own literal "from" plus a double-mustache (`{{ }}`) placeholder.

Two bugs stacked: the literal "from" in the template plus the "from" already in the value duplicates the word, and double-mustache Handlebars HTML-escapes the value's `<b>...</b>`, so the tag shows as visible text instead of rendering bold.

Sibling templates fed by the same `meetings.service.ts` value-construction pattern (`meeting-requested`, `meeting-request-rejected`) also use double-mustache for `organization_name` and could show the same literal-tag symptom, but don't duplicate "from" in their wording — out of scope here since not evidenced; noted as a known-similar-risk, not fixed preemptively.

## Fix
In the template body, replaced:
```
<span data-offset-key="839d8-0-2"><span data-text="true"><strong> </strong>from &nbsp;<strong>{{ organization_name }}</strong></span></span>
```
with:
```
<span data-offset-key="839d8-0-2"><span data-text="true">{{{ organization_name }}}</span></span>
```
Removes the redundant hardcoded "from" and wrapping `<strong>` (the value's own `<b>` already bolds it), and switches to triple-mustache so the HTML renders instead of being escaped. When `organization_name` is empty, output is now clean (no dangling "from ,").

One-line diff, no other template content touched.

## Important caveat — does not fix already-live tenant data
`installDefaultEmailTemplates()` only inserts templates missing from a tenant's `spa_email_templates` table, or backfills `defaultTemplateContent` when it's `null` — it never overwrites an existing row's live `templateContent`. This fix only changes what **new** tenants get seeded with going forward. The tenant that produced the reported screenshot already has the buggy `templateContent` persisted and will keep sending the broken email until someone manually edits it via the sc-saas-admin Email Templates management UI (find "[Meeting] Scheduled Meeting - To Sender", fix the "You have scheduled a meeting..." paragraph the same way).

Companion fix in `sc-saas-admin`'s mirrored seed copy: [[SAN-850]].

## Blast radius
`sc-saas-backend` seed data only — affects future tenant provisioning. No API/DTO/flag/tenant-scoping impact.

## Verification
`npx tsc --noEmit` — no errors reported for this file. No test framework covers email template content (string literal, not logic) — manual verification is rendering the compiled Handlebars template with a sample `organization_name` value and confirming a single, bold "from ORG" with no visible tags. Not yet done by hand.

Vishali independently confirmed the same duplicate-"from"/literal-`<b>` pattern in the live tenant's Email Templates editor and a real sent email, matching this fix exactly. That live row still needs a manual admin-panel edit — this code change only fixes future/re-seeded tenants (see caveat above).

Committed and pushed as `sc-saas-backend@1bf8db8a` on `ai_native_setup_vishali`. Linear moved to Done.

## Related
[[SAN-850]] — identical fix in sc-saas-admin's mirrored seed data.
