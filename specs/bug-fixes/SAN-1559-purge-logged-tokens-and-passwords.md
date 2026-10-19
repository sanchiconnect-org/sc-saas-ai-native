# SAN-1559 — Purge the auth tokens and passwords written to server logs by the SAN-1158 console.log calls, and invalidate affected sessions

- Linear: https://linear.app/sanchiconnect/issue/SAN-1559 (Urgent, milestone "P0 Stop the bleeding", due 2026-10-16; assignee Nirmal Singh; label Bug + Repo: Backend). Related: SAN-1158 (code fix, Done), PRA-5 (same follow-up, Prabhakar C).
- Repo: sc-saas-backend. Classification: mostly ENV_ERROR / operations (log purge, credential rotation, token invalidation happen on the servers, not in code), plus one CODE_ERROR left over from SAN-1158.

## Problem
SAN-1158 (commit `404c483c`, 30 Sep 2026, on `development` and `main`) removed three debug `console.log` calls that printed credentials. The values already written stay in pm2/server logs, and the ops follow-up had no owner.

## Evidence (checked in code, 2026-10-14)
1. **SAN-1158 missed one leak, still live.** `src/modules/conversations/conversations.service.ts` still did `console.log(chatPageUrl)`. `chatPageUrl` comes from `urlService.createAuthenticatedGroupChatUrl()`, whose `whatsappUrl` is `request/authenticate?token=<email JWT>&action=…`, a login link signed with `EMAIL_TOKEN_SECRET`. One link per group-chat member, printed on every group-chat message notification.
2. **The password log ran longer than SAN-1158 says.** `console.log('attributesToMap', …)` in `SESEmailService.sendAdminAccountCreatedEmail()` was added on **2025-09-18** (`c3331309`), not in August (`625b87f0` only changed the quotes). It printed the plaintext password of every non-SSO admin-panel account created through `POST api/v1/admin-actions/admin-account-created` (sc-saas-admin `auth/admins.php`, `partners/teams/list.php`, program-round / mentor-round / venture-studio jury invites; all write `spa_admin_users`).
3. **Leaked tokens may still be valid.** Locally `JWT_EXPIRES_IN_DAYS=30` (partner JWT from `getAdminConsoleUrl()`, logged since 2024-09-03) and `EMAIL_TOKEN_EXPIRES_IN_DAYS=90` (chat link token, logged since 2023-11-30). Check the production values. SAN-1158's note "session tokens expire with their JWT lifetime" means tokens logged on 30 Sep are valid until about 30 Oct.
4. **The values may also be in Sentry.** Backend Sentry (since 2026-07-28, `@sentry/node` v7) keeps its default Console breadcrumbs integration, which records `console.log` lines as breadcrumbs on every warn/error event. `scrubEvent` in `src/instrument.ts` scrubs request data, headers, `extra` and frame vars, but **not breadcrumbs**.
5. **Revocation options in code.** `JwtStrategy.validate()` checks no per-user revocation unless `single_session_login_enabled` is on (then only the token stored in `users_login_session` is accepted). Email tokens are stateless. The only global kill switch for either type is rotating `JWT_SECRET` / `EMAIL_TOKEN_SECRET` per deployment.

## Fix (code part)
Removed the remaining debug block in `ConversationsService` (the `groupUserIds`, `chatPageUrl` and `type` console.logs, 9 lines). This only removes logging; behaviour is unchanged.
Files: `sc-saas-backend/src/modules/conversations/conversations.service.ts`, plus regression test `sc-saas-backend/src/core/logging/no-credential-console-logs.spec.ts`. The test scans `src/` for `console.*` calls whose arguments, with string literals blanked, reference a token/password/secret/jwt/credential/authenticated-URL identifier. It fails on the old `conversations.service.ts` (`:185 console.log(chatPageUrl)`) and passes after the fix.

