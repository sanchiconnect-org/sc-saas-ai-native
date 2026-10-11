---
type: index
repo: backend
updated: 2026-10-08 # SAN-1467
---

# Backend Module Specs — Index

All 60 `sc-saas-backend` modules under `src/modules/` have a `module.spec.md` (up from 58 — `startup-recognition-id` and `public-portal` were added this pass, both new SAN-253/public-portal-work modules that previously had no spec coverage), plus 3 real bounded-context directories under `src/core/` (`zoho`, `upload-module`, `sockets` — the rest of `core/` is cross-cutting infra like `config`/`guards`/`entities`/`decorators`/`utils` and deliberately has no spec) — **63 specs total**. This index maps each to its spec, summarises its role, and flags security/quality notes surfaced during spec authoring.

> **How to use:** When working on a module, read its spec first — it records owned routes, consumed flags, tenant-scoping mechanism, invariants, and known footguns. When adding a route or flag gate, update the spec's `owns` / `consumes` frontmatter and `updated` date.

---

## Auth & Identity

| Module | Spec | Notes |
|---|---|---|
| `auth` | [spec](../sc-saas-backend/src/modules/auth/module.spec.md) | JWT issuance, OTP login, per-type registration. The auth contract every other module depends on. |
| `auth-external` | [spec](../sc-saas-backend/src/modules/auth-external/module.spec.md) | Cross-tenant user import/export flow. No JWT on any route — OTP + feature flags only. Bug: `default` branch passes `undefined` userId. |
| `user` | [spec](../sc-saas-backend/src/modules/user/module.spec.md) | Profile CRUD for all stakeholder types; widest-dependency module (11 imports). `update/notification` and `profile-views/increment` are unauthenticated. `deleteUserInformation` DB cleanup is commented out. |
| `verifications` | [spec](../sc-saas-backend/src/modules/verifications/module.spec.md) | OTP send/verify. **High-severity bug:** OTP stored as md5 but compared against raw plaintext — verification always fails unless client sends md5. |

---

## Applications & Programs

| Module | Spec | Notes |
|---|---|---|
| `application-management` | [spec](../sc-saas-backend/src/modules/application-management/module.spec.md) | Form submission, review, and scoring pipeline. |
| `form-management` | [spec](../sc-saas-backend/src/modules/form-management/module.spec.md) | Dynamic form builder and renderer. |
| `program-management` | [spec](../sc-saas-backend/src/modules/program-management/module.spec.md) | Incubator program CRUD + payment reminders. `payment-reminder/:adminMd5` has admin-check commented out — fully unauthenticated write. `updateRound()` now also triggers Startup Recognition ID generation (SAN-253) and drives `startup_reapplication_history`; a DI crash-loop from a missed provider registration (`CitiesRepository`/`DistrictsRepository`/`SubDistrictsRepository`) was fixed this pass. |
| `program-office-members` | [spec](../sc-saas-backend/src/modules/program-office-members/module.spec.md) | POM stakeholder lifecycle + ecosystem sync. Circular dep with `EcoSystemModule` via `forwardRef`. |
| `vs-programs-management` | [spec](../sc-saas-backend/src/modules/vs-programs-management/module.spec.md) | Venture Studio program rounds. Most `@Features(VENTURE_STUDIO)` annotations commented out. `getProgram` creates a DB row on every read. |
| `jury-nda` | [spec](../sc-saas-backend/src/modules/jury-nda/module.spec.md) | Schema-only (FA-010): `jury_nda_versions` + `jury_nda_acceptances` for Jury NDA Signing. No routes yet; email endpoints + retry cron to follow. Jurors sign in sc-saas-admin; this module owns the tables only. |

---

## Stakeholder Profiles

