# Sentry sweep — 2026-10-22

* **Scope:** all Sentry projects, `is:unresolved`, last 14 days. 31 issues.
* **Filed:** SAN-1971 to SAN-1997 in the Linear **Production Defects** project, milestone M5, all assigned to Vishali.
* **Code changes:** pushed to `ai_native_setup_vishali`, one commit per ticket: backend `ef3a3902` (SAN-1976), `4703763b` (SAN-1984); frontend `0ddace11a` (SAN-1986), `335b4000b` (SAN-1993), `553628da2` (SAN-1994), `8584477bf` (SAN-1982), `f569f6c8a` (SAN-1977), `efdc62166` (SAN-1978), `e2ce74be1` (SAN-1983); admin `0fc5e3bf` (SAN-1989); tenants-admin `b7483af` (SAN-1973); tenants `52ce2c4` (SAN-1981). Not yet on main, so not deployed. Frontend gates passed; backend gates: build fails on a pre-existing local typeorm mismatch in `deploy-migrate.ts`, everything else 0.

## Tickets

| Ticket | Repo | Sentry | Outcome |
|---|---|---|---|
| [SAN-1971](SAN-1971-connections-401-deploy-lag.md) | frontend | 2J | Deploy lag: every 401 is on a release without SAN-1673. No change. |
| [SAN-1972](SAN-1972-admin-aktu-1045-recheck.md) | admin | ADMIN-14 | Same 10-14 burst as SAN-1922; `f7020899` not on main. No change. |
| [SAN-1973](SAN-1973-tenants-admin-too-many-connections-scanner-burst.md) | tenants-admin | TENANTS-ADMIN-4 | Dev scanner bursts on the shared MySQL. `.htaccess` now 404s probe extensions before PHP. |
| [SAN-1974](SAN-1974-admin-too-many-connections-dev-scanner.md) | admin | ADMIN-5 | `environment: local` dev containers on a pre-SAN-1736 build plus scanners. No change. |
| [SAN-1975](SAN-1975-profile-views-nan-deploy-lag.md) | backend | 3M | Deploy lag: SAN-1872 `acfeb44a` not on main. No change. |
| [SAN-1976](SAN-1976-corporate-ecosystem-sync-empty-in-list.md) | backend | 5V | `WHERE id IN ( )` from an empty `sectoralInterestIds` in the corporate ecosystem sync. Fixed + 4 tests. |
| [SAN-1977](SAN-1977-wishlist-504-unhandled-add-to-wishlist.md) | frontend | 2W | Wishlist fetch had no error callback; Save/Remove left the spinner on. Fixed + 3 tests. |
| [SAN-1978](SAN-1978-programs-management-status-0.md) | frontend | 1 | Deploy lag, plus one unguarded `fetchProgramManagementByCode` (404 → `/programs`). Fixed + 2 tests. |
| [SAN-1979](SAN-1979-ses-throttle-still-quota.md) | backend | 5R | SES `GetMessageInsights` quota shared by all tenants. Ops/infra decision. |
| [SAN-1980](SAN-1980-analyzer-aiomysql-connection-lost-on-close.md) | ai-analyzer | ANALYZER-7 | Idle pooled connections dropped by MySQL. Fix plan only (repo not cloned). |
| [SAN-1981](SAN-1981-tenants-ecosystem-startup-duplicate-user-link.md) | tenants | TENANTS-7 | Owner still linked to an older startup row; detach before relink. Fixed + 3 tests. Design decision pending. |
| [SAN-1982](SAN-1982-page-load-timing-console-warn-noise.md) | frontend | HK | HiBrowser-injected timing `console.warn`; narrow `beforeSend` drop. |
| [SAN-1983](SAN-1983-corporate-intro-loginfault-mislabel.md) | frontend | AW | Backend 500 = SAN-1976; log label `loginFault` → `corporateInfoFault`. |
| [SAN-1984](SAN-1984-work-email-validator-throws-on-non-string.md) | backend | 5T | Work-email validator threw on a missing email → 500. Now returns 400. Fixed + 10 tests. |
| [SAN-1985](SAN-1985-pending-connection-reminder-template-tenant-data.md) | backend | 5N | One tenant's template row is broken. Data fix (ops). |
| [SAN-1986](SAN-1986-dynamic-form-submit-null-fields.md) | frontend | HR | `formObject.fields.map` on null fields. Fixed + 2 tests. |
| [SAN-1987](SAN-1987-duplicate-label-fingerprint-deploy-lag.md) | backend | 3P | Deploy lag: SAN-1868 `3473722f` not on main. No change. |
| [SAN-1988](SAN-1988-s3-signature-deploy-lag.md) | backend | 9 | Deploy lag; quiet since the 10-14 restart. Recommend resolving. |
| [SAN-1989](SAN-1989-admin-action-array-explode.md) | admin | ADMIN-15 | Scanner `?action[]=` reached `explode()`. Non-string action → 404. |
| [SAN-1990](SAN-1990-startupinfofault-status-0-deploy-lag.md) | frontend | 3M | Deploy lag: SAN-569 `cac790292` not in any release that fired. |
| [SAN-1991](SAN-1991-search-filter-preview-deploy-lag.md) | frontend | HQ | Same site as SAN-1933; `d7d588876` not in prod release. |
| [SAN-1992](SAN-1992-sendotpfault-http-0-register.md) | frontend | HP | Network status 0, already handled in UI. Filter decision pending. |
| [SAN-1993](SAN-1993-resource-viewer-modal-duplicate-loader.md) | frontend | HN | Bare `<ngx-ui-loader>` in the modal removed; loader floor 88 → 87. |
| [SAN-1994](SAN-1994-step-two-product-no-stage-selected.md) | frontend | HJ | Next without a stage threw and lost business models. Fixed + 2 tests. |
| [SAN-1995](SAN-1995-industry-technology-empty-ids-deploy-lag.md) | frontend | D4, CN | Deploy lag: SAN-705 auto-save guard not in release. |
| [SAN-1996](SAN-1996-foundersfault-invalid-access-token-deploy-lag.md) | frontend | 96 | Expected expiry; SAN-471 filter not in release. |
| [SAN-1997](SAN-1997-mentorship-hours-forbidden.md) | frontend | 2Y | Expected 403; filter not in release. Minor UX decision pending. |

