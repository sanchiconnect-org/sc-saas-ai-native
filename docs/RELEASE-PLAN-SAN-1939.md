# Release plan: `ai_native_setup` to production (SAN-1939)

Updated 2026-10-26 against git; first written 2026-10-19. Release path from `docs/DEPLOYMENT.md`: `ai_native_setup → development → stagingdemo → main/master`. Each step is a PR approved by someone other than its author, merged with a **merge commit**, then "Build now" on that branch's Jenkins jobs.

**Decided (Nirmal, 2026-10-19): full release.** Each step ships everything on `ai_native_setup`, which is what dev has been testing.

## Where each repo stands (2026-10-26)

Commits each branch is missing compared with the one before it (GitHub compare):

| Repo | Prod branch | `ai_native_setup` not in `development` | `development` not in `stagingdemo` | `stagingdemo` not in prod | Status |
|---|---|---|---|---|---|
| sc-saas-admin | `main` | 7 | 0 | 0 | **Released to `main` on 2026-10-26**, except today's 7 commits. Hotfix PR #2642 (SAN-2043) is open. |
| ai-startups-analyzer | `main` | 6 | 0 | 0 | **Released to `main` on 2026-10-26**, except today's CI/revert commits. |
| sc-saas-3rdparty-webservices | `master` | 0 | 0 | 40 | Waiting for stage 3. |
| sanchiconnect-saas-tenants | `master` | 18 | 65 | 0 | Waiting for stage 2. `development` is frozen at 2026-10-22. |
| sc-saas-backend | `main` | 25 | 154 | 0 | Waiting for stage 2. `development` is frozen at 2026-10-22. |
| sanchiconnect-saas-tenants-admin | `main` | 9 | 44 | 0 | Waiting for stage 2. |
| sc-saas-frontend | `main` (+ `sanchiconnect`) | 30 | 111 | 0 | Waiting for stage 2. |

## Urgent: production admin is ahead of production backend

The plan required the backend before the admin. The admin went first, so once production admin is built from today's `main`, two features fail until the backend is released:

| Admin feature | Needs from the backend | Production backend today | Effect until the backend ships |
|---|---|---|---|
| Form builder public submission link (SAN-35) | `forms.public_share_token` column (created by the backend at startup) | Column missing | Creating a link fails ("Could not create the link"); every share link returns 404 |
| "Backdoor Access" / view as applicant (SAN-1959) | `POST v1/application-programs-management/admin/applicant-token` | Route missing | The button shows an error; there's no fallback to the old URL |

The backend's `development` branch (frozen 2026-10-22) has the column but **not** the applicant-token route. **Refresh `development` from `ai_native_setup` (stage 1 again) before stage 2**, for the backend and, to keep them consistent, for tenants, tenants-admin and the frontend.

## New environment keys

