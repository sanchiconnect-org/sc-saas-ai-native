# Secret rotation log (SAN-1562)

Every secret that has been visible in code, git history, logs, an API response or the UI since July 2026 is treated as compromised and rotated. This page is the log: what leaked, where, whether the leak itself is closed, and when the secret was rotated and where it lives now.

**Never write a secret's value here, in Linear or in Slack.** Names, locations and dates only.

**Order for each row:** close the leak (the fix is deployed to production), then rotate, then delete or encrypt any stored copies, then fill in *Rotated* and *New home*. Rotating before the leak is closed just leaks the new value.

Status key: ✅ done · 🟡 leak closed on dev only (not yet in production) · 🔴 still leaking · ⏳ rotation pending

## Runtime leaks (API responses, UI, logs, database copies)

| # | Secret | Where it was visible | Leak closed? | Rotated | By | New home | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Production RDS database passwords (each tenant DB, and the cockpit DB) | sc-saas-admin and tenants-admin "DB Administration" link, put in the URL (SAN-852, SAN-1557, SAN-1913) | 🟡 fixed on `ai_native_setup` (admin `b29a7bf1` + `b67d4f4a`, tenants-admin `c724e9f` + `e3f8b17`); production waits for the release (SAN-1939) | 2026-10-14 | Nirmal | servers' `.env` + `tenant_users.database_password` | **Rotate again after the release**: production still shows the new value in that link. |
| 2 | Custom-SMTP passwords (`email_password_ses`), every custom-SMTP tenant | (a) public `tenant-settings/:hostname` response, and `tenant-settings/%25` returned a tenant's settings to anyone (SAN-44); (b) copied into `ses_email_queue.email_data` (SAN-1160) | 🔴 (a) hotfix PR tenants #204, then S7 key check; 🟡 (b) backend `f173ecb7` on dev | ⏳ | | tenant row (encrypt later) | After rotating, clear old copies: `JSON_REMOVE` the SMTP settings from `ses_email_queue.email_data` in each tenant DB. |
| 3 | `factacy_api_key` | public `tenant-settings` response (SAN-44); also a hard-coded seed default in `sanchiconnect-saas-tenants/src/modules/global/repositories/global.repository.ts` (git history) | 🔴 hotfix PR #204 + S7; the seed default now reads `FACTACY_API_KEY` from the environment | ⏳ | | tenants `.env` (`FACTACY_API_KEY`) | Rotate with Factacy. |
| 4 | `currency_api_key` | hard-coded seed default in `global.repository.ts` (git history); public `tenant-settings` until 2026-10-14 | ✅ withheld from `tenant-settings` (tenants `440d15d`); seed reads `CURRENCY_API_KEY` | ⏳ | | tenants `.env` (`CURRENCY_API_KEY`) | Rotate with the currency API provider. |
| 5 | Azure AD client secret (`azure_client_secret`, per tenant with SSO) | public `verify_tenant` / `resolve-domain` response until 2026-10-14 (SAN-44 S1); also sc-saas-admin `config/config.php` in git history (Sep 2025) | 🟡 tenants `a4909dd` on dev; production waits for the release | ⏳ | | `tenant_users` row | Rotate in Azure (Entra ID) for each SSO tenant, then update the tenant row. |
| 6 | Analyzer API token (`analyzer_api_token`, per tenant) | public `verify_tenant` and `tenant-settings` responses until 2026-10-14 (SAN-44 S1) | 🟡 tenants `a4909dd` on dev | ⏳ | | `tenant_users` row + analyzer `api_keys` | Issue a new analyzer key per tenant (`/generate-api-key/`), store it in the tenant row, then delete the old `api_keys` row. |
| 7 | WATI WhatsApp token | `sc-saas-admin` `whatsapp_management.php` rendered it (SAN-29) | 🟡 admin `18ccaea6` on dev | ⏳ | | admin settings table | Rotate in WATI. |
| 8 | OTP codes and other email secrets | `service_usage` subject column (SAN-1161) | 🟡 backend `f173ecb7` on dev | n/a (OTPs expire) | | n/a | Clear stored copies: redact `service_usage.subject` rows in each tenant DB. |
| 9 | Admin/jury plaintext passwords; partner JWTs; chat login-link email tokens | backend `console.log` → pm2 logs, and Sentry breadcrumbs (SAN-1158, SAN-1559) | 🟡 backend `03272a21` (last leak) on dev | ⏳ | | n/a | Force password resets for admin/jury accounts created since 2025-09-18 (list via `service_usage`). Decide on rotating `JWT_SECRET` / `EMAIL_TOKEN_SECRET` (logs everyone out) or wait for expiry. Purge pm2 logs and Sentry events. |
| 10 | GitHub gateway key | named in the SAN-1562 description | ? | ⏳ | | GitHub Actions secret | Owner to confirm what this is and where it leaked. |

## Found in git history by the secret scan (SAN-1564, 13 Oct)

These are gone from the current code but stay in git history, so treat them as leaked until rotated.

| # | Secret type | Location (repo / file) | Since | Rotated | By | New home |
|---|---|---|---|---|---|---|
| 11 | Stripe key | sc-saas-backend `src/modules/events/events.service.ts`, `payments/payments.service.ts`, `payment-gateways/payment-gateways.service.ts` | Mar–Apr 2025 | ⏳ | | |
| 12 | AWS access key | sc-saas-backend `src/core/database/spa_admin.sql` | Apr 2023 | ⏳ | | |
| 13 | SendGrid API key | sc-saas-backend `src/core/database/spa_admin.sql` | Apr 2023 | ⏳ | | |
| 14 | AWS access key | sc-saas-admin `modules/google-filer-viewer.php` | Mar 2025 | ⏳ | | |

## Still in current code: review, then rotate or mark public

Generic scanner matches in today's `ai_native_setup`. For each, decide whether it's a real secret (rotate it and move it to config) or a public, client-side key (note why it's fine).

| # | Location | Review result |
|---|---|---|
| 15 | sc-saas-frontend `src/app/modules/market-insights/market-insights-menus.ts`: 4 Grafana-type tokens | |
| 16 | sc-saas-frontend `src/app/modules/connection-request-action-email/connection-request-action-email.component.ts`: a JWT | |
| 17 | sc-saas-frontend `src/CONSTS.ts`, `src/environments/environment{,.local,.prod,.staging}.ts`, `core/service/modal-handler.service.ts`, `modules/payment-gateways/payment-gateways.component.ts`, `modules/dynamic-forms/event-forms/form-array-field/form-array-field.component.ts` | |
| 18 | sc-saas-admin `config/admin-data/forms.php` (8), `includes/core_functions.php` (2), `modules/meetings/session_detail.php`, `modules/meetings/detail_backup.php`, `modules/intellectual_property/conversation.php` | |

Not findings: `sc-saas-backend/cloudfront-private-key.pem` (committed by design); matches under `sanchiconnect-saas-tenants-admin/vendor/` and in README examples.

## Done when (from SAN-1562)

- Every row has a rotation date and the place the secret now lives (GitHub Actions secret, Environment secret, or the vault).
- Stored copies are deleted or encrypted (rows 2 and 8).
- This log is linked from the Production Defects description.
