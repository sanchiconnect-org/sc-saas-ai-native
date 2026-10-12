# SAN-1871 — `pending-connection-reminder` email template in the tenant DB has invalid Handlebars (operator fix)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1871 (Sentry SC-SAAS-BACKEND-4Q and BACKEND-5N) — status **TODO, not done**
- **Repo:** sc-saas-backend (code already handles it); the fix is operator data in the tenant DB · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** DATA / CONFIGURATION error, no code change

## Evidence
- BACKEND-4Q: 39 production events, one per recipient, render failures from a build that predates SAN-189.
- BACKEND-5N: 1 event from current code.
- The stored `pending-connection-reminder` template contains `{{ #each connections<...` (a space after `{{` and a mangled tag), which is invalid Handlebars.

## Root cause (observed vs inferred)
- **Observed:** the template body is stored in the **tenant DB** (admin email templates), not in code, and it fails to compile.
- The code in `src/core/services/ses-email.service.ts` (~2696) already precompiles the template once and logs one error per cron run (SAN-189), so the volume is now one event per run, not per recipient.

## Fix
None in code. **Operator action:** in the admin email templates, replace the body so the loop reads `{{#each connections}} ... {{/each}}` (no space after `{{`, closing `{{/each}}`). Until then the reminder email is **not sent**.

## Not fixed
Everything: this issue stays open until the template is corrected in each affected tenant DB (not checked which tenants carry it).

## Contract impact
None. No API, DTO, flag or auth change; no code change.

## Verification
Not applicable (no change made). The Handlebars diagnosis comes from the Sentry events; the stored template itself was not opened.

## Commit
None.

## Sentry
BACKEND-4Q and BACKEND-5N left **open**. Resolve after the template is fixed and one cron run completes without the error.
