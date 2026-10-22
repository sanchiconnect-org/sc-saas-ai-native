---
id: SAN-1985
title: "PENDING_CONNECTION_REMINDER template still invalid Handlebars in one production tenant DB (SC-SAAS-BACKEND-5N)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1985
sentry: [SC-SAAS-BACKEND-5N]
repos: [backend]
related: [SAN-1871, SAN-189, SAN-403]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1985: broken reminder template (tenant data)

## Investigation
* **Events:** 4 in production, at 00:00 UTC on 10-12, 10-15, 10-19 and 10-22, one per cron run.
  * Hosts: `ip-10-0-21-211` on 10-12, then `ip-10-0-21-180` (`app_start_time` 2026-10-14).
  * One event per run fits a **single tenant deployment**.
* **Error:** `Parse error on line 24: ...ence.</span></p>{{ #each connections<t`.
  * The caret is on the `#`: Handlebars allows no whitespace between `{{` and `#`.
  * The `connections<t` right after it shows that the rich-text editor also pushed HTML (`<t…`) into the mustache. The closing `}}` is probably missing or displaced too.
* **The tenant can't be named from Sentry.** The backend sets no tenant or domain tag on its events: there is no `setTag` in `src/instrument.ts`, and `tags[tenant]` / `tags[domain]` are empty on all 4 events. It is whichever ECS service runs on `ip-10-0-21-180` (an ops lookup).
* **The code already contains the damage.** SAN-189 / BACKEND-4Q changed `sendBulkPendingConnectionReminderEmail()` (`src/core/services/ses-email.service.ts` ~2696) to precompile once and log one error per run, instead of throwing per recipient. The cost is that this tenant's reminder emails are skipped.

## Code-side normaliser?
Not recommended.
* Rewriting `{{ #` to `{{#` alone would not make this template compile, because the mangled `connections<t…` tail comes right after it.
* Guessing at repairs to HTML-mangled mustaches could send wrong content to every recipient. The current fail-closed behaviour (log once, send nothing) is safer.
* The right place for a check is the admin template editor, validating on save. That is `sc-saas-admin` and out of scope here.

## Fix
None in code. This is a per-tenant data fix. In that tenant's DB, `spa_email_templates.template_content` for `template_code = 'pending-connection-reminder'` must use `{{#each connections}} … {{/each}}`.

## Blast radius / existing-flow impact
None (no change).

## Verification
* Sentry events and a code read.
* `npm run gates` for the slice: lint 0, test 0, test-floors 0, openapi-floors 0, build 1, unguarded-routes 0. The build failure is pre-existing and unrelated (see SAN-1976).

## Ops follow-ups
1. Identify the tenant, either way:
   * map ECS host `ip-10-0-21-180` (and `-211` for 10-12) to its service; or
   * run `SELECT id FROM spa_email_templates WHERE template_code='pending-connection-reminder' AND template_content LIKE '%{{ #%'` on each tenant DB.
2. Fix the row in the admin email-template editor, in source/HTML mode so it isn't mangled again.
3. Resolve 5N after the next 00:00 UTC run passes without the error.
4. Optional, as a separate ticket: tag backend Sentry events with the tenant (`app_domain`), so per-tenant data issues can be attributed.

## Related
SAN-1871, SAN-189, SAN-403.