## Not ticketed
* **ANALYZER-4:** already open as SAN-1927 (In Review).
* **FRONTEND-17 (lightGallery), FRONTEND-14 (moment deprecation):** noise per the board policy.

## Decisions pending
* SAN-1981 (product): an owner-less stale startup row — keep searchable, hide, or delete?
* SAN-1976 (dev lead): wrap the post-save ecosystem sync so a sync failure never fails a successful save?
* SAN-1973 / SAN-1974 (dev lead): should a 1040 that survives the retries return a 503 page?
* SAN-1979 (infra): raise the SES quota, or stagger tenant cron minutes.
* SAN-1994 (product): disable Next until a stage is chosen?
* SAN-1992 (dev lead): filter `HTTP 0` / `0 Unknown Error` warns in `beforeSend`?
* SAN-1997 (product): what other account types should see at `/mentorship-hours`.

## Cross-cutting
* **Deploy lag again.** 13 of the 27 tickets are fixes that exist but aren't on `main`. Frontend branch is 99 ahead of `origin/main`, backend 127, admin 118, tenants-admin 46. Promoting and redeploying is still the highest-value action.
* **Dev hosts report as `environment: local`.** ADMIN-5, TENANTS-ADMIN-4, BACKEND-5V and -5T all came from dev containers. Setting `SENTRY_ENVIRONMENT=development` there would separate them from prod.
* **New findings, not yet ticketed:**
  * `GET api/v1/wishlist/:userId/:userAccountType` never checks `userId` against the logged-in user — any signed-in user on a tenant can read another user's wishlist (security).
  * `sanchiconnect-saas-tenants-admin/index.php:43-45` has the same unguarded `explode()` as SAN-1989.
  * Unhandled 409 on `users/team-members` and 403 on `mentorship/auto-entry` in the frontend.