| Module | Spec | Notes |
|---|---|---|
| `startup` | [spec](../sc-saas-backend/src/modules/startup/module.spec.md) | Largest module (44 routes, 6 controllers). Pitch-deck, founders, funding, advisory board, and (new SAN-253) self-service Digital ID Card fetch. `public/startup-information` uses unverified JWT for gating. |
| `startup-recognition-id` | [spec](../sc-saas-backend/src/modules/startup-recognition-id/module.spec.md) | **New this pass.** Owns schema for Startup Recognition ID / Digital ID Card (SAN-253) — deliberately **no controller**; format config, Standard Geography, and Card templates are admin-configured tables `sc-saas-admin` reads/writes directly via Medoo. Only in-process behavior: round-entry ID generation, called from `program-management`. District/Sub-District segments are a live no-op today — no city has real district mapping data yet. |
| `individual` | [spec](../sc-saas-backend/src/modules/individual/module.spec.md) | Individual stakeholder profile. |
| `investor` | [spec](../sc-saas-backend/src/modules/investor/module.spec.md) | Investor profile and portfolio. |
| `corporate` | [spec](../sc-saas-backend/src/modules/corporate/module.spec.md) | Corporate stakeholder profile. |
| `mentors` | [spec](../sc-saas-backend/src/modules/mentors/module.spec.md) | Mentor profile + application management. `FeatureGuard` on application controller but no `@Features` — gate never fires. Ecosystem sync on edit is NOT best-effort. |
| `partner` | [spec](../sc-saas-backend/src/modules/partner/module.spec.md) | Partner lifecycle + startup onboarding. `premium-module/request` is fully open and can trigger SES to arbitrary addresses. `admin-console` leaks JWT in URL. |
| `service-providers` | [spec](../sc-saas-backend/src/modules/service-providers/module.spec.md) | Service provider profile. `public/service-provider-information` exposes all columns unauthenticated. |

---

## Ecosystem & Discovery

| Module | Spec | Notes |
|---|---|---|
| `ecosystem` | [spec](../sc-saas-backend/src/modules/ecosystem/module.spec.md) | Proxies search/profiles to the cockpit directory. Shared mutable `requestHeader` — concurrency bug. Admin push routes have no JWT. |
| `search` | [spec](../sc-saas-backend/src/modules/search/module.spec.md) | Stakeholder typeahead across 9 types. Profile typeahead has no feature gate or JWT. `StakeholderAccess` computed but never forwarded — partner scoping is a no-op. |
| `elastic-search` | [spec](../sc-saas-backend/src/modules/elastic-search/module.spec.md) | Elasticsearch index sync (20 routes). **All routes unauthenticated** — only `elastic_search` feature flag. Controller registered as both controller and provider. |
| `compare` | [spec](../sc-saas-backend/src/modules/compare/module.spec.md) | Side-by-side stakeholder comparison. |
| `connections` | [spec](../sc-saas-backend/src/modules/connections/module.spec.md) | Connection requests between stakeholders. |
| `connections-wishlist` | [spec](../sc-saas-backend/src/modules/connections-wishlist/module.spec.md) | Saved / wishlist connections. |

---

## Events & Community

| Module | Spec | Notes |
|---|---|---|
| `events` | [spec](../sc-saas-backend/src/modules/events/module.spec.md) | Event creation, registration, and attendance. |
| `community-wall` | [spec](../sc-saas-backend/src/modules/community-wall/module.spec.md) | Social feed / wall posts. |
| `challenges` | [spec](../sc-saas-backend/src/modules/challenges/module.spec.md) | Innovation challenge lifecycle. |
| `news` | [spec](../sc-saas-backend/src/modules/news/module.spec.md) | External news proxy + per-user category prefs. **All 4 routes have `JwtAuthGuard` commented out.** Preference write has no ownership check. |
| `notifications` | [spec](../sc-saas-backend/src/modules/notifications/module.spec.md) | Inbox + the SAN-1381 notification centre: `GET notifications/counters` (bell + badges, catch-up, `communityWallSince`, `opportunities.unseen`), section visits, item views, narrowed mark-all-read, live-feed items, 90-day purge, application-status and event-reminder writers. Gated by `notification_centre_enabled` (strict `true`). Badge = list on real MySQL: `badge-equals-list.integration.spec.ts` (opt-in). 6 cron-trigger POSTs are still open. The old `getNotifications` precedence bug was fixed in SAN-1409. |

---

## Mentorship & Learning

| Module | Spec | Notes |
|---|---|---|
| `mentorship` | [spec](../sc-saas-backend/src/modules/mentorship/module.spec.md) | Mentorship session booking + hour logging. Auto-entry email commented out. `console.log(session)` leaks session data. |
| `learning-management` | [spec](../sc-saas-backend/src/modules/learning-management/module.spec.md) | LMS — courses, modules, videos. `GET videos/:id/hls-url` is fully unprotected (returns signed CloudFront HLS URLs). Only `STARTUP` role can enroll. |
| `certificates` | [spec](../sc-saas-backend/src/modules/certificates/module.spec.md) | Certificate generation and issuance. |
| `id-cards` | [spec](../sc-saas-backend/src/modules/id-cards/module.spec.md) | Digital ID card generation. |

---

## Finance & Payments

