# SanchiSaaS — Module Map (Cross-Repo Reference)

> **The module inventory and the dependency diagram are now generated** from the module specs in [`docs/MODULE-MAP.md`](../docs/MODULE-MAP.md) (SAN-1627) and are kept current there. This hand-written page stays for what the generator can't derive: the per-module narrative and the roles-and-access tables. Where the two disagree, the generated page reflects the specs.

**Document type:** Internal architecture reference.
**Last updated:** 2026-07-21 (roles & access verified directly against code on this date).

**Companion documents:** `CLAUDE.md` (blast-radius graph + 6 cross-repo invariants) · `specs/SanchiSaaS-Repo-Map.md` (repo-level purpose / owns / depends-on) · each repo's own `specs/<repo>-module-specs-index.md` (full detail + security findings per module). This document *summarizes and cross-links* those indexes; it does not replace them.

**Purpose:** Answer four questions in one place — (1) what stack does each repo run, (2) what does every module in every repo actually do, (3) which modules, specifically, talk to which modules in other repos and how, and (4) who — which user/role — can actually access each repo and each piece of functionality in it.

---

## Part A — How the seven repos connect

```mermaid
graph TD
    T["sanchiconnect-saas-tenants<br/>cockpit / control plane<br/>(highest blast radius)"]
    F["sc-saas-frontend<br/>end-user PWA"]
    B["sc-saas-backend<br/>business API"]
    A["sc-saas-admin<br/>accelerator staff panel"]
    W["sc-saas-3rdparty-webservices<br/>integration gateway"]
    AN["ai-startups-analyzer<br/>AI scoring service"]
    TA["sanchiconnect-saas-tenants-admin<br/>platform operator UI"]
    PP["power-pitch-sanchiconnect-api<br/>(external — SanchiPowerpitch)"]

    T -->|verify_tenant / tenant-settings| F
    T -->|bootstrap config| B
    F -->|business calls via apiUrl| B
    B -->|SMS / email / video / chat / docs| W
    A -->|api_server_url REST| B
    A -.->|reads tenant DB directly| T
    A -->|score runs, HTTP| AN
    TA -.->|reads + writes tenants DB directly| T
    TA -->|unconditional PATCH on every tenant edit| B
    B -->|x-hostname + JWT| PP
```

Solid edges are live runtime calls. `tenants ↔ tenants-admin` and `admin → tenants` are **direct shared-database reads/writes, bypassing any API** — a schema change on either side can break the other with no compile-time warning. See `CLAUDE.md`'s full blast-radius graph and 6 invariants for the authoritative version of this diagram; the rest of this document works one level below it, at module granularity.

---

## Part B — Per-repo stack & module inventory

### 1. `sanchiconnect-saas-tenants` — Control plane / cockpit

**Stack:** NestJS 9 · TypeORM 0.3 · MySQL (single shared DB, row-per-tenant) · npm · Node 16+
**Role:** Source of truth for feature-flag names and tenant/workspace provisioning. Highest blast radius in the workspace — a change here can reach `frontend`, `admin`, and (via `backend`) everything backend touches, plus `tenants-admin` via direct shared-DB access.

| Module | Purpose / Goal / Description |
|---|---|
| `core` (bootstrap) | NestJS bootstrap (helmet, CORS, Swagger), env validation, TypeORM factory, `TransformInterceptor`, `@ClientDomainHeader`, global exception filter. |
| `tenants` | `TenantUsersEntity` — 218 boolean columns (217 genuine feature flags plus one status field, `active`), code-verified 2026-07-21; the cross-repo contract source of truth for every feature flag in the platform; also `TenantMaintenanceEntity`. |
| `global` | Entry point / pre-auth bootstrap surface every other repo calls before a JWT exists. All 5 routes — including `verify_tenant` and `tenant-settings` — are confirmed unauthenticated. |
| `global` → `global-verification` | `verify_tenant/:hostname` + `tenant-settings/:hostname` — the frozen tenant-verification contract; frontend and backend both bootstrap from this. |
| `global` → `global-system` | Currency exchange rates, system messages, program-promotion + tracking endpoints, SaaS leads, global settings. |
| `global` → `global-admin` | 22 `spa_*` TypeORM entities — schema definitions for admin-panel config tables; NestJS owns the schema, PHP (`tenants-admin`) writes the rows directly. |
| `organizations` | Billing org entity — invoices, payments, contacts, contracts. Only `name` is non-nullable; `tenant_users.organization_id` requires a pre-existing row here before a tenant can be provisioned. |
| `subscriptions` | Subscription lifecycle — links an organization to a plan; expiry has tenant-access implications. |
| `ai-credits` | Prepaid AI-credit wallet/ledger schema. Implements only the purchase path (catalog, Easebuzz order + webhook, GST invoicing) — one of three independent writers to the shared `ai_credit_*` tables (see Part C, thread 6). |
| `ecosystem` | Multi-tenant profile directory — 8 entity types (startups, investors, mentors, corporates, partners, service providers, individuals, program-office members), populated by best-effort sync from per-tenant backends. |
| `ip-management` | Patents + IP-connect requests (IP hub); facility bookings (facility hub). PHP admin panels write directly to these tables. |
| `ecosystem-facilities` | Facility directory (list/detail/types) — GET-only public endpoints, domain-scoped, no auth guard. |

### 2. `sc-saas-backend` — Business API

**Stack:** NestJS 8 · TypeORM · MySQL · one deployment per tenant (bootstrap config loaded from `tenants` at startup)
**Role:** Owns the API contract every client consumes — controllers + class-validator DTOs under `api/v{n}`. 58 modules under `src/modules/` plus 3 bounded-context directories under `src/core/`.

