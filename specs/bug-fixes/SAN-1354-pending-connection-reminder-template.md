# SAN-1354 / SAN-1355 — Pending-connection reminder template malformed

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1354 (backend) · https://linear.app/sanchiconnect/issue/SAN-1355 (admin seed)
- **Sentry:** SC-SAAS-BACKEND-3S and 15 siblings (3Q 3V 3Y 3Z 40–49 4A) · **Priority:** High · **Assignee:** Nirmal Singh · **Related:** SAN-189

## Problem
`sendBulkPendingConnectionReminderEmail() - failed to render … Parse error on line 23: {{ #each connections`.
The rich-text editor mangled the `pending-connection-reminder` loop:
- `{{ #each connections` opens the block (Handlebars doesn't allow the space, and there is no closing `}}`);
- the connection card follows;
- the stray `}}` lands after the card's `</table>`;
- there is no `{{/each}}`.

The template can't compile, so no investor received the reminder. SAN-189 only grouped the Sentry events.

## Fix
- Seeds: `{{#each connections}}` … `{{/each}}`, and the shortcodes list both tags.
  - sc-saas-backend `spa_email_templates.repository.ts` (SAN-1354)
  - sc-saas-admin `config/admin-data/email_templates.php` (SAN-1355)
- Existing tenants: `installDefaultEmailTemplates()` only inserts missing templates, so it now calls
  `repairPendingConnectionReminderTemplate()` at startup. The two exact replacements are applied to `template_content`,
  `default_template_content` and `shortcodes`, only when the broken opener occurs once, `{{/each}}` is absent and the
  stray `}}</td>` is present. It's idempotent, edited rows are left alone, and no manual SQL is needed.

## Verification
- Handlebars run: the old seed fails with "Parse error on line 23" (the Sentry error). The new seed renders one card per
  connection (2/2). A repaired broken row renders and equals the new seed (default content and shortcodes fixed too).
  A second repair run saves nothing.
- `tsc` clean; `php -l` clean. The repository file's 3 Prettier errors (lines 391/1401/4084) already exist on HEAD.

## Commit
sc-saas-backend `64a44589` + sc-saas-admin `be62c6ab` (on `ai_native_setup`)
