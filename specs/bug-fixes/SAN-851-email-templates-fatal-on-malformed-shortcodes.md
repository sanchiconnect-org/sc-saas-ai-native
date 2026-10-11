---
id: SAN-851
title: "Malformed shortcodes JSON fatals Email Templates page on PHP 8"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-851
repos: [admin]
commit: sc-saas-admin@58abaa46
created: 2026-09-18
updated: 2026-09-18
---

# SAN-851 — Email Templates listing fatals on a row with malformed shortcodes JSON

## Symptom

On the "demo2" tenant's production admin (`adm.demo2.sanchiapp.com/developer/email_management?moduletype=meetings`),
the Email Templates table renders correctly through `meeting-feedback-reminder`, then the `meeting-requested-moderation`
row shows no Preview/Action buttons and the page ends — no further rows, no modals. Confirmed via "View Page
Source": raw HTML output cuts off mid-row, immediately after `<b>Shortcodes: </b>`.

## Root cause (CODE_ERROR)

`themes/default/html/developer/email_templates.php` had a block wrapped in an **HTML comment**
(`<!-- <p> ... </p> -->`) inside the list table row — but PHP still executes `<?php ?>` tags regardless of the
surrounding HTML comment; only the browser treats it as inert:

```php
$shortCodes = @json_decode($template['shortcodes'], true);
...
echo implode(", ", $shortCodes);
```

The `meeting-requested-moderation` row's `shortcodes` column is malformed JSON (`..."brand_logo]` — missing the
closing `"`), so `json_decode` silently returns `null` (the `@` suppresses the warning). `implode(", ", null)` is
a **fatal `TypeError` on PHP 8+** (harmless on older PHP, where it degrades to a warning + empty string) — the
same class of PHP-version-sensitivity as the earlier SAN-76/77/78 incident. The fatal kills the rest of the
response mid-stream, which is exactly why the page truncates at that row and nothing renders after it.

## Fix

`themes/default/html/developer/email_templates.php`:
- Deleted the dead HTML-commented block in the list table entirely — it never rendered anything visible (comment
  wrapped), served no purpose, and was a live crash risk for any row with malformed `shortcodes`.
- Hardened the equivalent, actually-visible block in the "Edit Template" modal (used to populate the shortcode
  chip list when editing a template): `$shortCodes` is now coerced to `array()` when `json_decode` fails,
  instead of feeding `null` into `foreach`.

## Not fixed here (production data, not code)

The `meeting-requested-moderation` row's `shortcodes` value is still malformed after this fix — the code no
longer crashes on it, but the row's shortcode list is still empty/wrong until the data itself is corrected.
Corrective SQL (run by the user against the affected tenant DB(s), not run by this fix):

```sql
UPDATE spa_email_templates
SET shortcodes = '["email","brand_name","receiver_name","sender_name","organization_name","date","time","request_link","meeting_custom_title","brand_logo"]'
WHERE template_code = 'meeting-requested-moderation' AND shortcodes LIKE '%brand_logo]%';
```

## Addendum (2026-09-18, same day) — true root cause traced to sc-saas-backend

The user correctly pointed out these templates are created by the backend, not hand-typed via the admin UI.
Traced to `sc-saas-backend/src/modules/global/admin/spa_email_templates.repository.ts`'s
`installDefaultEmailTemplates()` — a hardcoded seed array with the exact same malformed `"brand_logo]` string
literal, run on every backend boot for any tenant missing that `templateCode`. Fixed in [[SAN-855]] (a second,
identical typo was also found and fixed there). This admin-side fix stays valid and necessary regardless — it's
the crash-hardening layer that stops a bad row (from any source, not just this one) from ever taking the whole
page down again.

## Separate finding (own issue, not fixed here)

[[SAN-852]] — the same page's "DB Administration" Developer-zone link renders the production Adminer URL with
the DB password in plaintext in the HTML, discovered incidentally while diagnosing this issue. Urgent, tracked
separately — a security/credential-rotation decision, not a code guess to make silently under this bug fix.

## Verification

`php -l themes/default/html/developer/email_templates.php` — no syntax errors. No test framework in this repo
(per `sc-saas-admin/CLAUDE.md`) — regression test skipped, gap noted. Manual QA needed: reload the affected
tenant's Email Templates → Meetings page and confirm the full row list (through `reject-meeting`) now renders
with Preview/Action buttons even before the data fix is applied.

## Rollout

Committed and pushed to `ai_native_setup`: `58abaa46`.

## Open questions

None blocking. Whether other `spa_email_templates` rows (in this or other tenants) also have malformed
`shortcodes` JSON is unknown — this fix only prevents the crash, it doesn't audit/repair all existing data.
