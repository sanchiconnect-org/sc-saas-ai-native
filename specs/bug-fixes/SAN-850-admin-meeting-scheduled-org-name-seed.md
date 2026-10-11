---
id: SAN-850
title: "Duplicated \"from\" + literal <b> tag in mirrored 1:1 meeting email seed data"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-850
repos: [admin]
commit: sc-saas-admin@cd91485c (branch ai_native_setup_vishali, pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-850 — admin-data meeting-scheduled-to-sender seed fix

## Problem
Companion to [[SAN-849]] (sc-saas-backend). `sc-saas-admin/config/admin-data/email_templates.php` carries its own copy of the `meeting-scheduled-to-sender` template (row id 13), byte-for-byte identical to the buggy segment fixed in the backend seed. Per `modules/developer/module.spec.md`, this file is bulk-inserted into admin-data tables (including `spa_email_templates`) by `maintenance.php` "on demand" — a second live seed source for the same content.

## Root cause
CODE_ERROR — identical template/data-contract mismatch as SAN-849: hardcoded "from " + double-mustache `{{ organization_name }}` in the template, while `sc-saas-backend`'s `meetings.service.ts` supplies a self-contained `` ` from <b>${orgName}</b>` `` value. Duplicates "from" and shows literal `<b>` tags.

## Fix
Same one-line change as SAN-849, applied to `config/admin-data/email_templates.php` (~line 577):
```
<span data-offset-key="839d8-0-2"><span data-text="true"><strong> </strong>from &nbsp;<strong>{{ organization_name }}</strong></span></span>
```
→
```
<span data-offset-key="839d8-0-2"><span data-text="true">{{{ organization_name }}}</span></span>
```

## Important caveat — does not fix already-live tenant data
This only fixes the maintenance-seed snapshot used when `maintenance.php` bulk-re-inserts admin-data tables on demand — it does not retroactively touch an already-provisioned tenant's live `spa_email_templates` row. The tenant behind the reported screenshot needs a manual edit via the sc-saas-admin Email Templates management UI (find "[Meeting] Scheduled Meeting - To Sender", fix the "You have scheduled a meeting..." paragraph) to actually stop the broken email from going out — no code change can do that from here.

## Blast radius
`sc-saas-admin` seed data only (`config/admin-data/email_templates.php`). No functional code path changed.

## Verification
PHP not installed in this environment — `php -l` not run, noted as a gap. Diff manually verified: single string segment replaced inside an existing PHP array literal, no quote/comma structure disturbed (confirmed via `git diff`). No test framework exists for `sc-saas-admin`. Manual verification is the same as SAN-849 — re-render the template with a sample `organization_name` and confirm no duplicate "from" or visible tags.

Vishali confirmed the same duplicate-"from"/literal-`<b>` bug was independently visible in the **live** tenant's Email Templates editor (`adm.thub.sanchidev.in/developer/email_management`, `meeting-scheduled-to-sender`) and in a real sent email — matching this seed bug exactly, confirming this isn't just a seed-file issue but the actual production template content too. That live DB row still needs a manual admin-panel edit (this code fix doesn't reach it) — tracked as a follow-up, not part of this ticket's scope.

First attempt at this edit was lost: an external `git pull origin ai_native_setup` ran against this checkout between turns (visible in `git reflog`, fast-forwarding to the SAN-846/#2501 merge commit), and the uncommitted working-tree change didn't survive it even though that merge commit didn't touch this file. Re-applied cleanly and verified via `git diff` before committing.

Committed and pushed as `sc-saas-admin@cd91485c` on `ai_native_setup_vishali`. Linear moved to Done.

## Related
[[SAN-849]] — the backend counterpart, same fix.