| Module | Spec | Notes |
|---|---|---|
| `payment-management` | [spec](../sc-saas-backend/src/modules/payment-management/module.spec.md) | Multi-gateway hub (PayPal, Razorpay, Stripe, Easebuzz, PayU). **Nearly every route is unauthenticated** (`JwtAuthGuard` commented out). Self-import `forwardRef`. |
| `memberships` | [spec](../sc-saas-backend/src/modules/memberships/module.spec.md) | Membership tiers + upgrade requests. Majority of routes have JWT commented out. Any caller can submit upgrade for any `profileId`. |
| `invoice` | [spec](../sc-saas-backend/src/modules/invoice/module.spec.md) | PDF invoice generation → S3 upload. Single unauthenticated endpoint; no DTO validation on file-write path. |
| `grants` | [spec](../sc-saas-backend/src/modules/grants/module.spec.md) | Entity stub only (no controller/service). Two grant entities registered for admin panel use. |
| `schemes-management` | [spec](../sc-saas-backend/src/modules/schemes-management/module.spec.md) | Empty controller stub — no routes; now consumed by `operational-cost-reimbursement`'s find-or-create scheme row (SAN-756). |
| `operational-cost-reimbursement` | [spec](../sc-saas-backend/src/modules/operational-cost-reimbursement/module.spec.md) | SAN-756/757/758 (T-RISE). 12-month eligibility grid, Month-1 claim submission, admin single/bulk download-triggers-Under-Process with immutable first-download stamp + transition email. New `AdminTokenGuard`. Flag: `operational_cost_reimbursement_enabled`. |

---

## Meetings, Chat & Messaging

| Module | Spec | Notes |
|---|---|---|
| `meetings` | [spec](../sc-saas-backend/src/modules/meetings/module.spec.md) | Meeting scheduling + video integration. `feedback-reminder/trigger` and `/:code/complete` are unauthenticated. |
| `chat` | [spec](../sc-saas-backend/src/modules/chat/module.spec.md) | CometChat integration and messaging. |
| `conversations` | [spec](../sc-saas-backend/src/modules/conversations/module.spec.md) | Threaded conversation management. |
| `tickets` | [spec](../sc-saas-backend/src/modules/tickets/module.spec.md) | Support ticket system. Clean, fully gated. SES failures on create are NOT swallowed (can block writes). |

---

## Content & Resources

| Module | Spec | Notes |
|---|---|---|
| `resources` | [spec](../sc-saas-backend/src/modules/resources/module.spec.md) | Resource library + download tracking. Two `send-email` endpoints on different guard levels. `convert-to-image` has no auth. `ResourceCategoriesEntity.title` typed `number` but maps to `varchar`. |
| `glossary` | [spec](../sc-saas-backend/src/modules/glossary/module.spec.md) | Term dictionary. No auth on either route. `getWord()` doesn't filter by `isActive`. |
| `dashboard` | [spec](../sc-saas-backend/src/modules/dashboard/module.spec.md) | Analytics dashboard aggregation. |
| `metrics` | [spec](../sc-saas-backend/src/modules/metrics/module.spec.md) | Custom chart metrics. Invite codes generated but never persisted — can't be redeemed. Two v1 endpoints use different time-bucketing keys. |

---

## Jobs & Opportunities

| Module | Spec | Notes |
|---|---|---|
| `job` | [spec](../sc-saas-backend/src/modules/job/module.spec.md) | Job board + applications. `@Roles(JOB_SEEKER)` applied but `RolesGuard` missing from `@UseGuards` — role check silent no-op. `PATCH hiring-profile` body is commented out (no-op). |
| `startup-kit` | [spec](../sc-saas-backend/src/modules/startup-kit/module.spec.md) | Curated startup resource catalogue. Browse is unauthenticated. In-memory cache with 10-hour TTL — edits invisible until restart. |
| `ip-management` | [spec](../sc-saas-backend/src/modules/ip-management/module.spec.md) | Intellectual property tracking (cockpit proxy). Shared mutable `requestHeader` concurrency bug (same as ecosystem). |

---

## Facilities & Physical

| Module | Spec | Notes |
|---|---|---|
| `facility_management` | [spec](../sc-saas-backend/src/modules/facility_management/module.spec.md) | Facility booking + kiosk check-in (5 controllers, 30+ routes). Inconsistent auth — some write paths accept unauthenticated callers. `PaymentTransactionsEntity` registered twice. |

---

## Tasks & Projects

| Module | Spec | Notes |
|---|---|---|
| `task-management` | [spec](../sc-saas-backend/src/modules/task-management/module.spec.md) | **Empty stub.** Controller and service are unimplemented. Entities scaffolded (`tasks`, subtasks, comments, attachments). Missing `@Controller` version → routes would land at `api/task-management` not `api/v1/`. |
| `milestones` | [spec](../sc-saas-backend/src/modules/milestones/module.spec.md) | Program milestone tracking. Ownership checks commented out — any authed user can mutate any milestone. `formatMileStoneInformation` does a DB write on every read call. |