## Ops follow-up (not code, needs server/DB access and a decision)
- **Log retention / purge:** confirm the pm2 log location and retention on every backend server (and any log shipping). Purge or redact entries matching `attributesToMap`, `console.log('token'`, `receiverUserToken`, `chatPageUrl`, `request/authenticate?token=`. Delete or limit access to the Sentry events whose breadcrumbs contain them (2026-07-28 onwards).
- **Affected accounts (passwords):** `spa_admin_users` has no created-at column. Per tenant, list them from the email audit instead: `service_usage` rows with `service_type='ses-email'` and `JSON_UNQUOTE(data->'$.subject')` matching that tenant's `admin-account-created` subject ("Your account has been created …"), `created_at` from 2025-09-18 to the deploy date of `404c483c`. Then force a password reset for those accounts that are not SSO.
- **Tokens:** decision for the dev lead: rotate `EMAIL_TOKEN_SECRET` (every outstanding email action link stops working) and `JWT_SECRET` (every user is logged out) per deployment, or wait for expiry. For partner JWTs that's about 30 days. For chat-link email tokens it's up to 90 days, and new ones were logged until this fix deploys.
- ~~Code hardening to consider: scrub `event.breadcrumbs` in `scrubEvent`.~~ Done on 2026-10-15, see "Sentry hardening" below.

## Verification
- Repo-wide scan of `console.*` / `this.logger.*` calls for token/password/secret/otp/jwt/authenticated-URL arguments: only static strings remain (CometChat "Missing Username or Password", Stripe "Missing Stripe secret key").
- `eslint` on the changed file: 0 errors once the CRLF Windows checkout is accounted for (`core.autocrlf=true`). The same 4 existing unused-var warnings as `HEAD`.
- `jest src/modules/conversations src/core/services/ses-email.service.logging`: 38/38 pass. `conversations` has no spec of its own.
- `npm run gates` (sc-saas-backend): lint 0, test 0 (1316 passing, floor 1314), test-floors 0, build 0 → passed. The first run failed only because `web-push` (already in package.json) was missing from local node_modules; it was installed locally with `--no-save`.

## Commit
`d65db719` on sc-saas-backend `ai_native_setup_vishali` (pushed 2026-10-14). The ops follow-up is still open on SAN-1559.

## Sentry hardening (2026-10-15)
Evidence point 4 closed in code: Sentry now redacts secrets in breadcrumbs and by value, not only by key name.
- New `sc-saas-backend/src/core/logging/sentry-redact.ts`: `redactSecretsInText()` replaces JWTs (`eyJ….….…`),
  `?token= / access_token / accessToken / refresh_token / password / secret / jwt=` query values and `Bearer …`
  credentials; `redactSecretsDeep()` applies it to every string in a value. The patterns are shape-specific, so
  ordinary text, ids and URLs pass unchanged.
- `src/instrument.ts`: new `beforeBreadcrumb: scrubBreadcrumb` (message redacted; `data` redacted by value, then by
  key through the existing `scrubObject`), and `scrubEvent` now also redacts `event.message`, exception values and
  `event.breadcrumbs`. It runs after the fingerprint functions, so issue grouping is unchanged.
- This protects new events only. Events already stored in Sentry are untouched; deleting them is still the ops item
  above. Sentry search covers the message, not breadcrumbs, so a search for these values finding nothing does not
  prove they are absent.

Verification: `sentry-redact.spec.ts` (6 cases, including ordinary lines left unchanged) and the existing
`no-credential-console-logs.spec.ts` pass. An end-to-end script loaded the compiled `dist/instrument.js` (with a
placeholder DSN, so nothing was sent) and called the registered `beforeBreadcrumb` / `beforeSend` with a JWT, a
`?token=` login link, a password object, a Bearer header and an `http` breadcrumb carrying `?password=`: no secret
survived, and an ordinary message was kept. `tsc` clean; eslint 0 errors (LF, as CI sees it); `npm run build` OK; gates
`test` (1325 passing), `test-floors`, `openapi-floors` passed.
