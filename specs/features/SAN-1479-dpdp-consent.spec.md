---
id: SAN-1479
title: "Consent and compliance (DPDP Act 2023): opt-in, one-click unsubscribe, stored consent records"
type: feature
status: in-review               # implemented 2026-10-13, awaiting Mahima's verification; not committed
linear: https://linear.app/sanchiconnect/issue/SAN-1479
owner: mahima.s@sanchiconnect.com
repos: [backend, frontend]      # dependency order
contracts:
  api:
    - "GET   api/v1/consent                        (backend, NEW, JWT): current consent state"
    - "PATCH api/v1/consent                        (backend, NEW, JWT): grant/withdraw per channel × category"
    - "GET   api/v1/consent/unsubscribe/:token     (backend, NEW, PUBLIC, rate-limited, read-only): what the link covers"
    - "POST  api/v1/consent/unsubscribe/:token     (backend, NEW, PUBLIC, rate-limited): withdraw email consent"
    - "GET   api/v1/migrations/backfill-user-consents/:adminMd5 (backend, NEW, adminMd5 like the other migrations): one-time audit rows for existing users"
    - "POST  api/v1/user/update/notification       (backend, CHANGED: now JWT-guarded and acts on the logged-in user only; body.email ignored)"
  flags: []                     # decision: all tenants at once, no flag
  events: []
tenant_scoped: true             # user_consents lives in each tenant DB (one deployment per tenant)
depends_on: [SAN-1478]
created: 2026-10-13
---

# Consent and compliance (DPDP Act 2023)

## Problem
SAN-1479 (BRD EX-20, §13, §15) requires explicit opt-in for email and WhatsApp, one-click unsubscribe, and stored consent records with time and source. Today there is no consent table. The only "unsubscribe" is `POST user/update/notification`, which has its JWT guard commented out and takes a raw email in the body. Anyone can unsubscribe anyone, or re-enable promotional email for someone who opted out. It also reveals whether an email has an account (404 vs 200). The email footer links to `/account/edit/email/notification/<raw email>`, and that page unsubscribes as soon as it opens, so mail scanners that prefetch links trigger it.

## Decisions (answered by Mahima, 2026-10-13)
- **D1 Existing users:** treated as opted in from their current settings. A one-time backfill writes `source=migration` rows.
- **D2 Granularity:** channel (email, WhatsApp) × category (marketing, digest, activity). `system` (OTP, password reset, verification, security, legal copies) is always sent and cannot be withdrawn.
- **D3 Rollout:** all tenants at once. No feature flag.
- **D4 Scope:** backend + frontend this pass. Admin consent-history view is a follow-up.
- **D5 New users:** a one-time post-login consent prompt covers every signup path. Until they choose: activity email stays on, marketing/digest email and all WhatsApp stay off.

## Design
- **Ledger:** new append-only table `user_consents` (`user_id`, `email` snapshot, `channel`, `category`, `status` granted|withdrawn, `source` prompt|settings|unsubscribe_link|migration, `ip`, `user_agent`, `created_at`). Rows are never updated. The newest row per user × channel × category is the history; the live state is mirrored on the user (below).
- **Live state (mirror):** `users.notification_settings.consent = { decided, email: {marketing, digest, activity}, whatsapp: {marketing, digest, activity} }`, plus `users.promotional_emails_enabled = email.marketing`.
  - Mirroring into fields that existing send paths already check means no email/WhatsApp caller has to change:
    - Broadcast recipients already require `promotional_emails_enabled` (`user.repository.ts` `getApprovedStakeholderUsers`).
    - Activity emails and chat WhatsApp already go through `shouldSendNotification` / `shouldSendWhatsappNotification` (`core/utils/app.utils.ts`, ~20 call sites). Both now return false when the matching `consent.<channel>.activity === false`.
  - `mergeNotificationSettings` keeps unknown top-level keys, so the existing settings PATCH never drops `consent`.
- **Derived state** (users with no `consent` key yet, e.g. before the backfill): email.marketing = `promotional_emails_enabled && all_emails_enabled`; email.digest = `all_emails_enabled`; email.activity = any topic email toggle on (or no settings); WhatsApp (all categories) = any topic WhatsApp toggle on (or no settings). `decided = true`, so no prompt.
- **New users:** `UserEntity` `@BeforeInsert` sets `consent.decided = false`, the D5 defaults, and `promotional_emails_enabled = false`. Every in-app signup path (register, event, other, job-seeker, startup, partner, import, challenge corporate) creates users through `entity.save()`, so the hook covers them. [INFERRED] Users inserted directly by `sc-saas-admin` (PHP) get no `consent` key and keep today's behaviour.
- **Unsubscribe token:** `base64url(email).base64url(HMAC-SHA256(jwt secret, "unsubscribe:" + email))`. No expiry, because unsubscribe links must keep working. No DB lookup at send time. The footer link becomes `<frontend>/unsubscribe/<token>`.
- **Legacy writers record consent too:** profile update with `promotionalEmailsEnabled` → email.marketing (source settings); topic toggles PATCH → email.activity / whatsapp.activity when the "any toggle on" value changes (source settings).

