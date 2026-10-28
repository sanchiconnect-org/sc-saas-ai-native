---
id: SAN-2122
title: "partner-detail SHOW fails 1684 under concurrent DDL — getPKID() then returned an empty primary key"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2122
sentry: [SC-SAAS-ADMIN-17]
repos: [admin]
related: [SAN-2114, SAN-1630]
commit: admin@1b3774bf (branch ai_native_setup_vishali, pushed; shared with SAN-2114)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2122: retry SHOW COLUMNS once on 1684

## Root cause
* 17: 1 event, dev, `/partner-detail/219/details`. That page runs `$database->getPKID("partners")` (`modules/partner-detail.php:725`), which runs `SHOW COLUMNS FROM partners`.
* 1684 means MySQL skipped a table under concurrent DDL, here `users`, whose `partner_id` foreign key points at `partners`. The backend's TypeORM sync (`synchronize` on by default, `database.module.ts:34`) alters `users` when dev boots.
* When the SHOW failed, `getPKID()` returned `""` and the page carried on with an empty primary key. `getColumns()` had the same exposure.

## Fix
`core/db.php`: new protected `showColumns($table)`. It runs `SHOW COLUMNS` with 1684 marked expected (`expectErrors()` from SAN-2114). On a 1684 it waits 0.5 s and retries once; a second failure is reported to Sentry as before. `getColumns()` and `getPKID()` both use it, and the normal path is unchanged.

## Verification
* `php -l core/db.php` → no syntax errors
* 1684 can't be reproduced on demand. The real fix for the cause is turning `DB_SYNCHRONIZE` off on dev (SAN-1630 phase 4).