---

## Public Portal (external website)

| Module | Spec | Notes |
|---|---|---|
| `public-portal` | [spec](../sc-saas-backend/src/modules/public-portal/module.spec.md) | **New this pass.** Read-mostly public API for an external, unauthenticated website (Quicklinks, Contacts, Events, Incubation Centers, Mentors, Startups, Registration/Recognition summaries + admin "flag for clarification" writes). Gated by `PublicPortalApiKeyGuard` (DB-stored key, fails closed) — no `Feature` flag involved at all. `buildAttachmentUrl()` (new) makes every image/attachment field a complete, ready-to-embed URL since the external site has no access to this app's own bootstrap endpoint. |

---

## Platform Infrastructure

| Module | Spec | Notes |
|---|---|---|
| `global` | [spec](../sc-saas-backend/src/modules/global/module.spec.md) | Platform backbone: reference data, tenant settings, admin actions (85+ routes). `backdoor-login` issues real JWTs with only an md5 token. `forgot-password` has no token at all. Exports `GlobalService` + `AdminActionsService`. |
| `audit-log` | [spec](../sc-saas-backend/src/modules/audit-log/module.spec.md) | `@Global()` write-only auditing. Exports `AuditedUpdateService`. Raw `repo.update()` calls bypass the audit trail. |
| `cron` | [spec](../sc-saas-backend/src/modules/cron/module.spec.md) | Scheduled job orchestration. `COMMUNITY_WALL_POSTS_WEEKLY_REMINDER` callback is missing `()` — no-op. Timezone hardcoded to `Asia/Kolkata`. |
| `notifications` | [spec](../sc-saas-backend/src/modules/notifications/module.spec.md) | *(also listed under Events & Community)* Exports `NotificationsRepository` write methods for sibling modules (job applications, application status, event reminders, connection-request actioned). |
| `migrations` | [spec](../sc-saas-backend/src/modules/migrations/module.spec.md) | Data migration scripts behind `:adminMd5` token. **No JWT, no feature gate** — only the md5 token protects bulk mutations. |
| `import` | [spec](../sc-saas-backend/src/modules/import/module.spec.md) | Bulk profile seeding. **5 routes with zero auth or feature gate** — open to anyone with network access. |

---

## Integrations & External

