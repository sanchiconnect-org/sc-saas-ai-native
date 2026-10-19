# Release plan: security fortnight fixes to production (SAN-1939)

Checked against git on 2026-10-19. Release path from `docs/DEPLOYMENT.md`: `ai_native_setup → development → stagingdemo → main/master`, each step a PR approved by someone other than its author (branch protection is on), then "Build now" on that branch's Jenkins jobs.

## What this release carries

`development`, `stagingdemo` and the production branch are level in every repo, so each step ships **everything** on `ai_native_setup`, not only the security fixes (about 280 commits). Hotfixes already on production (#84–#86, #2628, and #204 once merged) are on `ai_native_setup` as `-x` cherry-picks, so they arrive a second time with the same content.

| Repo | Prod branch | Commits | Security | Other notable changes | Schema (`synchronize: true`) |
|---|---|---|---|---|---|
| sanchiconnect-saas-tenants | `master` | 42 | 16: SAN-44 S1/S2/S4/S5 (no secrets in `verify_tenant`; `currency_api_key` withheld), exact hostname match (#204), S7 log mode, SAN-852 guard | generated contract types (SAN-1595), CI | none |
| sc-saas-backend | `main` | 63 | 19: SAN-1160/1161 (SMTP password and OTPs no longer stored), SAN-1158/1559 (no tokens in logs), SAN-35 share token, SAN-44 S7 key | push and WhatsApp notifications, tentative rounds, **consent ledger (new users default to marketing/digest email off)**, typed API responses, QA OTP wildcard | **additive only**: new tables `whatsapp_held_messages`, `user_consents`, `push_subscriptions`; new columns `forms.public_share_token`, `users.what_you_missed_sent_at` |
| sc-saas-frontend | `main` | 50 | 9: SAN-1892 socket handshake | push notifications and digest settings, community feed tests, typed OTP response | none |
| sc-saas-admin | `main` | 64 | 32: SAN-22, 23, 24, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 1894, 1906, 1909; DB-link fix (`b29a7bf1`, `b67d4f4a`) | bulk actions (SAN-1485), notification centre sections, AI-credit schema checks | none |
| sanchiconnect-saas-tenants-admin | `main` | 23 | 11: SAN-42, 43, 46, 1907; DB-link fix (`c724e9f`, `e3f8b17`) | Client Stats page (SAN-1910) | none |
| ai-startups-analyzer | `main` | 19 | 4 | Serper/Firecrawl counts (SAN-1723); already-hotfixed thesis/auth changes | none |
| sc-saas-3rdparty-webservices | `master` | 19 | 4 | CI only (`ci-secret-test.txt` was added and removed on 13 Oct; not in the tree) | none |

**Decided (Nirmal, 2026-10-19): full release.** Each step ships everything on `ai_native_setup`, which is what dev has been testing, rather than a security-only cherry-pick set that has never run anywhere as a whole.

## Before the first PR

1. **Dev sign-off**: the fixes are tested on dev server 1 (`thub.sanchidev.in`), per the standing "test on dev before release".
2. **#204 merged and deployed** (tenants hotfix). Stops the `tenant-settings/%25` leak today, independent of this release.
3. **RDS snapshot** of every tenant database and the cockpit database, right before the backend and tenants builds: the backend adds tables and columns at startup.
4. **Environment variables**, set before each app restarts:
   - every sc-saas-backend `.env`: `AI_CREDITS_INTERNAL_API_KEY` = the tenants API's value (SAN-44 S7);
   - tenants API `.env`: `TENANT_SETTINGS_KEY_MODE=log`.
5. **Reviewer lined up**: every PR needs one approval from someone who isn't its author.

## Order

Each repo goes through all three stages before its production build. Deploy order matters at the production stage:

1. **sanchiconnect-saas-tenants** first. Its new log mode lets every call through, so it is safe before the backends send the key.
2. **sc-saas-backend**, every client job (26), demo and SanchiConnect. Must be live **before sc-saas-admin**, because SAN-35 needs `forms.public_share_token` to exist.
3. **sc-saas-3rdparty-webservices** and **ai-startups-analyzer** (independent; CI and small changes).
4. **sc-saas-admin** and **sanchiconnect-saas-tenants-admin**.
5. **sc-saas-frontend**: client `main`, demo `stagingdemo`, and the SanchiConnect `sanchiconnect` branch (needs its own PR from `main` or `stagingdemo`, since it sits outside the release path).

## Each stage, per repo

| Stage | PR | Build | Check |
|---|---|---|---|
| 1 | `ai_native_setup → development` | dev server 2 jobs | app starts; smoke the changed areas |
| 2 | `development → stagingdemo` | Demo jobs (production servers) | `sc-saas-e2e` against staging (Ritu); checks below on the demo tenant |
| 3 | `stagingdemo → main/master` | client production jobs | checks below on one client, then roll out to all |

Merge commits only (no squash), so the cherry-picked hotfix commits on the production branches reconcile cleanly.

## Checks after each production build

| Repo | Check | Expect |
|---|---|---|
| tenants | `GET /api/v1/public/global/tenant-settings/%25` | 404 |
| tenants | `GET .../verify_tenant/<one letter>` | 404 |
| tenants | pm2 log `SAN-44 S7 [log mode]` lines | one per backend still missing the key; set it there |
| backend | the app starts; `users`/`forms` tables have the new columns | no errors in the pm2 log |
| admin | Developer zone → DB Administration link | `../db_admin.php`, no password in the URL |
| admin / tenants-admin | `GET /adminer/adminer.php` without a session | 403 |
| admin | `GET /form_builder/public_submissions/<id>/<slug>` (old id link) | 404 |
| admin | filemanager, aws, csv export endpoints without a session | redirect to login, or 403 |
| frontend | chat between two users; typing; notifications | still work (handshake fix SAN-1892) |

Then hand over to **SAN-1563** (Aman): non-author verification of each finding, with the request and response pasted on the finding.

## After the release

1. **Rotate** per `docs/SECRET-ROTATION-LOG.md`: RDS again, every custom-SMTP password, `factacy_api_key`, Azure client secrets, analyzer tokens, WATI token. Clear `ses_email_queue.email_data` SMTP copies and `service_usage` OTP subjects in each tenant DB.
2. **SAN-1938**: two-user smoke test, then `SOCKET_AUTH_ENFORCE=true` on every backend.
3. **SAN-44 S7**: once the tenants log shows no `[log mode]` lines, set `TENANT_SETTINGS_KEY_MODE=enforce`.
4. Record each production deploy (repo, job, date, who) on SAN-1939.

## Rollback

As in `docs/DEPLOYMENT.md`: revert the merge on the production branch through a hotfix PR, then "Build now". The backend's new tables and columns stay (additive, harmless to the old code); restore from the RDS snapshot only if data was damaged. Users may keep the cached PWA until they reload.