Set them **before** the app restarts. Every mode defaults to `log` (allow everything, log what's missing), so a key that's missing doesn't break anything until its mode is switched to `enforce`. On dev, `GATEWAY_KEY_MODE=enforce` without the key made every email and OTP fail with a 500: always set the key first, then the mode.

| App | Key | Value | Needed when |
|---|---|---|---|
| tenants API | `TENANT_SETTINGS_KEY_MODE` | `log` | This release |
| tenants API | `CURRENCY_API_KEY`, `FACTACY_API_KEY` | Provider keys | Only seeds missing `global_settings` rows; existing rows are unchanged |
| every backend | `AI_CREDITS_INTERNAL_API_KEY` | The tenants API's value | This release (SAN-44 S7) |
| every backend | `FACTACY_API_KEY` | The Factacy key | **This release.** Factacy now reads it from the backend's own environment (SAN-1941); unset means Factacy calls fail |
| every backend | `GATEWAY_INTERNAL_API_KEY` | Same value as the 3rdparty gateway's | Before `GATEWAY_KEY_MODE=enforce` |
| every backend | `ADMIN_BACKEND_INTERNAL_API_KEY` | Same value as that tenant's admin `.env` | Before `ADMIN_SERVER_KEY_MODE=enforce` |
| every backend | `ADMIN_SERVER_KEY_MODE`, `APPLICANT_TOKEN_MODE` | Leave unset (`log`) | Switch to `enforce` after the checks below |
| every backend | `SOCKET_AUTH_ENFORCE` | Leave unset (off) | `true` after the two-user chat check (SAN-1938) |
| every backend | `APPLICANT_TOKEN_SECRET` | Optional, long random | Signs applicant tokens; without it the key is derived from `JWT_SECRET_KEY`, and boot never fails |
| every backend | `TRUST_PROXY_HOPS` | Default `1` | Only if a server sits behind more than one proxy |
| every backend | `DEFAULT_ADMIN_PASSWORD` / `DEFAULT_ADMIN_EMAIL` | 12+ characters | Only for a **new** tenant's first boot (SAN-2015); unset means the seeded admin starts locked |
| every backend | `QA_FIXED_OTP`, `QA_FIXED_OTP_EMAILS` | **Never set on production** | Dev/QA only (SAN-1864) |
| 3rdparty gateway | `GATEWAY_INTERNAL_API_KEY` | Long random | Before `GATEWAY_KEY_MODE=enforce` |
| 3rdparty gateway | `GATEWAY_KEY_MODE` | `log` | `enforce` once every backend sends the key |
| every admin | `ADMIN_BACKEND_INTERNAL_API_KEY` | Same value as that tenant's backend | Nothing is sent while it's unset |
| analyzer | `ANALYZER_CORS_ORIGINS` | Leave unset | No browser calls the analyzer any more (SAN-2017) |

## Before the next PRs

1. Merge hotfix **#2642** (SAN-2043, "Couldn't prepare analysis" for forms with image/video answers) and build the production admin jobs.
2. **Stage 1 again:** `ai_native_setup → development` for backend, tenants, tenants-admin and frontend, and build dev server 2.
3. **RDS snapshot** of every tenant database and the cockpit database, right before the backend and tenants production builds.
4. Set the keys above on each server before its build.
5. A non-author reviewer for every PR.

## Production order

1. **sanchiconnect-saas-tenants** (log mode lets every call through).
2. **sc-saas-backend**, every client job, demo and SanchiConnect. **Most urgent**: production admin already needs it.
3. **sc-saas-3rdparty-webservices** (stage 3 only, `GATEWAY_KEY_MODE=log`).
4. **sanchiconnect-saas-tenants-admin**.
5. **sc-saas-frontend**: client `main`, demo `stagingdemo`, and the `sanchiconnect` branch (its own PR from `main`).

## Schema (backend and tenants, `synchronize: true`)

**Additive only**; no column is removed or renamed in either repo (checked against the entity diff).
- **Backend:** new tables `whatsapp_held_messages`, `user_consents`, `push_subscriptions`, `startup_kit_categories`, `startup_kit_submissions`; new columns `forms.public_share_token`, `users.what_you_missed_sent_at`, `verifications.attempts`. Integer `width` removed from entity definitions (SAN-1630), which stops repeated ALTERs and doesn't change data.
- **Tenants:** new `organizations_contracts` table.

## Checks after each production build

| Repo | Check | Expect |
|---|---|---|
| tenants | `GET /api/v1/public/global/tenant-settings/%25` | 404 |
| tenants | `GET .../verify_tenant/<one letter>` | 404 |
| tenants | pm2 log `[log mode]` lines | One per backend still missing its key; set it there |
| backend | App starts; new tables and columns exist | No errors in the pm2 log |
| backend | `GET /api/v1/health` | `ok` |
| backend + admin | Form builder: create a public submissions link, open it | Link works; an old id link returns 404 |
| backend + admin | Backdoor Access on an application | Opens the PWA with the application |
| backend | Factacy lookup on a startup | Returns data (needs `FACTACY_API_KEY`) |
| 3rdparty | Send an OTP and an email | Delivered; gateway log shows `GATEWAY_KEY_MODE=log` lines only for callers without the key |
| admin | Developer zone → DB Administration | `../db_admin.php`, no password in the URL |
| admin / tenants-admin | `GET /adminer/adminer.php` without a session | 403 |
| admin | Prepare an AI analysis on a form with an image answer | Runs (after #2642) |
| frontend | Chat between two users, typing, notifications | Still work (SAN-1892) |

Then `sc-saas-e2e` against staging (Ritu) at stage 2. After production, hand over to **SAN-1563** (Aman) for non-author verification.

## After the release, in order

1. Once each log is clean, switch to `enforce` one at a time and re-check: `TENANT_SETTINGS_KEY_MODE`, `GATEWAY_KEY_MODE`, `ADMIN_SERVER_KEY_MODE`, `APPLICANT_TOKEN_MODE`, then `SOCKET_AUTH_ENFORCE=true` (SAN-1938).
2. Remove each scanner `stagedGuards` entry once its mode is `enforce` everywhere (SAN-1561).
3. Dependabot ignore rules (SAN-2044) take effect once they're on the default branches.
4. Record each production deploy (repo, job, date, who) on SAN-1939.

Rotation of the Factacy and currency keys and of the old seeded admin password is **not** planned (decision 2026-10-26, SAN-1914 / SAN-2015).

## Rollback

As in `docs/DEPLOYMENT.md`: revert the merge on the production branch through a hotfix PR, then "Build now". The backend's new tables and columns stay (additive, harmless to old code). Restore from the RDS snapshot only if data was damaged. Users may keep the cached PWA until they reload.