| Module | Spec | Notes |
|---|---|---|
| `factacy` | [spec](../sc-saas-backend/src/modules/factacy/module.spec.md) | Proxies Factacy AI-news API. Errors swallowed silently (returns HTTP 200 with `data: undefined`). |
| `power-pitch-module` | [spec](../sc-saas-backend/src/modules/power-pitch-module/module.spec.md) | Power Pitch video platform bridge. CFA + transcript routes have no JWT. |
| `zoho` (`core/`) | [spec](../sc-saas-backend/src/core/zoho/module.spec.md) | One-way outbound sync of stakeholders + mentorship/meeting/startup-kit-submission activity into Zoho CRM (Leads→Accounts/Contacts, "Connects" custom module). **All 6 routes have zero guards** — no `@UseGuards`/`@Roles`/`@Features` anywhere in the controller; corrects a prior "5 routes" count (it's 6 — `update-meeting-data` was previously missed). `updateStakeholdersAccounts()`'s `INVESTOR` branch has a dead early `return` — investor account syncs are a silent no-op. |

---

## Core Infrastructure (cross-cutting, `src/core/`)

Most of `core/` is deliberately un-specced infra (config, guards, entities, decorators, utils, etc.). These two subdirectories are real bounded contexts and have their own `module.spec.md`.

| Module | Spec | Notes |
|---|---|---|
| `upload-module` (`core/`) | [spec](../sc-saas-backend/src/core/upload-module/module.spec.md) | Shared internal provider (no controller) centralising all S3 file I/O (`AmazonS3Service`, `UploadService`) plus an HTML→PDF renderer (`PdfRenderHtmlService`) used for invoice generation. Consumed by ~25 feature modules — the one shared upload path for the whole backend. New this pass: `getBase64DataUri()`/`getObjectAsBase64DataUri()` — returns S3 object bytes as a data URI (no origin) so client-side `<canvas>` export can't be CORS-tainted; used by `startup`'s Digital ID Card. Content-type derivation is inconsistent: fixed maps for documents/images but raw-extension-derived for video, despite an in-file comment saying that's unsafe. |
| `sockets` (`core/`) | [spec](../sc-saas-backend/src/core/sockets/module.spec.md) | Single Socket.IO gateway (`FetchCountGateway`) — the only real-time push channel (unread counts, typing indicators, presence, connection/chat notifications). **No auth guard of any kind** on the WS gateway; rooms are named by raw numeric user id with no membership check, so a guessed/enumerated room id can receive another user's `fetch-count`/notification events. Presence map is in-process only (no Redis) — inconsistent across multi-instance deployments. |

---

## Stubs / Data-Model Only

| Module | Spec | Notes |
|---|---|---|
| `portfolio-management` | [spec](../sc-saas-backend/src/modules/portfolio-management/module.spec.md) | 8 entities, zero controller/service. Schema consumed by PHP admin via direct DB. Three `date` columns typed `number` in TS. |
| `grants` | *(see Finance above)* | |
| `schemes-management` | *(see Finance above)* | |
| `task-management` | *(see Tasks above)* | |

---

## Security findings summary (surfaced by spec authoring)

These findings were captured in module `Watch out for` sections. They are **not fixed here** — they are documented for awareness and prioritisation.

| Severity | Module | Finding |
|---|---|---|
| 🔴 Critical | `verifications` | OTP stored as md5 but compared against plaintext — verification always fails |
| 🔴 Critical | `global` | `backdoor-login` issues real JWTs with only an md5 token; `forgot-password` has no token |
| 🔴 Critical | `import` | 5 bulk-import endpoints have zero auth or feature gate |
| 🔴 Critical | `payment-management` | Nearly every payment route has `JwtAuthGuard` commented out |
| 🔴 Critical | `milestones` | Ownership checks commented out — any authed user can mutate any milestone |
| 🟠 High | `migrations` | All mutation routes protected only by md5 token, no JWT |
| 🟠 High | `news` | All 4 routes have JWT commented out; preference write has no ownership check |
| 🟠 High | `learning-management` | `GET videos/:id/hls-url` fully unprotected — leaks signed CloudFront HLS URLs |
| 🟠 High | `memberships` | Majority of routes have JWT commented out; any caller can submit upgrade for any profile |
| 🟠 High | `elastic-search` | All 20 routes unauthenticated — only a feature flag gates index/search operations |
| 🟠 High | `partner` | `premium-module/request` is open and can trigger SES to arbitrary addresses |
| 🟠 High | `user` | `update/notification` and `profile-views/increment` are unauthenticated |
| 🟠 High | `auth-external` | `default` branch passes `undefined` as userId → crash on unsupported user types |
| 🟠 High | `zoho` (`core/`) | All 6 CRM-sync routes have zero auth guards — anyone reachable can trigger a full Zoho push/sync pass |
| 🟡 Medium | `sockets` (`core/`) | WS gateway has no auth guard; rooms keyed by raw user id let a guessed id receive another user's notifications |
| 🟡 Medium | `cron` | `COMMUNITY_WALL_POSTS_WEEKLY_REMINDER` callback missing `()` — scheduled job is a no-op |
| 🟡 Medium | `job` | `@Roles(JOB_SEEKER)` applied but `RolesGuard` missing from `@UseGuards` — role check ignored |
| 🟡 Medium | `notifications` | 6 cron-trigger POST endpoints are completely open |
| 🟡 Medium | `meetings` | `feedback-reminder/trigger` and `/:code/complete` are unauthenticated |
| 🟡 Medium | `vs-programs-management` | `getProgram` creates a DB row on every read call |
| 🟡 Medium | `program-management` | `payment-reminder/:adminMd5` admin-check commented out |

---

## Feature specs and Gap Register

Cross-repo features are specified in `specs/features/` (the workspace layer), not in module specs. The notification-centre family:

- [SAN-1381 Notifications and an Action-Driven Dashboard](features/SAN-1381-notifications-action-driven-dashboard.spec.md) (formerly NOTIF-001). Phase 1; includes the performance measurements and BRD sign-off.
- Phase 2 specs:
  - [SAN-1471 application status updates](features/SAN-1471-application-status-updates.spec.md)
  - [SAN-1472 event reminders](features/SAN-1472-event-reminders.spec.md)
  - [SAN-1475 escalation rules](features/SAN-1475-escalation-rules.spec.md)
  - [SAN-1478 in-app preferences](features/SAN-1478-notification-preferences-in-app.spec.md)
  - [SAN-1481 recommended for you](features/SAN-1481-recommended-for-you.spec.md)
- [BRD §4 baseline queries](features/SAN-1381-baseline-queries.md)

Known gaps (deferred, unverified or risky items) are tracked in the **[Gap Register](gap-register.md)**.