## Acceptance criteria
- [ ] `user_consents` is created by `synchronize` and only ever inserted into.
- [ ] `GET/PATCH api/v1/consent` read and write the matrix for the logged-in user; `system` is not accepted.
- [ ] Every change writes one row per changed channel × category with source, IP and user agent.
- [ ] `POST api/v1/consent/unsubscribe/:token` with a valid token withdraws email marketing (default) or all email categories (`scope: all`); an invalid token returns 400 and does not reveal whether the email exists.
- [ ] `GET` on the unsubscribe link changes nothing (scanner-safe).
- [ ] `POST user/update/notification` requires a JWT and only changes the logged-in user.
- [ ] Withdrawn email.activity stops connection/meeting/chat emails; withdrawn whatsapp.activity stops chat WhatsApp; withdrawn email.marketing removes the user from broadcast recipients.
- [ ] System emails (OTP, password reset, verification) are unaffected.
- [ ] Existing users: no change in what they receive, and no prompt.
- [ ] New users see the consent prompt once after login; their choice is recorded with `source=prompt`.
- [ ] The backfill endpoint is idempotent (skips users who already have rows).

## Per-repo plan
### backend
- `src/modules/consent/`: `entities/user-consent.entity.ts`, `consent.types.ts`, `consent-token.util.ts`, `consent.service.ts`, `consent.controller.ts`, `dto/update-consent.dto.ts`, `dto/unsubscribe.dto.ts`, `consent.module.ts`, `module.spec.md`. Registered in `app.module.ts`.
- `core/utils/app.utils.ts`: consent check in `shouldSendNotification` and `shouldSendWhatsappNotification`.
- `core/types/notification-type.ts`: optional `consent` key.
- `core/services/ses-email.service.ts`: footer uses the signed token link.
- `modules/user/entities/user.entity.ts`: `@BeforeInsert` new-user defaults.
- `modules/user/user.service.ts` + `user.controller.ts`: guard `update/notification`; record consent from legacy writers.
- `modules/migrations/`: `backfill-user-consents/:adminMd5`.
- `core/constants/enum.ts`: `RateLimitKeyPrefix.CONSENT_UNSUBSCRIBE`.

### frontend
- `core/service/consent.service.ts` + `ApiEndpointService` `CONSENT` endpoint.
- `core/domain/profile.model.ts`: optional `consent` on `NotificationSettings`.
- Unsubscribe page: new public route `unsubscribe/:token`; shows what will stop and asks for one click; the old `account/edit/email/notification/:email` route shows "link expired, log in to manage settings".
- Email settings page (`mail-notification-setting`): consent matrix (email/WhatsApp × promotional/digest/activity) with a "security emails are always sent" note.
- Consent prompt component, shown once when `consent.decided === false`.

## Contracts & invariants
- New endpoints only. `update/notification` is tightened; its only callers are the frontend unsubscribe page (moved to the token flow) and an unused method on the settings page. Admin does not call it.
- No flag (D3). Tenant isolation is by database; no cross-tenant reads.
- Auth model stated per endpoint above. The public unsubscribe endpoints are rate-limited and token-authenticated.

## Test plan
- Unit: token sign/verify (tamper, wrong secret, malformed); derived state; diff → rows; mirror to `promotional_emails_enabled` and `consent`; `shouldSendNotification` / `shouldSendWhatsappNotification` with consent withdrawn; existing `user.service.notification-settings.spec.ts` still passes.
- Type-check and lint both repos; frontend production build.
- Manual: unsubscribe link from a real email; prompt on a new account; settings page round-trip.

## Rollout
1. Deploy the backend (synchronize creates `user_consents`), then the frontend.
2. Run `GET api/v1/migrations/backfill-user-consents/<adminMd5>` once per tenant for the audit rows.
3. Old footer links already in inboxes show "link expired, log in to manage settings".

## Out of scope / follow-ups
- `List-Unsubscribe` / `List-Unsubscribe-Post` headers: the gateway (`sc-saas-3rdparty-webservices`) does not pass custom headers yet. This needs a gateway DTO change.
- Non-chat WhatsApp sends (program-management, corporate, resources, metrics, auth OTP) are transactional/system and are not gated in this pass.
- The "What you missed" user digest (SAN-1477) has no sender in the backend today, so `digest` is recorded but has nothing to gate yet.
- Admin consent-history view/export (D4).
- Retention period for consent records (not decided; rows are kept).

## Open questions
None blocking. Retention is listed as a follow-up.