| Module | Purpose / Goal / Description |
|---|---|
| `auth` | JWT issuance, OTP login, per-type registration — the auth contract every other module depends on. |
| `auth-external` | Cross-tenant user import/export flow. No JWT on any route — OTP + feature flags only. |
| `user` | Profile CRUD for all stakeholder types; widest-dependency module (11 imports). |
| `verifications` | OTP send/verify. |
| `application-management` | Form submission, review, and scoring pipeline for programs/CFAs. |
| `form-management` | Dynamic form builder and renderer. |
| `program-management` | Incubator program CRUD + payment reminders. |
| `program-office-members` | POM stakeholder lifecycle + ecosystem sync. |
| `vs-programs-management` | Venture Studio program rounds. |
| `startup` | Largest module (46 routes, 6 controllers) — pitch deck, founders, funding, advisory board. |
| `individual` | Individual stakeholder profile. |
| `investor` | Investor profile and portfolio. |
| `corporate` | Corporate stakeholder profile. |
| `mentors` | Mentor profile + application management. |
| `partner` | Partner lifecycle + startup onboarding. |
| `service-providers` | Service provider profile. |
| `ecosystem` | Proxies search/profiles to the `tenants` cockpit directory. |
| `search` | Stakeholder typeahead across 9 types. |
| `elastic-search` | Elasticsearch index sync (20 routes). |
| `compare` | Side-by-side stakeholder comparison. |
| `connections` | Connection requests between stakeholders. |
| `connections-wishlist` | Saved / wishlist connections. |
| `events` | Event creation, registration, and attendance. |
| `community-wall` | Social feed / wall posts. |
| `challenges` | Innovation challenge lifecycle. |
| `news` | External news proxy + per-user category prefs. |
| `notifications` | Inbox + badge-count aggregator; exports `NotificationsRepository` write methods for sibling modules. |
| `mentorship` | Mentorship session booking + hour logging. |
| `learning-management` | LMS — courses, modules, videos. |
| `certificates` | Certificate generation and issuance. |
| `id-cards` | Digital ID card generation. |
| `payment-management` | Multi-gateway hub — PayPal, Razorpay, Stripe, Easebuzz, PayU. |
| `memberships` | Membership tiers + upgrade requests. |
| `invoice` | PDF invoice generation → S3 upload. |
| `grants` | Entity stub only (no controller/service) — schema for the admin panel. |
| `schemes-management` | Empty controller stub — entities scaffolded for the admin panel. |
| `meetings` | Meeting scheduling + video integration. |
| `chat` | CometChat integration and messaging. |
| `conversations` | Threaded conversation management. |
| `tickets` | Support ticket system — same tables the frontend `tickets` module and admin `tickets` module both work with. |
| `resources` | Resource library + download tracking — served to admin's `resource-files` authoring UI and frontend's `resources` display. |
| `glossary` | Term dictionary — backend counterpart to frontend `glossary` and admin `glossary`. |
| `dashboard` | Analytics dashboard aggregation. |
| `metrics` | Custom chart metrics. |
| `job` | Job board + applications. |
| `startup-kit` | Curated startup resource catalogue. |
| `ip-management` | Intellectual property tracking — cockpit (`tenants`) proxy. |
| `facility_management` | Facility booking + kiosk check-in (5 controllers, 30+ routes). |
| `task-management` | Empty stub — controller/service unimplemented; entities scaffolded. |
| `milestones` | Program milestone tracking. |
| `global` | Platform backbone — reference data, tenant settings, admin actions (85+ routes). Exports `GlobalService` + `AdminActionsService`. |
| `audit-log` | `@Global()` write-only auditing; exports `AuditedUpdateService`. |
| `cron` | Scheduled job orchestration. |
| `migrations` | Data migration scripts behind an `:adminMd5` token. |
| `import` | Bulk profile seeding. |
| `factacy` | Proxies the Factacy AI-news API. |
| `power-pitch-module` | Bridge to the Power Pitch video platform — the one confirmed cross-workspace contract (see Part C, thread 11). |
| `zoho` (`core/`) | One-way outbound sync of stakeholders + activity into Zoho CRM — independent of, and unrelated to, `sc-saas-admin`'s own `zoho` module (see Part C, thread 10). |
| `upload-module` (`core/`) | Shared internal provider centralizing all S3 file I/O plus an HTML→PDF renderer, consumed by ~25 feature modules. |
| `sockets` (`core/`) | Single Socket.IO gateway — the only real-time push channel (unread counts, typing indicators, presence). |
| `portfolio-management` | 8 entities, zero controller/service — schema consumed by the PHP admin via direct DB access. |

### 3. `sc-saas-frontend` — End-user PWA

**Stack:** Angular 13 · NgRx · PWA
**Role:** The product surface startups, mentors, investors, and every other stakeholder type actually use. Pure consumer — owns nothing cross-repo. 82 module directories under `src/app/modules/` (several are "umbrella" specs covering sibling directories together — noted below).

| Module | Purpose / Goal / Description |
|---|---|
| `auth` | Every entry point into/out of the platform — OTP login, registration variants, email verification, admin-backdoor mount. |
| `admin-actions` | "Backdoor login" impersonation tool (`/backdoor-login/:id/:uuid`). |
| `connection-request-action-email` | Generic "magic link" landing page for 8 different email-notification action types. |
| `connection-approve-reject-page` | Public, token-less accept/reject landing page from an email link. |
| `account` | Generic "Account Settings" area reused across every stakeholder type. |
| `team` | Generic team-member roster ("sub-accounts"), deep-linked from 5+ places. |
| `individuals` / `individual-profile` | Self-service portal for the INDIVIDUAL account type. |
| `startups` | Full startup self-service portal — profile lifecycle, pitch-deck variants, dashboard, compare tool. |
| `investors` | Investor self-service portal (org + individual variants). |
| `corporate` | Corporate user self-service portal. |
| `mentors` | Mentor self-service portal + mentorship-hours tracker. |
| `partners` / `partners-dashboard` / `partners-details` | Public partner directory, authenticated partner hub, public partner-profile page. |
| `service-provider` | Service-provider self-service portal, gated by the `service_providers` flag. |
| `program-office` / `program-office-team` | Self-service portal + standalone team page for the "program office" account type. |
| `hire` / `job-search` / `job-details` / `job-public-details` / `job-interview` / `applied-jobs` | Full job-board domain — post/manage (employer), search/apply/track (seeker), live interview room. |
| `challenges` / `challenge-details` / `challenge-search` / `challenge-public-details` / `challenge-public-view` / `challenge-collection` | Full innovation-challenge lifecycle — corporate create/manage, startup discover/apply/track. |
| `programs` / `vs-programs` / `call-for-applications` | Three parallel program-application tracks, unified into one applicant-facing surface. |
| `dynamic-forms` / `static-form-field` | Dynamic-form rendering engine for admin-configured forms; consumed by ~15 other modules. |
| `event-agenda` / `public-events` / `webinars` | Authenticated event agenda, public event registration, YouTube webinar catalog. |
| `meetings` / `calender` | In-meeting VideoSDK experience + "My Meetings" scheduling hub. |
| `chat` | In-app messaging — CometChat SDK or in-house REST+socket chat, selected by the `chat_type` setting. |
| `community-feed` | Member-facing social feed + notification inbox, real-time over Socket.IO. |
| `notifications` | Notification feed + navbar badge count. |
| `connection-v4` / `connections-v3` | Current active-connections experience. |
| `search` / `global-search-page` | Paginated search across 9 stakeholder types + a global search page. |
| `ip-search` / `ip-request` | Cross-tenant "IP Hub" patent browse/search + connection-request inbox. |
| `resources` / `glossary` / `deeptech-news` / `product-updates` / `resource-reports` / `startup-kit` / `market-insights` | Five read-heavy content sections plus a static PowerBI embed shell. |
| `learning-management` | Course catalogue, enrollment, HLS video playback, quizzes. |
| `dashboard-v2` / `growth-matrics` / `growth-matrics-print` | Role-aware home dashboard + KPI submission/reporting + print/export view. |
| `payment` / `payment-gateways` (dead) / `membership` | Gateway checkout, coupons, order history, membership plan-picker. |
| `facilities-management` / `external-facilities-management` | Bookable-space lifecycle + cross-tenant ecosystem facility catalogue. |
| `milestones` / `tickets` / `tracker` | Startup goal tracking, support tickets, mentor-hours logging. |
| `pitch-deck-management` / `pitch-deck-recorder` (dead) | Pitch-video management across PowerPitch/Loom/raw-upload modes. |
| `cerificates` / `sc-certificate-renderer` / `sc-id-card-renderer` | Public certificate verification + certificate/ID-card visual rendering. *(Module name `cerificates` is the real, misspelled directory.)* |
| `ad-viewer` | Dumb presentational banner-ad component — frontend consumer of admin's `ads-management`. |
| `share-links` / `slider` / `inline-styles-csp` / `public-shared` / `page-not-found` | Shared component libraries and the 404 page — no routes of their own. |
| `public` (dead) / `payment-gateways` (dead) | Confirmed unreachable — repurposed as component libraries or fully orphaned. |
| `core` (infra) | `HttpInterceptorModule`, `ServiceModule`, `StateModule` (38 NgRx effects) — the app's service/state backbone; resolves `apiUrl` from the `tenants` bootstrap. |
| `shared` (infra) | Cross-cutting presentation/utility components. |

