---
id: SAN-2024
title: "PENDING_CONNECTION_REMINDER still fails nightly: SAN-1985 normaliser not on main, and the row is unrepairable"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2024
sentry: [SC-SAAS-BACKEND-5N]
repos: [backend]
related: [SAN-189, SAN-403, SAN-1354, SAN-1871, SAN-1985]
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2024: 5N is one tenant's hand-edited template row

## Investigation
* 5 production events, all at 00:00 UTC from the reminder cron: 10-12 on `ip-10-0-21-211`, then 10-15, 10-19, 10-22 and 10-26 on `ip-10-0-21-180`. The latest `app_start_time` is 2026-10-14, i.e. the 10-11 `main` build.
* SAN-1985's `{{ #`→`{{#` normaliser (`4b69595e`) is on `development` / `ai_native_setup`, not on stagingdemo or main.
* After `{{#each connections` the row has `<t`, not `}}`. `<` is not valid in a Handlebars name, so even the normaliser can't make it compile.
* The SAN-1354 boot repair (on main) only fixes the exact broken shape we shipped, so this copy was edited by hand.
* The tenant can't be named: backend events carry no tenant tag, and `ip-10-0-21-180` hosts several tenant containers.

## Root cause
Tenant data (one `spa_email_templates` row), not code.

## Fix
None in code.

## Blast radius / existing-flow impact
None (no change).

## Verification
Read-only. `git merge-base --is-ancestor 4b69595e origin/main` → not an ancestor.

## Ops follow-ups
1. On each tenant DB, run `SELECT id FROM spa_email_templates WHERE template_code='pending-connection-reminder' AND template_content LIKE '%{{ #%'`. Fix the row to `{{#each connections}} … {{/each}}` in source mode.
2. Promote `4b69595e`, so the boot log names any row it can't repair.

## Decisions pending
* **Product owner:** when a tenant's customised template doesn't compile, should we fall back to `defaultTemplateContent` (logging one warning) instead of sending nothing? That is better for users, but it silently replaces the tenant's own wording.
* **Dev lead:** add a global `app_domain` tag in the `Sentry.init` call in `src/instrument.ts`, and set `SENTRY_RELEASE` in the prod task definitions, so backend events name the tenant and the build.