### 4. `sc-saas-admin` — Accelerator staff panel

**Stack:** PHP · Medoo · sparkAdminTpl · jQuery/Bootstrap · two DB connections per request — `$mainDatabase` (tenants DB: flags, `api_url`, per-tenant DB creds) and `$database` (per-tenant client DB: all business data)
**Role:** Admin panel used by accelerator/incubator staff (not platform operators) — applications, cohorts, broadcasts, bulk actions, AI-scoring orchestration. 68 of 68 module directories spec'd.

| Module | Purpose / Goal / Description |
|---|---|
| `core-bootstrap` | Dual-DB connection setup, tenancy resolution, router, template engine, feature-flag loading. |
| `auth` | Admin login, session, SSO (Microsoft/Azure), password reset, profile. |
| `ajax` | 7 jQuery AJAX endpoints: `api_actions`, `crud_actions`, `email_actions`, `spa_actions`, `whatsapp_actions`, `stakeholder_export`, `fields_mapping`. |
| `stakeholder-crud` | Generic CRUD engine (`table.php` / `add.php` / `edit.php`) for all entity types, driven by `spa_data_management`. |
| `application_management` | Full CFA lifecycle — program wizard, round management, submission review, jury evaluation, approve/reject. Triggers score runs on `ai-startups-analyzer`. |
| `program-management` | PM/corporate-PM dashboards + program creation wizard. |
| `jury` | Jury assignment, per-round scoring dashboards. |
| `challenges` | Corporate challenge creation, participant management. |
| `venture-studio` | VS program management — individuals apply, admins form teams. |
| `startup-application-management-flow` | Kanban/table/reports view for a program's applications; bulk email; round moves via backend `:adminMd5` API. |
| `stakeholder-detail-pages` | Startup/application/PM/mentor/investor detail views, incl. ID-card auto-gen on approval. |
| `learning_management` | LMS course + enrollment management (admin side of the frontend/backend LMS trio). |
| `events` | Admin management of the generic multi-format events table. |
| `meetings` | Admin view of peer-to-peer 1:1 meetings — calls the 3rdparty gateway directly, bypassing backend, for VideoSDK session lookups. |
| `community_wall` | Moderation + admin-authored posting for the member social feed. |
| `connections` | Admin-side connection moderation — user + global connection matrices. |
| `memberships` | Membership lifecycle across all stakeholder types. |
| `finance_management` | Orders, payments, proforma invoices, coupons, tax + gateway settings. |
| `payment_gateways` | Gateway enable/disable with live credential validation. |
| `tax_management` | Tax profile CRUD (GST/VAT rates). |
| `ai_credits` | Admin-facing AI-credits wallet/buy/history/orders/invoice UI — one of three independent writers to the shared `ai_credit_*` tables (see Part C, thread 6). Reserve/settle/refund spend logic lives here, called from `application_management`. |
| `broadcast_messages` | Compose + send audience-filtered broadcasts (email/chat/community-wall). |
| `canned_responses` | Reusable email templates for the broadcast composer. |
| `outreach_requests` | Cross-tenant/cross-partner program-promotion request system — `program_promotions` lives in the shared tenants DB, connecting to `tenants`' global-system module. |
| `contacts` | Generic category-tagged personal/organizational rolodex. |
| `news` | Curated external "deeptech news" feed. |
| `glossary` | Term/definition dictionary — authoring side; frontend `glossary` is the display side, both via backend `glossary`. |
| `resource-files` | Live tenant-facing resource library — real cross-repo feature served by backend's `resources` module. |
| `video_gallery` | YouTube-embed-only video showcase. |
| `industry_reports` | Downloadable report content items. |
| `product_updates` | Changelog/release-notes feed. |
| `ads-management` | In-app promotional banner CRUD — authoring side of frontend's `ad-viewer`. |
| `startup-booster-kit` | Vendor/partner service-offer catalog. |
| `certificates` / `certificate_builders` / `id_card_builders` / `id_cards` | Certificate + ID-card template design and issuance — authoring side of the frontend renderer trio. |
| `metric_types` / `growth_metrics` / `milestones` / `tickets` / `portfolio_management` / `reporting` | KPI catalogue, KPI reporting/dashboards, milestone viewer, ticket lifecycle, cap-table tracking, custom BI dashboards. |
| `facilities` | Physical space booking — soft-delete writes to both tenants and client DB (connects to `tenants`' `ecosystem-facilities` / `ip-management`). |
| `partners` / `recruitment-partners` | Partner (tenant sub-admin) self-service portal + recruiter-facing job pipeline view. |
| `form-management` / `form_builder` / `document_types` / `csv` | Program application-form builder, standalone data-collection forms, document-category registry, generic CSV import/export. |
| `zoho` | Zoho CRM connector — OAuth connect, field mapping — independent of, and unrelated to, backend's own `zoho` module (see Part C, thread 10). |
| `aws` | Raw S3 bucket manager. |
| `filemanager` | Local-disk file browser (dead/unfinished — list template missing). |
| `scrapper` | Capboard/IESA external scrapers, plus a `list.php` that reads every tenant's DB directly. Not the same thing as `tenants-admin`'s `modules/scrapper.php` despite the identical name (see Part C, thread 13). |
| `intellectual_property` | Patent/copyright/trademark register — writes directly to the shared tenants DB (`patents` table, connecting to `tenants`' `ip-management`). |
| `upload` | TinyMCE rich-editor inline image upload endpoint. |
| `developer` | Super-admin config cockpit — DDL, email/WhatsApp config, menu management, form-field/table-view mapping, settings management. |
| `system_logs` / `profile_audit_logs` / `task_management` | Read-only op logs viewer, profile-change history viewer, internal ops ticketing tool. |

### 5. `ai-startups-analyzer` — AI scoring service

**Stack:** Python 3.10+ · FastAPI · SQLAlchemy (async) · MySQL (own DB) · OpenAI/Anthropic/Gemini via `DEFAULT_PROVIDER`
**Role:** LLM-based startup application scoring. Leaf node — called only by `sc-saas-admin`, never calls back; admin polls for results.

| Module | Purpose / Goal / Description |
|---|---|
| `core-bootstrap` | FastAPI app setup, lifespan (DB init + task cleanup), `status.json`, async pool, auto-migration (`_sync_missing_columns()`), CORS. |
| `data-models` | 17 Pydantic DTOs + 3 SQLAlchemy ORM models (`Analysis`, `Batch`, `APIKey`). |
| `scoring-engine` | All 19 API endpoints; batch orchestration; `_coerce_rating` (0–500 → 1–5, the frozen cross-repo scoring contract); weighted-criteria mode; fallback scoring. |
| `ai-provider` | Provider facade (`DEFAULT_PROVIDER` switch); per-provider JSON-forcing; token extraction; USD cost computation. |
| `enrichment` | Serper.dev search + Firecrawl scrape — best-effort, never blocks scoring; disabled by default. |

### 6. `sc-saas-3rdparty-webservices` — Integration gateway

**Stack:** NestJS 9 · TypeScript · stateless (no DB, no tenant context)
**Role:** Centralizes every third-party API call in one place. Leaf node — called only by `sc-saas-backend` (plus one documented direct call from `sc-saas-admin`'s `meetings` module).

| Module | Purpose / Goal / Description | Backend caller |
|---|---|---|
| `sms` | OTP delivery via Auth.key.io | `core/services/sms.service.ts` |
| `sendGrid` | Email delivery via SendGrid | `core/services/ses-email.service.ts` |
| `ses` | Email delivery via AWS SES | `core/services/ses-email.service.ts` |
| `cometChat` | Chat — users, friends, blocked-users, messages, groups | `core/services/comet-chat.service.ts` |
| `videoSDK` | Video meetings — create/fetch/sessions | `core/services/video-sdk.service.ts` |
| `shortIo` | Short URLs / action links (accept/reject connection requests) | `core/services/url.service.ts` |
| `convertKit` | Document conversion — PPT→PNG (pitch decks) | `core/services/convertapi.service.ts` |

### 7. `sanchiconnect-saas-tenants-admin` — Platform operator UI

**Stack:** PHP ≥5.5 · Composer · Medoo · sparkAdminTpl (QUCod) · one DB connection — the shared tenants MySQL DB (same DB `sanchiconnect-saas-tenants` owns)
**Role:** Used by Sanchi's own platform-operator staff (not tenant/accelerator staff) to provision tenants, manage roles, and administer global cockpit data. Distinct from, and unrelated to, `sc-saas-admin` despite the similar name. 9 of 9 module directories spec'd.

| Module | Purpose / Goal / Description |
|---|---|
| `core` (root-level) | `index.php` routing, `config/`, `core/db.php` + `session.php`, `includes/core_functions.php`, and the generic `add.php` / `edit.php` / `table.php` / `detail.php` engine over the tenants DB. |
| `ajax` | 5 JSON AJAX handlers — `crud_actions.php` (table/column DDL), `spa_actions.php` (`spa_*` config CRUD). |
| `auth` | Login, session-based RBAC, operator profile, admin/role/partner account CRUD — notifies `sc-saas-backend` on new-admin creation. |
| `developer` | Platform config tools — API route registry, email/settings/menu/form-field/form-layout/table-view management, per-tenant data export. |
| `ai_credits` | Operator screens for the AI-credits commercial catalogue — packages, per-task rates, one-off tenant grants, cross-tenant read-only orders view. One of three independent writers to the shared `ai_credit_*` tables (see Part C, thread 6). |
| `finance_management` | The platform's own billing of tenants for AI-credits purchases — GST/VAT tax profiles, invoice supplier settings, read-only invoice register. Not related to `sc-saas-admin`'s member-facing `finance_management`. |
| `aws` | Raw S3 bucket manager ("Files Storage" screen). |
| `filemanager` | Local-disk file browser over the admin server's own filesystem. |
| `csv` | Generic table-driven CSV export/import for the dynamic CRUD engine — any table, by name. |
| `upload` | TinyMCE rich-text image-upload endpoint. |
| `modules/scrapper.php` (standalone file, not a subdirectory) | Reads across every tenant's DB directly for platform-level reporting — unrelated in purpose to `sc-saas-admin`'s own `scrapper` module of the same name (see Part C, thread 13). |

---

## Part C — Cross-repo module connections

This is the synthesis the per-repo indexes don't show on their own: which specific module in one repo talks to which specific module in another, and by what mechanism.

### 1. Feature flags — the platform's most-propagated contract

`tenants` → `tenants` module (`TenantUsersEntity` boolean columns, **218 of them** — 217 genuine feature flags plus one status field, `active`) is the single source of truth. Consumers: `backend`'s `Feature` enum + `feature-guard.ts` (`core/constants/enum.ts`) · `frontend`'s `IFeatures` (`core/domain/brand.model.ts`) · `admin`'s `config.php` constants. A column rename must propagate to all three simultaneously, or a flag silently stops gating in one client while still gating in another.

> **Flag count — resolved (code-verified 2026-07-21).** `TenantUsersEntity` has **218** boolean columns: **217 genuine feature flags** plus one generic status field (`active`). A raw `grep -cE ':\s*boolean'` returns 219; one property, `startup_to_mentor_connection_questions`, is typed `boolean` in TypeScript but is actually a `text` column, so it is excluded. This supersedes the earlier "150+", "~180", and "~218" figures across the docs.
>
> **Backend enforcement gap.** Only **78** of these flags have a member in `sc-saas-backend`'s `Feature` enum (`core/constants/enum.ts`), and just 74 of those match a real column — so roughly **143 of the 217 flags have no backend gate** via `@Features(...) + FeatureGuard` today. Four enum values (`connections_wishlist`, `news`, `payment_gateways`, `tax_profile`) have no matching column at all. This may be intentional (frontend/admin-only toggles with no backend-enforced behavior), or a real coverage gap; it is worth a follow-up pass for any flag expected to gate backend behavior.

### 2. Tenant verification / bootstrap

`tenants` → `global` / `global-verification` module (`verify_tenant/:hostname`, `tenant-settings/:hostname`) is called by:

- `backend`'s core-bootstrap, at process startup, to load per-tenant config (DB creds, `api_url`, secrets).
- `frontend`'s core module (`GlobalService`, `brand.model.ts`) to resolve `apiUrl` before any business call.

One-directional, `tenants` upstream of both. Confirmed unauthenticated on the `tenants` side — anyone who can reach it and knows a hostname gets the same plaintext secrets both consumers receive.

### 3. Business API contract

`backend`'s ~58 `src/modules/*` controllers/DTOs (`api/v{n}`) are consumed by:

- `frontend`'s `core/service/*` layer, via the `apiUrl` resolved in thread 2.
- `admin`, via `api_server_url` cURL calls scattered across most modules.
- `tenants-admin`, via two specific, direct, unconditional calls: `modules/edit.php` → `PATCH .../saas/settings` (`resetAPISaaSSettings()`, fires on every `tenant_users` edit) and `modules/auth/admins.php` → `admin-account-created/:token` (conditional, on new-admin creation).

### 4. Third-party integration gateway

`backend`'s `core/services/*.service.ts` files call `sc-saas-3rdparty-webservices` modules 1:1 — see the table in Part B §6. Consuming backend feature modules: `auth` / `verifications` (sms), most notification-sending modules (sendGrid/ses), `chat` / `conversations` (cometChat), `meetings` (videoSDK), connection-request flows across many modules (shortIo), `startup` / pitch-deck flows (convertKit). Documented exception: `admin`'s `meetings` module calls the 3rdparty gateway directly for VideoSDK session lookups, bypassing backend entirely — the only confirmed non-backend caller of that service.

### 5. AI scoring pipeline

`admin`'s `application_management` / `jury` modules → HTTP → `ai-startups-analyzer`'s `scoring-engine`. Analyzer never calls back; admin polls for results. The 0–500 → 1–5 scale (`_coerce_rating` in the analyzer, `decimal(4,3)` column in the backend schema consumed by admin) is a frozen contract — changing it on one side without the other silently corrupts scores.

### 6. AI Credits — three independent, non-synchronized writers

The same `ai_credit_*` tables in the shared tenants DB are written by three separate modules with no shared validation layer:

- `tenants` → `ai-credits` module — purchase path only (catalog, Easebuzz order + webhook, invoicing).
- `admin` → `ai_credits` module — wallet/buy/history UI (calls `tenants`' `v1/ai-credits/purchase`); reserve/settle/refund spend-side logic lives in `includes/ai_credits_functions.php`, invoked from `application_management`.
- `tenants-admin` → `ai_credits` module — operator-side catalogue management (packages, task-rates, grants) + a cross-tenant, read-only orders view.

See `specs/features/FT-005-ai-credits-system.spec.md` for the full architecture and the risk this fragmentation creates.

### 7. Shared tenants DB — direct access, no API

- `tenants-admin` — the entire application reads/writes `tenant_users`, `organizations`, and every `spa_*` table directly (its `core`, `ai_credits`, `finance_management`, `developer/data_export.php`, and standalone `modules/scrapper.php` all touch this DB with no NestJS intermediary).
- `admin` — several specific modules cross into the tenants DB directly rather than going through backend: `growth_metrics` (`metric_types.php` writes), finance-memberships's `settings.php`, `outreach_requests` (`program_promotions` table — see thread 9), `intellectual_property` (`patents` table), `facilities` (dual-DB soft-delete write), and its own `scrapper` module's `list.php` (reads every tenant's DB with no scoping to the current tenant — a known finding, not by design).

### 8. Ecosystem directory (cross-tenant profile sharing)

`backend`'s `ecosystem` module proxies profile search/sync to `tenants`' `ecosystem` module (8 entity types, best-effort). `frontend`'s `search` / `global-search-page` are the UI surface on top of this chain.

### 9. Program promotions / outreach

`admin`'s `outreach_requests` module reads/writes the `program_promotions` table, which lives in the shared tenants DB, not the per-tenant client DB — the same table `tenants`' global-system module exposes via its program-promotion-tracking endpoint (itself consumed by `backend`'s `sanchiconnect.service.ts`).

### 10. Zoho — same name, no shared contract (documented gotcha)

`backend`'s `zoho` (`core/zoho`) and `admin`'s `zoho` module are two entirely independent CRM integrations — different code, different sync logic, no shared table or contract. Do not assume a change in one affects the other; this is called out explicitly as a workspace-wide guardrail because the naming collision invites exactly that mistake.

### 11. External cross-workspace: PowerPitch

`backend`'s `power-pitch-module` calls `power-pitch-sanchiconnect-api`'s `/v1/externals/*` endpoints (SanchiPowerpitch workspace, external to this repo folder) via `PowerPitchExternalService` — tenant identity via `x-hostname` header, session token cached/refreshed 10 min before JWT expiry. `frontend`'s `pitch-deck-management` module is the UI surface for this integration's "live video" mode. PowerPitch never calls back into any SanchiSaaS repo.

### 12. Same-feature, three-repo pairs (authoring in admin, delivery via backend, display in frontend)

Several features exist as a matched trio — an admin authoring/management module, a backend module that owns the contract, and a frontend display module:

| Feature | Admin module | Backend module | Frontend module |
|---|---|---|---|
| Resource library | `resource-files` | `resources` | `resources` |
| Glossary | `glossary` | `glossary` | `glossary` |
| Support tickets | `tickets` | `tickets` | `tickets` |
| Learning management | `learning_management` | `learning-management` | `learning-management` |
| Certificates / ID cards | `certificates`, `certificate_builders`, `id_card_builders`, `id_cards` | `certificates`, `id-cards` | `cerificates`, `sc-certificate-renderer`, `sc-id-card-renderer` |
| Growth metrics / milestones | `growth_metrics`, `metric_types`, `milestones` | `metrics`, `milestones` | `dashboard-v2`, `growth-matrics`, `milestones` |
| Facilities | `facilities` | `facility_management` | `facilities-management`, `external-facilities-management` |
| In-app ads | `ads-management` | — (served as flag/config) | `ad-viewer` |
| IP / patents | `intellectual_property` (+ direct tenants-DB write) | `ip-management` (proxy) | `ip-search`, `ip-request` |

### 13. Two identically-named "scrapper" modules — unrelated

`sc-saas-admin/modules/scrapper/` (Capboard/IESA external scrapers + a `list.php` reading every tenant's DB) and `sanchiconnect-saas-tenants-admin/modules/scrapper.php` (a single file reading the tenants DB directly for platform reporting) share a name and nothing else — different repo, different purpose, different code. Treat as a naming collision, not a connection.

### 14. Hub/Spoke stakeholder visibility, moderation ownership & program provenance (added 2026-09)

A "spoke" is a partner's own branded subdomain (`{partner.abbreviation}.{tenant domain}`, e.g. `kah.thub.sanchidev.in`), resolved backend-side by `PartnerSubdomainMiddleware` off the `x-hostname` header the frontend sends on every call (the SPA itself always calls one shared `apiUrl` regardless of which spoke subdomain the browser is on). This body of work makes Connections, Meetings, and the three program-listing surfaces (Programs, VS Programs, Call for Applications) spoke-aware end to end, gated on `Feature.HUB_SPOKE_DOMAIN_ENABLED`:

- **Moderation bypass.** Two stakeholders of the *same* spoke connecting or meeting no longer needs Hub moderation by default — `ConnectionsService.isModerationRequired()` and `MeetingsRepository.createMeetingV2()` both short-circuit when `getStakeholderPartnerId(fromUser) === getStakeholderPartnerId(toUser)` (a stakeholder's spoke lives on their own profile row — `StartupEntity.partnerId` etc — **not** on `UserEntity.partnerId`, which is a different, sibling field meaningful only for `accountType === 'partner'`). A new tenant flag, `spoke_stakeholders_meeting_moderation_enabled`, lets a tenant opt back into moderating same-spoke meetings too.
- **Moderation ownership enforcement.** When a same-spoke meeting *does* require moderation (via the flag above), only that spoke's own partner may Accept/Reject it — not the Hub. Enforced at the backend (`performModerationMeetingAction()` compares `meeting.partnerId` against a server-side `actingPartnerId`, never a client-supplied value) and mirrored in `sc-saas-admin`'s UI (the Forward/Reject buttons only render for the party actually allowed to act).
- **`connections.partner_id` / `meetings.partner_id`.** Stamped only when both parties share one spoke — the moderation-ownership signal above, not a general visibility filter.
- **Spoke Engagement console** (`sc-saas-admin`, partner sessions, `Engagement → Connections/Meetings`, routed through the same `table/connections` / `table/meetings` generic engine Hub admins use, not a separate one). Deliberately **broader** than the `partner_id` column: shows every row where *either* party is one of that spoke's own stakeholders — including cross-spoke and Hub-native counterparts — resolved via a `getSpokeStakeholderUserIds()` helper across all 7 stakeholder tables, not `partner_id` equality.
- **Program visibility.** `programs-management` and (newly, this pass) `vs-programs-management` scope results to the resolved spoke's own `partnerId`; `application-programs-management`'s authenticated route was fixed to resolve the viewer's spoke server-side (`req.user.partnerId ?? resolvedPartner?.id`) instead of trusting a client-supplied query param (tracked historically as SAN-391). VS Programs gained a `partnerId` column (previously had no spoke concept in the schema at all).
- **Provenance badge.** The "Active Programs" dashboard widget and full Programs list badge a promoted/cloned program with its source (partner name, source tenant name, or the Hub's own brand name for a Hub-owned program promoted to a spoke) via `program.isPromoted` / `program.promotedFromName`, additive fields with no effect on programs that aren't promoted.
- **Email link routing.** Stakeholder-facing action links (connection request/accept/reminder, meeting feedback, mentor-hours approval) resolve the *recipient's* own spoke via `UrlService.getLongActionUrl(actionUrlDto, recipientPartner?)`, an opt-in parameter — omitted, it's byte-identical to the pre-existing Hub-only behavior. The one deliberate exception: the actual video-meeting-join link stays Hub-only always, because VideoSDK (the video-call provider) has no public API for per-spoke domain whitelisting — a spoke visitor is routed to the Hub's own (already-whitelisted) domain specifically for that link, by the frontend's `MeetingService.getMeetingUrl()`.

### 15. Dynamic persona / branding fields (`*_title` columns, added 2026-08/09)

`TenantUsersEntity` carries a family of nullable `varchar` columns (`events_title`, `glossary_title`, `partners_title`, `service_providers_title`, `startups_title`, `startup_kit_title`, …) letting a tenant rename a persona/product word platform-wide (e.g. "Startups" → "Shopkeepers" for a non-deep-tech accelerator) without a code change. Each is a single **plural-only** English default; a singular form is derived at render time via a `toSingular()` wrapper around the `pluralize` npm package (frontend) or a crude `preg_replace('/s$/i', ...)` helper (admin — `getStartupsTitle()` in `includes/core_functions.php`). No shared/generic mechanism exists across either consuming app: every UI site hand-wires `brandDetails?.features?.xxx_title || 'Default'` (frontend) or reads the tenant-DB setting directly (admin, via `$customHeadersFromTenants` in `modules/common.php` for page/menu titles, or ad hoc per call site for everything else). Consumed by `frontend`'s `IBrandDetails.features` (via the same `verify_tenant`/`resolve-domain` payload as feature flags — thread 2 above) and `backend`'s generic boolean/string type-split (`segregateSAASData()`), which puts every `*_title` string into `saasSettings` automatically the moment a column exists, with no special-casing required.

---

## Part D — Roles & access

Verified directly against code (role enums, guards, session role checks) on 2026-07-21 — not inferred from naming.

### D.0 — Who logs into which repo, at a glance

| Repo | Who accesses it | How |
|---|---|---|
| `sanchiconnect-saas-tenants` | Nobody, directly — no human login or UI. Consumed by `backend` at bootstrap and read/written directly by `tenants-admin` (shared DB). | N/A |
| `sc-saas-backend` | Nobody logs in directly — a JWT-authenticated API called by end-users (via `frontend`) and staff (via `admin` / `tenants-admin` cURL calls under their own separate sessions). A subset of privileged routes accept an `:adminMd5` path token instead of a JWT+role check, for admin-triggered writes. | JWT (`Role` / `accountType`) + `:adminMd5` token (admin-triggered routes) |
| `sc-saas-frontend` | End-users of 10 account types, self-registered. | JWT + localStorage session, `AuthGuard` per route |
| `sc-saas-admin` | Accelerator/incubator internal staff (7 roles, 2 dead) + a logically separate external partner-org actor (token-exchange login, not a staff role). | Session-based RBAC (`spa_admin_roles`, per-tenant) |
| `ai-startups-analyzer` | Nobody, directly — API-key authenticated, called only by `sc-saas-admin`. | Bcrypt-hashed API key |
| `sc-saas-3rdparty-webservices` | Nobody — no auth of any kind, relies entirely on network isolation. Called only by `sc-saas-backend` (+ one documented direct call from `admin`'s `meetings` module). | None (network-isolation only) |
| `sanchiconnect-saas-tenants-admin` | Sanchi's own internal platform-operations staff — same 7 role names as `sc-saas-admin` (this repo is a forked sibling codebase), but a logically separate role table scoped to the shared, platform-global tenants DB, not per-tenant. | Session-based RBAC (`spa_admin_roles`, platform-global) |

### D.1 — `sc-saas-frontend`: account types & portal access

**Account types** (`ACCOUNT_TYPE`, `src/app/core/domain/auth.model.ts`): STARTUP, INVESTOR, OTHER, CORPORATE, PARTNER, JOB_SEEKER, MENTOR, SERVICE_PROVIDER, PROGRAM_OFFICE, INDIVIDUAL. A separate `ACCOUNT_ROLE` enum (`FOUNDER`, `CO_FOUNDER`, `HIRING_MANAGER`, `BUSINESS_HEAD`) is a sub-role within an account (e.g. team-member permissions), not a portal-gating dimension.

**Mechanism:** `AuthGuard` (`shared/guards/auth.guard.ts`) compares the logged-in user's stored `accountType` against a route's `data.expectedType` array, redirecting via a per-type dashboard URL map when it doesn't match — a real redirect-based guard, but only on routes where `expectedType` is actually declared.

| Portal module | Restricted to | Notes |
|---|---|---|
| `startups` | STARTUP | Consistently enforced |
| `investors` | INVESTOR | Consistently enforced |
| `mentors` | MENTOR | Only one route enforces it; others have it commented out (stale copy-paste) but still require login |
| `service-provider` | SERVICE_PROVIDER | Enforced |
| `individual-profile` | INDIVIDUAL | Only the dashboard route enforces it |
| `partners-dashboard` | PARTNER | Enforced on the dashboard route |
| `corporate` | Intended CORPORATE — mostly unenforced | Only one edit route enforces it; dashboard + most edit pages have `expectedType` commented out — any logged-in user of any account type can reach `/corporates/dashboard` by direct URL |
| `program-office` | Intended PROGRAM_OFFICE — not enforced anywhere | No route in this module declares `expectedType` — any logged-in user of any account type can reach the program-office dashboard/edit pages |
| `account`, `team`, `chat`, `notifications`, `community-feed`, `dashboard-v2`, `payment`, `tickets`, `milestones` | none | Shared across all account types — login only |

No admin account type exists in this app. `admin-actions`' `/backdoor-login/:id/:uuid` is pure impersonation (no `AuthGuard`, no confirmation UI, md5-secret-protected) — real staff login only happens in the separate PHP admin panels.

### D.2 — `sc-saas-backend`: roles & route enforcement

**Role enum** (`Role`, `src/core/constants/enum.ts`): STARTUP, INVESTOR, CORPORATE, MENTOR, INDIVIDUAL, SERVICE_PROVIDER, PARTNER, OTHER, JOB_SEEKER, PROGRAM_OFFICE — the same 10 values as frontend's `ACCOUNT_TYPE`, carried in the JWT payload.

**Mechanism:** `@Roles(...)` decorator + `RolesGuard`, stacked alongside `JwtAuthGuard` and (independently) `FeatureGuard` + `@Features(...)`. `RolesGuard` checks `roles.includes(request.user.accountType)` — it only fires where a route pairs `@Roles(...)` with `@UseGuards(..., RolesGuard)`; where that pairing is broken, the decorator is dead metadata (see gaps below).

| Module(s) | Role(s) required |
|---|---|
| `startup` (+ founder, pitch-deck, supporting-docs, advisory-board, fundingCommitment), `power-pitch-module`, `learning-management`, `form-management` (partial) | STARTUP |
| `investor` | INVESTOR |
| `corporate` | CORPORATE |
| `mentors` | MENTOR |
| `mentorship` | STARTUP, MENTOR (mixed per route) |
| `service-providers` | SERVICE_PROVIDER |
| `individual` | INDIVIDUAL |
| `partner` | PARTNER (+ PROGRAM_OFFICE on one route) |
| `program-office-members` | PROGRAM_OFFICE |
| `vs-programs-management` | INDIVIDUAL |
| `job` | STARTUP/INVESTOR/CORPORATE/PARTNER/SERVICE_PROVIDER/PROGRAM_OFFICE (employer side); JOB_SEEKER + OTHER (seeker side) |
| `challenges` | CORPORATE (create/manage), STARTUP (participate) |
| `metrics` / `metrics-v2` | STARTUP/INVESTOR/CORPORATE/MENTOR/PARTNER (view), STARTUP-only (write) |
| `user` (team-members) | STARTUP/INVESTOR/CORPORATE/PARTNER/SERVICE_PROVIDER |
| All other modules (`auth`, `connections`, `notifications`, `events`, `memberships`, `payment-management`, `invoice`, `ip-management`, `facility_management`, etc.) | No role restriction — JWT-only (any authenticated account type) |

**Confirmed decorator-without-enforcement gaps:** `job.controller.ts`'s `GET applied/list` and `POST :jobUUID/apply` carry `@Roles(JOB_SEEKER)` but the guard chain omits `RolesGuard` — any authenticated user of any type can call them. `startup-kit.controller.ts`'s check/submission endpoints carry `@Roles(STARTUP)` with the same gap. `application-management`'s role check is fully commented out (`// @Roles(Role.STARTUP)`) — effectively JWT-only now.

**Admin/internal access — no role, md5-token pattern instead:** there is no ADMIN value in `Role`. Privileged routes triggered by the PHP admin panels bypass JWT+`@Roles` entirely via an `:adminMd5` path param checked against `AdminUsersEntity.authToken`. Confirmed on: `migrations` (all 6 routes, no JWT/Feature guard at all), `program-management` (`update-round`, `payment-reminder` — admin check commented out, i.e. unauthenticated, `reject-round`, `tentative-round`), `ecosystem-admin`, `facility_management`, `payment-management`, `challenges`, `learning-management`, `connections`, `mentors` (application-management), `memberships`, `application-management`, `events`, `global` / `admin-actions`, `vs-programs-management`.

### D.3 — `sc-saas-admin`: staff roles & module access

**Enforcement mechanism:** session-based RBAC. Login validates against `spa_admin_users`; the user's `spa_admin_roles` row (columns incl. `code`, `title`, `is_dev`, `features`, `tables`, `menus`) loads into `$_SESSION['admin_roles']` on every request via `getMenus()`. `checkRole($flag)` tests a boolean role attribute (most commonly `is_dev`); `checkAdminRole()` / inline comparisons test `$_SESSION['admin_roles']['code']` against role-ID constants `define()`d in `config/config.php` from per-tenant ENV values. `checkLoggedIn()` alone is **not** a role check — several modules use only that.

**Role constants** (`config/config.php`): `super_admin_role_id`, `developer_role_id` (paired with the `is_dev` flag), `program_manager_role_id`, `corporate_program_manager_role_id`, `jury_role_id`, `recruitmentpartner_role_id`, `tto_role_id` / `tto_superadmin_role_id`. `reviewer_role_id` and `analyst_role_id` are defined but **dead** — zero comparisons anywhere in code. `incubator_admin_role_id` / `incubator_program_manager_role_id` are synthetic roles auto-provisioned for external partner-org logins (see below), not internal staff.

| Restriction | Modules |
|---|---|
| `is_dev` only (super_admin + developer) | `developer/*` (api, database, email, forms, menu, table-view management), `reporting/*` (dashboards, template/source editors), `finance_management/settings/gateways/*` |
| Explicit super_admin OR developer `code` check | `developer/settings_management.php`, `developer/email_template_preview.php`, cost-visibility gates in `application_management` (`analysis_list.php`, `analysis_cost_dashboard.php`, `analysis_result.php`) |
| `jury_role_id` only | All of `jury/*` (dashboard, programs, round review, ratings, startups) |
| `program_manager_role_id` (+ `corporate_program_manager_role_id` for challenge flows) | `application_management/program.php`, `reports.php`, `submission-application-management*.php`, `edit_program_round*.php` |
| `recruitmentpartner_role_id` only | `recruitment-partners/jobs.php`, `job-detail.php` |
| Explicitly excludes jury, otherwise open to any staff | `application_management/analysis_list.php`, `edit_program_round.php`, `draft_applications.php`, `finance_management/{payments,coupons,orders}/list.php` |
| `checkLoggedIn()` only — no role check | `system_logs/*` (any staff role can view raw log payloads), `ai_credits/*`, `profile_audit_logs/list.php` |
| `tto_role_id` | `intellectual_property/*` |

`partners` is a genuinely different actor, not a staff role: `partners/auth/login.php` exchanges a frontend `accessToken` cookie via cURL against `v1/users/profile/`, sets `login_auth_type = "partner"` + `partner_id` / `partner_org_uuid`, and scopes all queries to that external organization. It auto-provisions a synthetic `spa_admin_roles` row (`incubator_admin` / `incubator_pm`) purely so existing `checkRole()` code paths still work — this is plumbing, not a real internal role. `recruitment-partners/`, despite the similar name, is an ordinary internal-staff module gated by `recruitmentpartner_role_id` through the regular admin session.

### D.4 — `sanchiconnect-saas-tenants-admin`: platform-operator roles & module access

Confirmed directly in `config/config.php:117-140`: the same 7 role-ID constants as `sc-saas-admin` (`super_admin_role_id`, `reviewer_role_id`, `recruitmentpartner_role_id`, `jury_role_id`, `developer_role_id`, `program_manager_role_id`, `analyst_role_id`) — all actively referenced here, unlike the two dead ones in the sibling repo. This is not a documentation copy-paste error: this repo is a forked sibling codebase of `sc-saas-admin`, so the role names carry over even though they read oddly for a platform-operator tool ("jury"/"recruitment_partner" are vestigial from the shared template). The `spa_admin_roles` table here lives in the shared, platform-global tenants DB — a logically separate role table from `sc-saas-admin`'s per-tenant one, despite identical mechanics. `sc-saas-admin` additionally defines `tto_role_id`, `tto_superadmin_role_id`, `corporate_program_manager_role_id`, which don't exist here.

**Mechanism:** the same `checkRole($flag)` (boolean attribute, e.g. `is_dev`) and inline `$_SESSION['admin_roles']['code'] == ...` comparisons as `sc-saas-admin`; role data refreshes post-login via `getMenus()` → `checkRoleUpdates()`.

| Module | Gate | Role(s) required |
|---|---|---|
| `developer/*` (api_management, table_view_management, menu_management, form_fields_management, forms_layout_management, email_management, database_management) | `is_dev` flag | Any role carrying `is_dev` (typically developer) |
| `developer/settings_management.php`, `email_templates.php` | code check | super_admin or developer |
| `developer/data_export.php` | `is_dev` OR super_admin code | `is_dev` flag, or super_admin |
| `ai_credits/*` (grants, task_rates, orders, packages, setup_menu) | code check | super_admin or developer |
| `finance_management/*` (invoices, taxes, invoice_settings, invoice_view, setup_menu) | code check | super_admin or developer |
| `auth/admins.php` | code check (page); `is_dev` (full role visibility) | super_admin or developer |
| `aws/s3.php`, `filemanager/list.php`, `upload/rich_editor.php` | `checkLoggedIn()` only | Any logged-in operator, any of the 7 roles |
| `aws/ajax.php`, `filemanager/ajax.php` / `download.php`, `csv/export.php` / `import.php` | none | Unauthenticated — see the `csv` / `filemanager` / `aws` findings in each repo's own module-specs index |

`add.php` / `edit.php` also do targeted `program_manager_role_id` / `jury_role_id` lookups for conditional form-section visibility — not an access gate, just what's shown.

### D.5 — No human role model (leaf / internal services)

- `sanchiconnect-saas-tenants` — no UI, no login. Every route is either called by `backend` at bootstrap or read/written directly by `tenants-admin` against the shared DB; the confirmed-unauthenticated `verify_tenant` / `tenant-settings` routes (Part B, repo 1) have no role concept at all, just no auth.
- `sc-saas-3rdparty-webservices` — no auth of any kind on any endpoint; security is "only `sc-saas-backend` can reach this network path," not a role check.
- `ai-startups-analyzer` — bcrypt-hashed API keys (`api_keys` table), checked per-request; no concept of roles, just "has a valid key or not." Called only by `sc-saas-admin`, which itself decides which of its own staff roles are allowed to trigger a score run (see D.3, `application_management`).

---

## Sources

- Workspace `CLAUDE.md` (blast-radius graph + 6 cross-repo invariants)
- `specs/SanchiSaaS-Repo-Map.md` (repo-level purpose / owns / depends-on, 2026-07-16)
- `specs/tenants-module-specs-index.md`, `specs/backend-module-specs-index.md`, `specs/frontend-module-specs-index.md`, `specs/admin-module-specs-index.md`, `specs/ai-analyzer-module-specs-index.md`, `specs/3rdparty-webservices-module-specs-index.md`, `specs/tenants-admin-module-specs-index.md`
- Each repo's own `CLAUDE.md`
- Direct 2026-07-21 code verification of role enums/guards/session-role-checks in `sc-saas-frontend` (`auth.model.ts`, `auth.guard.ts`), `sc-saas-backend` (`enum.ts`, `roles.decorator.ts`, `rolesGuard.ts`, `jwt.strategy.ts`), `sc-saas-admin` (`config/config.php`, `includes/core_functions.php`), and `sanchiconnect-saas-tenants-admin` (`config/config.php`, `includes/core_functions.php`)
