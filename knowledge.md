# SanchiSaaS — Workspace Knowledge (as-is synthesis)

Last updated: 2026-08-13

This is a **synthesis document**, not a fresh code-extraction pass. Its source material is the seven
per-repo `knowledge.md` files (plus spot-checked `api.md`/`database.md`/`design.md`), all completed earlier
in this same documentation series:

- `sc-saas-admin/knowledge.md`, `sanchiconnect-saas-tenants/knowledge.md`, `sc-saas-backend/knowledge.md`,
  `sc-saas-frontend/knowledge.md`, `ai-startups-analyzer/knowledge.md`, `sc-saas-3rdparty-webservices/knowledge.md`,
  `sanchiconnect-saas-tenants-admin/knowledge.md`

Every claim below is a restatement or connection of a per-repo finding, cited as
`[Source: <repo>/<file> §<section>]`. Claims that go beyond a direct restatement — i.e. the cross-repo
*connections* this document exists to make — are tagged `[INFERRED — requires validation]` only where the
connection itself, not the underlying facts, is a synthesis judgment. Do not use this document as a
replacement for a per-repo `knowledge.md` — it intentionally omits detail that document already owns.

---

## 1. What each repo is and does (one paragraph each, from each repo's own knowledge.md)

**`sanchiconnect-saas-tenants`** — The control-plane/cockpit. NestJS 9 + TypeORM + a single shared MySQL
database (row-per-tenant). Owns the feature-flag *names* (`TenantUsersEntity`, ~180 boolean/enum columns)
and the two tenant-verification endpoints (`verify_tenant`, `tenant-settings`) that `sc-saas-frontend` and
`sc-saas-backend` depend on respectively. Also owns the AI-Credits **purchase-side** schema and the
Ecosystem/IP-Management cross-tenant-sharing features. Has no working tenant-provisioning API — the
`TenantsController` exposes zero routes. `[Source: sanchiconnect-saas-tenants/knowledge.md §Module Map, §Tenant Provisioning]`

**`sc-saas-backend`** — The business API. NestJS 8 + TypeORM + MySQL, **one deployment per tenant**, config
and feature flags loaded once at bootstrap from the cockpit and held in memory for the process lifetime.
Owns the REST API contract (58 wired-in feature modules, not the ~51 its own `CLAUDE.md` claims) that
`sc-saas-frontend` and `sc-saas-admin` both consume. Auth is JWT via an httpOnly cookie (Bearer fallback).
`[Source: sc-saas-backend/knowledge.md §Module Map, §The One-Deployment-Per-Tenant Tenancy Model]`

**`sc-saas-frontend`** — The end-user PWA. Angular 13 + NgRx (34 slices, not "~38"), no database, no
server-side API of its own. Resolves its tenant at runtime via `verify_tenant`, then points every
subsequent business/WebSocket call at the `apiUrl` the cockpit returns. Auth is actually an httpOnly
cookie, not the "JWT in localStorage" its own `CLAUDE.md` claims. `[Source: sc-saas-frontend/knowledge.md
§Bootstrap / Tenant-Verification Flow, §Auth Model]`

**`sc-saas-admin`** — The internal operations panel. Plain PHP ≥5.5, no framework, two simultaneous Medoo
connections per request (`$mainDatabase` = cockpit, `$database` = the resolved tenant's own DB). Owns the
AI-Credits **reserve/settle/refund/debit** spend-side logic (against tables defined by the NestJS tenants
repo) and drives the full AI-scoring lifecycle against `ai-startups-analyzer`. Also calls `sc-saas-backend`
and, directly and undocumented until this pass, `sc-saas-3rdparty-webservices`.
`[Source: sc-saas-admin/knowledge.md §Tenancy Resolution, §AI Credits System, §Third-Party Integration Pattern]`

**`ai-startups-analyzer`** — The AI scoring service. Python 3.10+/FastAPI/SQLAlchemy async, its own small
MySQL schema (`api_keys`, `analyses`, `batches`). Scores startup applications via a swappable LLM provider
(OpenAI/Anthropic/Gemini) on a frozen 0–500→1–5 scale. Called exclusively by `sc-saas-admin`; never
initiates contact with any other repo. `[Source: ai-startups-analyzer/knowledge.md §Application Bootstrap
& Lifespan, §Scoring Orchestration & Batch Pipeline]`

**`sc-saas-3rdparty-webservices`** — The integration gateway. NestJS 9, no database, no auth on any
endpoint (network-trust only, independently confirmed by exhaustive grep). Proxies SMS, email (SendGrid +
SMTP), chat (CometChat), video (VideoSDK), URL shortening (Short.io), and document conversion (ConvertAPI).
Documented as "called only by `sc-saas-backend`" — confirmed false; `sc-saas-admin` also calls it directly
for two routes. `[Source: sc-saas-3rdparty-webservices/knowledge.md §Security Model, §Reality Check: Who
Actually Calls This Service]`

**`sanchiconnect-saas-tenants-admin`** — The platform-operator admin UI over the tenants control-plane DB.
PHP, a fork of `sc-saas-admin`'s own skeleton (byte-identical dispatch loop) with the per-tenant-DB
resolution deliberately stripped out — it opens exactly one Medoo connection, directly to the shared
tenants DB. Documented as "fully standalone, no backend dependency" — confirmed false; it calls
`sc-saas-backend` directly on every `tenant_users` edit. `[Source:
sanchiconnect-saas-tenants-admin/knowledge.md §(a) Routing & Bootstrap, §(c) The Shared-DB Relationship,
§(g) Other Architecturally Significant Findings]`

---

## 2. Cross-repo thread: the AI-Credits schema has three independent direct mutators

The AI-Credits prepaid-wallet system (`ai_credit_wallets`, `ai_credit_ledger`, `ai_credit_orders`,
`ai_credit_task_rates`, `ai_credit_packages`, `ai_credit_grants`, plus GST/invoice tables) lives entirely in
the **shared tenants MySQL database** — not a dedicated AI-Credits database — and is mutated directly by
**three independently-deployed codebases with no shared schema-versioning mechanism between them**:

1. **`sanchiconnect-saas-tenants` (NestJS, TypeORM)** — owns the canonical schema (9 entities under
   `src/modules/ai-credits/`) and implements the **credit (purchase) side only**: a hash-verified Easebuzz
   payment callback increments `balance`/`totalPurchased` and writes a `CREDIT` ledger row, inside one
   transaction with a `pessimistic_write` row lock (added in a same-day fix, commit `0b6f504`). This repo
   has **no** `reserveAiCredits`/`settleAiCredits`/`refundAiCreditReservation`/`debitAiCreditsInstant`
   function anywhere. `[Source: sanchiconnect-saas-tenants/knowledge.md §AI Credits System]`
2. **`sc-saas-admin` (PHP, raw SQL over Medoo's `$mainDatabase`)** — owns the **reserve → settle → refund →
   debit spend side**: `includes/ai_credits_functions.php` implements exactly the four functions the NestJS
   repo lacks, against the identical table names, using raw PDO for the two atomic `WHERE balance >= ?`
   UPDATEs Medoo's query builder can't express, plus caller-level MySQL `GET_LOCK` advisory locks. The
   `credit_type` ENUM is cross-referenced in-code as "matching the canonical schema owned by
   `sanchiconnect-saas-tenants`" — i.e. this repo knows it is a schema *consumer*, not owner.
   `[Source: sc-saas-admin/knowledge.md §AI Credits System (reserve / settle / refund ledger)]`
3. **`sanchiconnect-saas-tenants-admin` (PHP)** — a third, newly-confirmed writer: this repo's
   `modules/ai_credits/{grants,task_rates,packages,orders}.php` perform direct PHP admin CRUD against the
   same `ai_credit_*` tables, gated only by the repo's own inlined
   `super_admin_role_id || developer_role_id` check (not a schema-aware guard). `[Source:
   sanchiconnect-saas-tenants-admin/database.md §AI Credits tables — a second, undocumented writer of the
   same schema `sc-saas-admin` mutates]`

**No cross-repo schema contract exists for any of this.** The NestJS repo has `synchronize: true` and no
migrations (see §5) — a column rename there silently alters or drops a column two independent PHP
codebases already assume exists, with zero compile-time or type-level warning on either PHP side, since PHP
has no visibility into TypeORM entity changes at all. `[Source: sanchiconnect-saas-tenants/knowledge.md
§Shared Database With `sanchiconnect-saas-tenants-admin` — Verified]` `[INFERRED — requires validation]`:
this three-way finding is a workspace-level connection no single repo's own documentation pass could see —
the tenants repo's own knowledge.md correctly identifies the *NestJS/PHP-admin* split but was written before
the tenants-admin pass confirmed the *third* writer.

---

## 3. Cross-repo thread: the documented call graph is wrong in at least three places

The workspace `CLAUDE.md`'s blast-radius graph and at least three repos' own `CLAUDE.md` files state
call-graph claims that this pass's seven independent code-extraction passes found to be **factually false**:

1. **`sc-saas-3rdparty-webservices` claims "called only by `sc-saas-backend`."** False.
   `sc-saas-admin` calls it directly for two routes: `getMeetingSessions()`
   (`includes/core_functions.php:5695`, plain `curl_exec`, **no auth header at all**, hitting
   `GET {3p_api_server_url}/v2/video-sdk/meetings/{code}/sessions`) and
   `acdGenerateProfileShortLink()` (`modules/table.php:124`, Guzzle,
   `POST {3p_api_server_url}/v1/short-io/short-url`). Both repos resolve `3p_api_server_url` /
   `THIRD_PARTY_SERVICE_BASE_URL` from the *same* `global_settings` row, neither aware the other also calls
   it directly. `[Source: sc-saas-admin/knowledge.md §Third-Party Integration Pattern; independently
   confirmed from the receiving side at sc-saas-3rdparty-webservices/knowledge.md §Reality Check: Who
   Actually Calls This Service]`
2. **`sanchiconnect-saas-tenants-admin` claims "fully standalone... does NOT call `sc-saas-backend`."**
   False. `resetAPISaaSSettings()` fires unconditionally on every `tenant_users` edit through this repo's
   generic dynamic-table form, calling `PATCH {api_url}api/v1/public/global/saas/settings` on that tenant's
   own `sc-saas-backend` deployment (a real, unauthenticated route confirmed present on the receiving side).
   A second call site, `sendAccountCreatedEmail()`, calls
   `{api_server_url}v1/admin-actions/admin-account-created/{token}` conditionally, if a `spa_settings` row
   for `api_server_url` happens to exist. `[Source: sanchiconnect-saas-tenants-admin/knowledge.md §(g) Other
   Architecturally Significant Findings, cross-referenced against sc-saas-backend/src/modules/global/global.controller.ts:51]`
3. **`sc-saas-admin` itself calls repos the workspace graph doesn't route through it at all**, beyond the
   documented `sc-saas-backend`/`ai-startups-analyzer` edges: direct Zoho CRM OAuth + REST calls, a direct
   WATI/WhatsApp client, a direct Google Gemini integration for video-pitch transcription (entirely separate
   from `ai-startups-analyzer`'s own multi-provider facade), direct payment-gateway credential validation
   against PayPal/Stripe/Razorpay/Easebuzz/PayU, and (via `easebuzz_callback.php`, deliberately routed
   *outside* `index.php`'s own dispatcher) a direct call to **`sanchiconnect-saas-tenants`**'s
   `/api/v1/ai-credits/webhooks/easebuzz/{success|failure}` — a fourth SanchiSaaS repo this one talks to
   that neither this repo's own `CLAUDE.md` nor the workspace graph names as a consumer relationship.
   `[Source: sc-saas-admin/knowledge.md §Third-Party Integration Pattern]`

**The corrected, real call graph** (workspace-CLAUDE.md edge in parentheses where it differs):

| Caller | Callee | Documented? |
|---|---|---|
| `tenants` | — (upstream, calls nothing inbound) | matches |
| `sc-saas-backend` | `tenants` (bootstrap) | matches |
| `sc-saas-backend` | `sc-saas-3rdparty-webservices` | matches |
| `sc-saas-backend` | `power-pitch-sanchiconnect-api` | matches |
| `sc-saas-frontend` | `tenants` (verify_tenant) | matches |
| `sc-saas-frontend` | `sc-saas-backend` (dynamic apiUrl) | matches |
| `sc-saas-admin` | `tenants` (reads cockpit DB directly) | matches |
| `sc-saas-admin` | `sc-saas-backend` (api_server_url) | matches |
| `sc-saas-admin` | `ai-startups-analyzer` | matches |
| **`sc-saas-admin`** | **`sc-saas-3rdparty-webservices`** (2 routes, direct) | **NOT documented — new edge** |
| **`sc-saas-admin`** | **`tenants`** (Easebuzz webhook, outside dispatcher) | **NOT documented — new edge** |
| `sc-saas-admin` | Zoho / WATI / Gemini / PayPal / Stripe / Razorpay / Easebuzz / PayU (external) | not in graph at all (external, but undocumented in this repo's own `CLAUDE.md`) |
| **`sanchiconnect-saas-tenants-admin`** | **`sc-saas-backend`** (PATCH saas/settings, conditional admin-account-created) | **NOT documented — contradicts this repo's own "fully standalone" claim** |
| `sanchiconnect-saas-tenants-admin` | `tenants` DB (shared, direct) | matches (documented as DB-sharing, not an API call — correct, this one really is DB-only) |
| `ai-startups-analyzer` | (none — leaf, confirmed) | matches |
| `sc-saas-3rdparty-webservices` | external providers only (leaf, confirmed) | matches |

`[INFERRED — requires validation]`: the table above is this document's own synthesis of the seven repos'
independently-confirmed findings; each row is individually sourced as cited above, but their assembly into
one corrected graph is a workspace-level judgment call, not a restatement any single repo's doc makes.

---

## 4. Cross-repo thread: three tenancy models coexist, plus one stripped fork, on this platform

This is a genuine architectural fact of this specific platform, not a defect to fix — four different
mechanisms answer "which tenant does this request belong to," each in a different repo:

1. **`sanchiconnect-saas-tenants`** — single shared MySQL DB, **row-per-tenant** keyed by `domain`, one
   TypeORM connection for the whole process. `[Source: sanchiconnect-saas-tenants/knowledge.md §Database
   Configuration & TypeORM Strategy]`
2. **`sc-saas-backend`** — **one deployment per tenant**. Config/flags loaded once at bootstrap into
   in-memory `saasSettings`/`saasFeatures` objects; no per-query tenant guard because there is only ever one
   tenant's data in the process. A `domain` column *does* exist on ~10 stakeholder entities but is never
   used as a query filter — it is a denormalized label for other tenants' deployments to read over HTTP
   (the Ecosystem Directory pattern), not a scoping mechanism. `[Source: sc-saas-backend/knowledge.md §The
   One-Deployment-Per-Tenant Tenancy Model — Verified Against Entity/Repository Code]`
3. **`sc-saas-admin`** — **per-tenant DB connection resolved per-request** from the shared cockpit DB,
   via two simultaneous Medoo connections (`$mainDatabase` for tenant lookup, `$database` for the resolved
   tenant's own business DB). `[Source: sc-saas-admin/knowledge.md §Tenancy Resolution (per-request,
   per-tenant DB)]`
4. **`sanchiconnect-saas-tenants-admin`** — a **stripped fork of `sc-saas-admin`'s own lineage**
   (byte-identical `index.php` dispatch loop) with the per-tenant-DB-resolution code still present,
   commented out verbatim, and deliberately disabled — this repo opens exactly **one** connection, directly
   to the shared tenants DB, and now operates as a platform-level tool with no tenancy resolution at all.
   One route (`modules/scrapper.php`) reintroduces ad-hoc per-tenant connections in a loop for a
   cross-tenant analytics dashboard, gated only by `checkLoggedIn()` — a legitimate platform-operator
   capability, but one that directly opens live connections into every tenant's own production database with
   plaintext credentials read from the shared DB, undocumented in either this repo's `CLAUDE.md` or
   `module.spec.md`. `[Source: sanchiconnect-saas-tenants-admin/knowledge.md §(c) The Shared-DB Relationship
   — a single, direct connection to the control-plane DB]`

`[INFERRED — requires validation]`: stating this as "three tenancy models plus one stripped fork" (rather
than "four models") is this document's own framing — the underlying four-way mechanism split is a direct
restatement of each repo's own finding.

---

## 5. Cross-repo thread: `synchronize: true` with no migrations is a platform-wide pattern

Confirmed independently, by separate code-extraction passes, in **every NestJS repo in the workspace**:

- **`sanchiconnect-saas-tenants`**: `synchronize: true` hardcoded unconditionally for every `NODE_ENV`
  branch; no migrations directory anywhere in the repo. Combined with `autoLoadEntities: true`, adding a new
  `@Entity` anywhere creates a live table in the shared control-plane DB on next deploy, no review gate
  beyond normal code review. `[Source: sanchiconnect-saas-tenants/knowledge.md §Database Configuration &
  TypeORM Strategy]`
- **`sc-saas-backend`**: independently reproduces the identical finding — `synchronize: true` hardcoded in
  every branch, no migrations directory (the `src/modules/migrations` folder found on grep is an unrelated
  NestJS feature module, not a TypeORM migrations folder). Across 305 entity files, a column rename
  auto-drops or auto-renames the live MySQL column on next deploy. `[Source: sc-saas-backend/knowledge.md
  §Database Configuration & TypeORM Strategy]`

This is the single highest-severity structural finding shared across the two NestJS repos, and it is what
makes §2's three-mutator AI-Credits finding materially worse than an ordinary "poly-repo, coordinate your
deploys" risk: the coupling there is a **raw shared-table schema**, not a versioned REST contract, and one
of the three writers can unilaterally, silently alter the shared schema on any deploy with no migration
safety net at all. `ai-startups-analyzer` is the one repo in the workspace with a *partial* mitigation — an
add-only `_sync_missing_columns()` auto-migration plus one legacy hand-written SQL migration predating it —
which never drops/renames, only adds. `[Source: ai-startups-analyzer/knowledge.md §Configuration & Database
Engine]`

---

## 6. Consolidated security findings across the platform

- **`verify_tenant`/`tenant-settings` plaintext secret exposure** (already flagged in the workspace
  `CLAUDE.md`, refined by this pass): `verify_tenant` exposes `azure_client_secret` in plaintext to any
  unauthenticated caller who knows a tenant hostname; `tenant-settings` (a different, also-unauthenticated
  route) separately exposes `email_password_ses` and other SMTP fields. Both endpoints use two different,
  non-equivalent `LIKE` hostname-matching strategies (substring vs. effectively-exact), and both are fully
  open (`public/global` prefix, no guard). `[Source: sanchiconnect-saas-tenants/knowledge.md §The
  Tenant-Verification Contract]`
- **Per-tenant DB passwords stored plaintext** in `tenant_users` (already flagged in the workspace
  `CLAUDE.md`) — this pass found a *new* consumer of that plaintext column the workspace guardrail didn't
  anticipate: `sanchiconnect-saas-tenants-admin`'s `modules/scrapper.php` reads
  `tenant_users.database_password` in plaintext to open ad-hoc connections into every individual tenant's
  production database. `[Source: sanchiconnect-saas-tenants-admin/knowledge.md §(c) The Shared-DB
  Relationship, Known Issues]`
- **Hardcoded live API keys committed to source** — `sanchiconnect-saas-tenants`'s
  `global.repository.ts` hardcodes a live `factacy_api_key` and `currency_api_key` as TypeORM seed defaults
  (not read from `.env`). `<redacted — see sanchiconnect-saas-tenants/knowledge.md §Shared Database With
  `sanchiconnect-saas-tenants-admin` — Verified>`
- **Plaintext OAuth secrets in `sc-saas-backend`'s `PaymentGatewaysEntity`** — stored as plaintext `varchar`
  columns; a working `CryptoService.encrypt`/`decrypt` exists in the same codebase but is used only by an
  unrelated module (`connections/public/connection.service.ts`), never by payment-management.
  `<redacted — see sc-saas-backend/knowledge.md Change Log entry and sc-saas-backend/database.md §PaymentGatewaysEntity>`
- **Unauthenticated Adminer console with an embedded live DB password** — `sanchiconnect-saas-tenants-admin`
  bundles a full third-party MySQL web console (`adminer/adminer.php`) at the repo root, outside the app's
  own routing/auth entirely (Apache serves it directly since it's a real file); the "DB Administration" menu
  link renders the live `.env`-sourced database password as a plaintext URL query parameter.
  `<redacted — see sanchiconnect-saas-tenants-admin/knowledge.md §(g) Other Architecturally Significant
  Findings>`
- **`sc-saas-3rdparty-webservices` has zero authentication on any endpoint**, confirmed by exhaustive grep —
  anyone with network access can create/delete CometChat users, generate VideoSDK meeting tokens, send
  arbitrary email/SMS billed to the platform's own provider accounts, and generate arbitrary short links,
  with no rate limiting anywhere. This is architecturally-intended (network-perimeter trust), but the §3
  finding that `sc-saas-admin` also calls it directly — one call site with **no auth header at all** — means
  the trust boundary is wider in practice than either caller's own documentation assumes.
  `[Source: sc-saas-3rdparty-webservices/knowledge.md §Security Model: No Auth, Network Trust Only]`
- **Five of six sampled AJAX handlers in `sanchiconnect-saas-tenants-admin` skip the login check entirely**,
  relying on CSRF-token-equality (which any anonymous visitor can obtain by loading any public page) as the
  only access control on endpoints that create/update/delete `spa_settings`, email templates, API-route
  metadata, S3 objects, and — via the generic CRUD handler — arbitrary rows in any table this admin panel
  manages, including `tenant_users` itself. `[Source: sanchiconnect-saas-tenants-admin/knowledge.md §(g)
  Other Architecturally Significant Findings]`
- **Arbitrary raw SQL execution with no login/role gate, confirmed in *two* separate admin repos** (found
  2026-07-16/17, module-spec-level review — see §10): `sc-saas-admin/modules/ajax/crud_actions.php` and
  `sanchiconnect-saas-tenants-admin/modules/ajax/crud_actions.php` each expose a `sql_query` action that
  passes `$_POST['sql']` directly to `$database->query()` with zero allowlist — and the entire file in both
  repos has no `checkLoggedIn()`/`checkRole()` call at all, only `verifyCSRFToken()`. In `sc-saas-admin`,
  the same ungated file is also where `system-admin`'s destructive DDL (CREATE/DROP/ALTER/TRUNCATE/RENAME
  TABLE) actually runs, despite being documented as gated behind `is_dev` — any logged-in admin of any role
  can execute it. `[Source: sc-saas-admin/module.spec.md (ajax), sanchiconnect-saas-tenants-admin/module.spec.md (ajax)]`
- **`facility_management`'s authenticated routes are not actually feature-gated** — three of five
  controllers (`FacilityManagementController`, `BookingFacilityController`, `EcosystemFacilityManagementController`)
  only apply `JwtAuthGuard`; `FeatureGuard` (the guard that reads `@Features` metadata) is never imported or
  applied there. Disabling the `facility_management` flag for a tenant currently does nothing to these
  routes — only the two `Public*` controllers actually enforce the flag. `[Source: sc-saas-backend/module.spec.md (facility_management)]`
- **Two "guard decorator present but not wired" gaps in `sc-saas-backend`**: `startup-kit`'s
  `@Roles(Role.STARTUP)` and `verifications`' `@RateLimit` on the WhatsApp OTP send route are both dead
  metadata — `RolesGuard`/`RateLimiterGuard` are never actually applied on those specific routes, so the
  restriction/rate-limit each decorator implies is not enforced. `[Source: sc-saas-backend/module.spec.md (startup-kit, verifications)]`
- **Worst finding of the entire module-spec sweep (2026-07-19): `sanchiconnect-saas-tenants-admin`'s
  `modules/csv/export.php`/`import.php` have no authentication of any kind** — not even the CSRF-token-
  equality check every other unguarded endpoint in that repo at least has. Traced end-to-end
  (`index.php`'s router → `common.php` → the handler itself: no `checkLoggedIn()`, no `verifyCSRFToken()`
  anywhere in the chain) against the single shared tenants MySQL DB, with the table name taken raw from the
  query string and no allow-list. Any anonymous caller can dump `tenant_users` (plaintext per-tenant DB
  credentials) or `spa_admin_users` (operator password hashes) with one GET request, or insert arbitrary
  rows via `import.php`. Tracked as **Linear SAN-42 (Urgent)** — not yet fixed. `[Source:
  sanchiconnect-saas-tenants-admin/modules/csv/module.spec.md]`
- **The same unauthenticated `filemanager`/`aws` endpoint pattern exists in *both* PHP admin repos** —
  `sc-saas-admin` and `sanchiconnect-saas-tenants-admin` each have a `filemanager/download.php` with zero
  auth (readfile() of any path) and an `ajax.php` whose one `cleanPath()` path-traversal sanitizer is
  defined but never called anywhere in either codebase; both also have an `aws/ajax.php` gated only by a
  CSRF token that `index.php` mints for any anonymous visitor. Tracked as SAN-22/31 (`sc-saas-admin`) and
  SAN-43/46 (`sanchiconnect-saas-tenants-admin`) — same code lineage, same bug, two repos, none fixed yet.
  `[Source: sc-saas-admin/modules/{filemanager,aws}/module.spec.md, sanchiconnect-saas-tenants-admin/modules/{filemanager,aws}/module.spec.md]`
- **`sc-saas-backend`'s WebSocket gateway (`core/sockets/FetchCountGateway`) is fully unauthenticated** — no
  `@UseGuards`, no JWT/handshake identity check anywhere. Its `joinRoom` handler joins any connected client
  to any arbitrary room string with zero validation, so knowing/guessing a `conversation_<uuid>` (or a bare
  numeric user-id room) lets a client eavesdrop on someone else's chat typing indicators, messages, and
  notifications. Confirmed real, actively-used consumers (`chat.service.ts`, `connections.service.ts`,
  `conversations.service.ts`), not dead code. Tracked as **SAN-45**. `[Source: sc-saas-backend/src/core/sockets/module.spec.md]`
- **`sc-saas-frontend`'s `admin-actions` module calls a backend impersonation endpoint
  (`/backdoor-login/:userId/:adminMd5`) that takes a real admin auth token as a raw URL path segment** —
  exposed to browser history/server logs/`Referer` headers by construction — with no per-target-user
  validation and no route guard beyond a no-op `FeatureGuard` (no `@Features()` decorator on that specific
  handler). A leaked link grants permanent impersonation of any user by id. Tracked as **NIR-5**.
  `[Source: sc-saas-frontend/src/app/modules/admin-actions/module.spec.md]`
- **`global.controller.ts`'s zero-auth-guard finding (bullet 1 above) has a new confirmed refinement**:
  `getTenantSettings()`'s query has no `active = true` filter at all in its `where` clause (unlike
  `verifyTenant()`, which does filter on it) — so a **deactivated** tenant's plaintext SMTP password and
  other settings remain fetchable by hostname alone, not just active tenants'. Tracked as **SAN-44**.
  `[Source: sanchiconnect-saas-tenants/src/modules/global/module.spec.md]`

---

## 7. No Docker, CD, or infra-as-code anywhere in the workspace; CI since October 2026

No `Dockerfile` and no infra-as-code (Terraform, CloudFormation, Pulumi) in any of the seven repos;
deployment is manual/ops-run (Jenkins) in every case. `[Source: each repo's own design.md]`

**Updated 2026-10-14 (P-SAN-75):** GitHub Actions CI now exists in all seven repos: `ci.yml` (runs
`scripts/gates.sh`: lint/test/build, test floors, phpstan/phpcs, auth-gate and ai-credit-write checks per
stack), `secret-scan.yml` (gitleaks), and the cross-repo contract workflows `flags`, `tenant-contract`,
`scoring-contract`, `api-contract`. `ci-alerts.yml` posts release-branch failures to Slack. Branch model,
gates, rulesets and CI secrets: `docs/DEPLOYMENT.md`. `[Source: .github/workflows/ in each repo]`

---

## 8. Verifying the workspace `CLAUDE.md`'s own blast-radius graph

What the graph gets **right**, confirmed by this pass:
- `tenants → backend` (bootstrap-blocking), `tenants → frontend` (verify_tenant, app-init-blocking),
  `backend → {frontend, admin}` via the REST API contract — all confirmed exactly as documented, at the code
  level, from both producer and consumer sides. `[Source: sanchiconnect-saas-tenants/design.md §Why a
  verify_tenant/tenant-settings shape change breaks..., sc-saas-frontend/design.md §Why a verify_tenant
  Shape Change Breaks This Repo Specifically]`
- `ai-startups-analyzer` is correctly a leaf node — confirmed, it never calls back into any SanchiSaaS repo.
  `[Source: ai-startups-analyzer/knowledge.md, repo-wide]`
- `sc-saas-3rdparty-webservices` never calls back into any other SanchiSaaS repo (leaf in the *outbound*
  direction) — confirmed. What's stale is the *inbound* side (see §3).
- `sanchiconnect-saas-tenants-admin ↔ sanchiconnect-saas-tenants` DB-sharing is confirmed exactly as
  documented, at the literal table-name level (`tenant_users`, `global_settings`, `ai_credit_*`, 20 `spa_*`
  entities). `[Source: sanchiconnect-saas-tenants/knowledge.md §Shared Database With
  sanchiconnect-saas-tenants-admin — Verified]`
- The `power-pitch-sanchiconnect-api` external contract (invariant #6) is confirmed accurately described,
  including the `x-hostname` header and the 10-minute-before-expiry token refresh.
  `[Source: sc-saas-backend/knowledge.md §PowerPitch External Integration]`

What the graph gets **stale/wrong**, per §3 above:
- `sc-saas-3rdparty-webservices` is not "called only by `sc-saas-backend`" — `sc-saas-admin` is a confirmed
  second direct caller.
- `sanchiconnect-saas-tenants-admin` is not DB-only toward the tenants repo — it also makes direct outbound
  HTTP calls to `sc-saas-backend`.
- The graph has no edge at all for `sc-saas-admin → sc-saas-3rdparty-webservices` or
  `sc-saas-admin → tenants` (Easebuzz webhook) or `sanchiconnect-saas-tenants-admin → sc-saas-backend` — all
  three are real, confirmed, undocumented edges.

---

## 9. The workspace boundary — SanchiPowerpitch is a sibling poly-repo, not part of this one

`CLAUDE.md` invariant #6 documents the one contract that crosses into SanchiPowerpitch
(`power-pitch-sanchiconnect-api`'s `/v1/externals/*`, called from `sc-saas-backend`'s
`PowerPitchExternalService`), but neither `CLAUDE.md` nor this document previously named the sibling
workspace's other repos or confirmed it actually exists on disk. Verified directly, 2026-07-16:

- SanchiPowerpitch is a separate poly-repo workspace, cloned at `/Users/mac/Desktop/Work/SanchiPowerpitch`
  (a sibling of this `SanchiSaaS` folder, not nested inside it) — its own `CLAUDE.md`/`README.md`/
  `AI-NATIVE-SETUP.md`/`specs/` exist there, mirroring this workspace's own root-level structure.
- It contains **four** repos, each with its own `.git`: `power-pitch-sanchiconnect-api`,
  `power-pitch-sanchiconnect-frontend`, `power-pitch-sanchiconnect-admin`, `power-pitch-partners`.
- **Exactly one** contract crosses the boundary in either direction: `sc-saas-backend` → `power-pitch-
  sanchiconnect-api`'s `/v1/externals/*` (invariant #6, unchanged). PowerPitch never calls back into
  SanchiSaaS. No other SanchiPowerpitch repo (frontend, admin, partners) has any confirmed contract with
  any SanchiSaaS repo.
- **Correction to a claim in this workspace's own repo-map reference (dated 2026-07-15):** that document
  states `power-pitch-sanchiconnect-admin` "had no meaningful commits yet." Checked directly via `git log`
  — this is wrong, not just stale: the repo has 12 commits total, including real feature work ("plans
  management", "add partner user", email-template changes) dated 2022-12-21 through 2023-04-21, then a
  three-year gap before a single docs-only commit (CLAUDE.md + module specs) landed 2026-06-19. So the repo
  has genuine historical business logic, just no active development in over three years as of this check —
  a materially different situation from "no meaningful commits."
- `prabs/` (the evaluated-and-rejected SpecPod framework) lives in this `SanchiSaaS` folder, not
  SanchiPowerpitch's — already covered by this workspace's own memory/decision record, not a SanchiPowerpitch
  concern.

---

## 10. Module-level re-verification (2026-07-16/17) — real bugs found beyond doc drift, at a much higher rate than expected

Following the repo-level re-verification in §8/Change Log, every committed `module.spec.md` in all 7 repos
(139 files total) was individually re-checked against current source code. Most modules were already
accurate — this was a targeted fix pass. The severe security findings from this pass are folded into §6
above; this section covers the broader methodology and the non-security bugs found.

**Real bugs confirmed (not just doc drift), beyond the §6 security items:**
- `sc-saas-3rdparty-webservices`'s `shortIo.service.ts`: `getShortAcceptUrl()` builds the identical
  `/connection-request/reject` URL as `getShortRejectUrl()` — accepting a connection request currently
  generates a reject link. `[Source: sc-saas-3rdparty-webservices/module.spec.md (shortIo)]`
- `sanchiconnect-saas-tenants`'s `ecosystem-facilities.service.ts`: `getTenantUserByDomain()` selects only
  `['facility_module_allowed_domains', 'domain']` from `TenantUsersEntity`, omitting `facility_module_type`
  — every `=== FacilityModuleType.EXTERNAL` check compares against `undefined` and always evaluates false.
  The External Facilities Hub feature is silently non-functional for every tenant, no error surfaced
  anywhere. `[Source: sanchiconnect-saas-tenants/module.spec.md (ip-management + ecosystem-facilities)]`
- `sanchiconnect-saas-tenants`'s `organizations` table was misattributed: the prior spec claimed
  `sc-saas-admin` writes `organizations`/`invoices`/`payments`/`contacts`/`contracts` directly — grepped
  `sc-saas-admin` and found zero references to any of these tables. The actual writer is
  `sanchiconnect-saas-tenants-admin` (registers `organizations` as "Clients" in its generic CRUD engine).
  `[Source: sanchiconnect-saas-tenants/module.spec.md (organizations)]`
- `sc-saas-admin`'s `tickets` module: the documented "closed state" model was wrong — `reopen_ticket` sets
  separate `reopened_at`/`reopened_by_id` columns rather than clearing the closed pair, and there is no
  `tickets.token` column at all (the `{token}` path segment on backend email endpoints is a one-time admin
  backdoor token, not a ticket identifier). `[Source: sc-saas-admin/module.spec.md (tickets)]`
- `sc-saas-frontend`: `dashboard-v2`'s `/market-insights/news/hot-topics` route wires to
  `InnovationsDashboardComponent`, not the declared `HotTopicsComponent` (which is dead code, never
  referenced by any route) — a genuine routing bug, not a doc issue. Separately, `pitch-deck-recorder` is
  confirmed dead code end-to-end (unrouted; its one embed site is itself unreachable), and the `payment`
  module's `/payment-gateways` route has no `loadChildren` anywhere, making it fully unreachable.
  `[Source: sc-saas-frontend/module.spec.md (dashboard-v2, pitch-deck-recorder, payment)]`

**Methodology finding — trust a single verification pass's "no changes" claims with caution:** after this
pass, an adversarial second round sampled 18 modules the first pass had explicitly marked "no changes —
verified accurate" and re-ran them with agents instructed to assume the prior verdict was wrong and try to
disprove it. **16 of 18 (89%) had real, previously-missed gaps** — only 2 modules held up cleanly under
genuine adversarial pressure. A "verify this doc against the code" instruction without adversarial framing
produces confirmation-biased results; agents tend to skim-and-agree rather than genuinely try to break each
claim. Only 18 of the ~125 modules originally marked "no changes" across this workspace have been
adversarially re-checked so far — the remaining ~107 are still resting on the original, now-demonstrated-to-
be-unreliable pass, and would very likely surface more real issues at a similar hit rate if swept.

---

## 11. Module-spec coverage is now complete across all 7 repos (2026-07-17 → 2026-07-20)

Following on from §10, every module directory in every repo in this workspace now has its own
`module.spec.md` — a workspace-wide gap-closing effort spanning four sessions. **101 new module specs were
authored** on top of the pre-existing ones, bringing every repo to full coverage:

| Repo | Module specs | New this pass | Index |
|---|---|---|---|
| `sc-saas-admin` | 68 | 38 | [admin-module-specs-index.md](specs/admin-module-specs-index.md) |
| `sc-saas-backend` | 61 (58 `src/modules` + 3 real bounded contexts in `src/core`) | 3 | [backend-module-specs-index.md](specs/backend-module-specs-index.md) |
| `sc-saas-frontend` | 82 | 52 | [frontend-module-specs-index.md](specs/frontend-module-specs-index.md) |
| `sanchiconnect-saas-tenants` | 8 | 2 | [tenants-module-specs-index.md](specs/tenants-module-specs-index.md) |
| `sanchiconnect-saas-tenants-admin` | 10 (9 modules + root/foundation spec) | 6 | [tenants-admin-module-specs-index.md](specs/tenants-admin-module-specs-index.md) *(new index — this repo had none before)* |
| `sc-saas-3rdparty-webservices` | 7 | 0 (already complete; index refreshed, several stale route paths corrected) | [3rdparty-webservices-module-specs-index.md](specs/3rdparty-webservices-module-specs-index.md) |
| `ai-startups-analyzer` | 1 consolidated spec + `scoring_engine_spec.md` (FastAPI's structure doesn't map to one-spec-per-directory) | 0 (index refreshed; found the scoring-engine spec's rounding-precision text hadn't caught up to a 2026-07-17 code fix) | [ai-analyzer-module-specs-index.md](specs/ai-analyzer-module-specs-index.md) |

**How to use these indexes:** each is the fastest way to find a module's spec, its owned/consumed
contracts, and any known bugs/security findings without grepping the repo directly — start here before
reading a module's code cold. Every index was regenerated (or, for `sanchiconnect-saas-tenants-admin`,
created for the first time) by re-deriving its contents directly from the actual `module.spec.md` files and
directory listings on disk, not by trusting the previous index's claims — each repo's coverage was also
independently re-verified with a fresh directory scan as part of this pass (all showed 0 gaps).

**Naming-collision pattern found repeatedly across repos**: several directories in `sc-saas-admin`,
`sc-saas-frontend`, and the workspace generally contain *only* a `module.spec.md` and no code — older,
broader "combined" docs (e.g. `sc-saas-admin/modules/integrations/`, `content-management/`,
`growth-metrics/`, `finance-memberships/`, `partners-recruitment/`; `sc-saas-frontend/modules/utilities/`
and ~13 other umbrella specs) that predate this workspace's one-spec-per-directory convention and document
several real code directories jointly. These are kept as supplementary/legacy references, cross-linked from
the newer per-directory specs that now supersede them for anything code-specific — not deleted, since they
sometimes contain cross-cutting context (e.g. shared DB-write patterns) the narrower specs don't repeat.

**New security/correctness findings surfaced by this final sweep are folded into §6 above** rather than
repeated here — see the bullets covering `sanchiconnect-saas-tenants-admin`'s unauthenticated `csv`
export/import (the single worst finding across the whole multi-session effort), the repeated
`filemanager`/`aws` unauthenticated-endpoint pattern across both PHP admin repos, `sc-saas-backend`'s
unauthenticated WebSocket gateway, and `sc-saas-frontend`'s `admin-actions` impersonation-endpoint risk.

---

## 12. Observability rollout (2026-07-28 → 2026-07-30) — Sentry across all 7 repos, a real multi-week downtime incident it surfaced, and a full 39-issue triage pass

This week added the workspace's first error-tracking/observability layer, on top of which a genuine production
incident was found and fixed, followed by a systematic bug-fixing pass over every issue it surfaced. This
section is the map of what now exists and how it was built — read it before assuming "no monitoring exists"
(true before this week) or before re-investigating any of the specific bugs listed below (already root-caused
and fixed).

**a. Sentry.io rollout.** One Sentry organization (`sanchisaas`, `sanchisaas.sentry.io`), one project per repo
(7 total, matching the workspace's repo list). Errors + Performance are live on all 7; the structured Logs
pillar only exists on the two repos whose stack can run the v8+ SDK mainline (`@sentry/nestjs`, Node ≥18) —
everywhere else (`sc-saas-backend`, `sc-saas-3rdparty-webservices` on Node 16; both PHP admin repos;
`sc-saas-frontend` on Angular 13) uses the older `@sentry/node@7`/`sentry/sentry` SDKs, which have no Logs API,
so a `CaptureConsole`-equivalent integration (console.warn/error → Sentry Issues) substitutes for that pillar.
A custom `SentryLoggerService` (NestJS repos) forwards only `logger.error()`/`.warn()` to Sentry — `.log()`
(the `LOG_ENTER`/`LOG_EXIT` convention used ~360 places) stays console-only, so routine tracing never floods
the Sentry quota. Every `Sentry.init()`/`\Sentry\init()` across all 7 repos sets `sendDefaultPii: false` plus a
`beforeSend`/`before_send` hook that scrubs known secret-key-name patterns from request data/headers/extra
context — a deliberate hardening layer given this workspace's own confirmed plaintext-secret exposure paths
(payment gateway credentials, per-tenant DB passwords, live API keys — see §6). Full env-var and Sentry-project
detail lives in each repo's own `CLAUDE.md`/`knowledge.md`, not repeated here.

**b. The rollout itself briefly broke production** (SAN-76 through SAN-85, ~2-3 weeks of real downtime/degradation
before root cause was found) — three independent, unrelated dependency-vs-runtime mismatches, all surfaced or
caused by the same rollout:
- Two PHP repos (`sc-saas-admin`, `sanchiconnect-saas-tenants-admin`): `composer install` resolves against
  whatever PHP version is on the *local machine running the install*, not the actual deployment target — a
  version mismatch there silently installs incompatible package versions.
- One Node repo: same failure mode, npm-side.
- A `.env` var left blank (present but empty, not absent) passed Joi's `.optional()` check (which only
  tolerates *absent*, not *empty-string*) without `.empty('')` — `SENTRY_DSN` silently stayed unset with zero
  error, so `Sentry.init()` ran with an empty DSN and never sent anything, for both PHP admin repos before this
  was caught (root cause underneath SAN-84/85).
- `instrument.ts` must load `.env` itself (`import 'dotenv/config'` as the literal first line) — `Sentry.init()`
  runs before NestJS's own `ConfigModule.forRoot()` ever executes, so without this the DSN is empty at init
  time regardless of what's actually in `.env`.
- An unanchored `.gitignore` pattern matched a nested vendor path on a case-insensitive filesystem (SAN-81),
  separately.

All of SAN-76 through SAN-85 are fixed and were pushed in earlier sessions this week (not part of this
session's uncommitted work) — flagged here only so a future session doesn't re-diagnose a solved incident from
scratch.

**c. Sentry MCP connected** (`claude mcp add --transport http sentry https://mcp.sentry.dev/mcp`, then `/mcp` →
Authenticate) — this is what made both the incident diagnosis and the 39-issue triage pass below possible
without manual dashboard screenshots. Tools available: `find_organizations`/`find_projects`, `search_issues`,
`get_sentry_resource` (full event detail: stack trace, HTTP request, tags), `update_issue`
(resolve/resolvedInNextRelease/ignore/unresolved). **This connection is not durable across sessions** — it
silently expired mid-session on 2026-07-30 (both Sentry and Linear MCP did) and needed manual re-authorization
via `/mcp` before work could continue; a future session hitting `MCP server requires re-authorization` on
either connector should treat that as expected/recoverable, not a sign the integration was removed.

**d. All 39 then-unresolved Sentry issues were bulk-imported into Linear** (2026-07-30) as `SAN-87` through
`SAN-125`, one Linear Project per Sentry project ("Sentry Issues: `<repo>`"), Sentry's severity mapped to
Linear priority. **e. Then, in the same session, every one of those 39 issues was individually investigated
and resolved** — root-caused against the real Sentry event payload (not guessed), fixed in code where the
finding was a genuine bug, marked resolved/ignored/canceled in both Sentry and Linear with a comment explaining
why, and Linear-Canceled (not code-fixed) where the finding was environmental/non-actionable noise rather than
a defect. **All code changes were held as uncommitted working-tree changes through a full user review pass**
(per [[feedback_commit_push]]), which itself caught two real regressions before they shipped: an `!empty()`
guard in `sc-saas-admin` that would have blanked a legitimately-₹0 program amount (fixed to `isset()`), and an
overly-broad `catch` in `sc-saas-frontend` that silently swallowed genuine backend 500s alongside the expected
404 (narrowed to only silence the 404 case). After that review, every fix was committed to a dedicated branch
per repo (`fix/sentry-logger-error-object-gap` for `sc-saas-backend`, `fix/sentry-issues-2026-07-30` for the
other three touched repos — see [[feedback_developer_guide_mandatory]] for why per-repo branching is now a hard
rule, not optional), merged `--no-ff` into `ai_native_setup`, and pushed. All 30 code-fixed Linear issues moved
to Done; the 3 environmental/non-actionable ones (SAN-109, SAN-122, plus the 3 `ai-startups-analyzer` ones)
stayed Canceled; SAN-123 (HammerJS, needs a new npm dependency) stayed in Backlog on purpose. Patterns found,
several recurring across multiple repos:

- **`sc-saas-backend` (10 issues, all resolved).** `SentryLoggerService.error(msg, err)` was dropping the
  `Error` object before forwarding to Sentry — fixed to use `captureException` when one is present, so future
  backend errors actually carry a stack trace. Five separate cron jobs (`meeting-reminder`,
  `pending-program-application-reminder`, `startup-recommendation-to-investor`, `connection-remainder-2`,
  `milestone-notifications`) crashed on unguarded access after a `LEFT JOIN` that can legitimately return null
  (a deleted user, a startup owned by a team-member sub-account, a startup with no financials/pitch-deck yet)
  — one of these (`meeting-reminder`) never marked the record processed on failure, so it retried and re-failed
  every ~4 minutes forever (332+ events); all five fixed with null-guards, and the permanent-data-problem cases
  now mark themselves handled instead of retrying. `GlobalExceptionFilter` was forwarding *every* exception to
  Sentry including deliberately-thrown 4xx `HttpException`s (a normal "not found" 404 is not a bug) — fixed to
  only forward `statusCode >= 500`, closing 4 issues at once. `FetchCountGateway.handleConnection()` registered
  a new `server.engine.on('initial_headers'/'headers', ...)` listener on *every client connection*, an
  unbounded EventEmitter leak — fixed by moving registration to `afterInit()` (fires once). One genuine
  environmental one-off (S3 `SignatureDoesNotMatch`, single local-env occurrence, likely clock skew) and two
  AWS-SDK deprecation console notices (non-actionable, ignored forever in Sentry) needed no code fix.
- **`sc-saas-admin` + `sanchiconnect-saas-tenants-admin` (9 issues combined, all resolved).** Both PHP admin
  repos' `Sentry\init()` had no `error_types` set, so the SDK wrapped *every* PHP error level — including
  routine `E_WARNING`/`E_NOTICE`/`E_DEPRECATED` from normal rendering — into a full "error"-severity Sentry
  issue; fixed with an explicit `error_types` exclusion in both repos, closing most of these at once. Behind
  that noise, `sc-saas-admin` had 4 genuine first-party template bugs (unguarded nested array access, a
  `foreach()` on a `false` value, two unguarded `$this->amount[...]` reads inconsistent with every sibling field
  in the same file) — all fixed to match this repo's own established `sparkAdminTpl`-has-no-`__isset` /
  local-var-first convention. **The most consequential single finding of this whole pass**: `sc-saas-admin`'s
  "Too many connections" DB-exhaustion issue was actually `.git` reconnaissance scanning — the `.htaccess`
  rewrite rule only skips requests matching an *existing* file/dir, so a probe for a non-existent git ref fell
  through to `index.php`, whose bootstrap opens a DB connection before routing even determines it's a 404; high
  request-volume scanning this way exhausted the connection pool. Fixed by blocking dotfile/dotdir paths with a
  403 at the `.htaccess` level, before PHP or the DB are ever touched (excluding `/.well-known/` so ACME
  renewal isn't broken). **Flagged directly for you, not resolved by this pass**: if `.git` was actually
  readable (not just probed) before this fix, a full commit-history extraction may have succeeded — worth
  confirming from web-server access logs, which this session had no access to.
- **`sc-saas-frontend` (17 issues, all resolved).** The highest-volume single bug this pass found (291 events,
  plus 3 duplicate-grouped variants Sentry hadn't merged): `DynamicFormPreviewComponent`'s template gated
  rendering on `*ngIf="formObject"`, but `formObject` is set synchronously while `dynamicFormGroup` (the actual
  `FormGroup` used by every `[formGroup]` binding and `getFormValues()`) is only built afterward, behind an
  `await`-loop fetching field options — a real timing window rendered the form before its own FormGroup
  existed. Fixed with one gate change: `*ngIf="formObject && dynamicFormGroup"`. Also found: an `ngOnDestroy`
  calling `.unsubscribe()` on a `Subject` before `.complete()` (throws `ObjectUnsubscribedError` — RxJS's
  correct teardown is `.next()` + `.complete()`, no `.unsubscribe()` on the subject itself, confirmed against
  the correct pattern already used elsewhere in this same repo); a backdoor-login flow with no error handling
  at all (a missing route param resolves to the literal string `'null'`, always 404s, and left users stuck on
  a "Logging in..." spinner forever); an async API-response-details method with zero try/catch that treated a
  normal "no application yet" 404/null response as a crash, called from 6 unguarded sites; a `notificationsCount`
  template accessed without the `?.` safe-navigation operator already used correctly two lines above it in the
  same file; an investor-list `.map()` crashing on the same class of empty-join-result bug found independently
  in `sc-saas-backend` that same session. Two issues were **traced but deliberately not code-fixed**: an NG0100
  `ExpressionChangedAfterItHasBeenCheckedError` is provably a dev-mode-only diagnostic (Angular's
  double-check-and-compare pass that throws it is disabled by `enableProdMode()`, confirmed active only when
  `environment.production` is true, and every event here is tagged `environment: local`) — no evidence it ever
  reaches a real production build; a `status: 0` HTTP failure is a genuine network-layer blip (CORS/DNS/reset),
  not a code defect. One (`NgxImageCropper`/HammerJS pinch-gesture warning) was left open in Linear Backlog on
  purpose — real fix needs a new npm dependency (`hammerjs` + `HammerModule` wiring), out of scope for a
  bug-fixing pass, your call whether it's worth adding.
- **`ai-startups-analyzer` (3 issues, all closed, no code fix).** All three were the same known, pre-existing,
  deferred local-dev MySQL connectivity issue (see [[project_ai_analyzer_specs_done]]) — Sentry-ignored
  (`untilEscalating`, so a genuine regression would still surface) and Linear-Canceled with that context.

**What this enables next** (not yet done, listed so a future session doesn't have to rediscover the
opportunity): the `error_types` fix pattern applied to both PHP admin repos this pass is a genuinely reusable
finding — worth a quick check of whether any *other* Sentry-instrumented repo has the same "capturing
everything, including expected noise" problem before it accumulates 39 more issues. The async-timing bug class
found in `sc-saas-frontend` (`*ngIf` gated on a proxy field instead of the actual dependency) is a pattern worth
a targeted sweep across the other ~50 dynamic-forms-adjacent components in that repo, since this pass only
looked at the ones with filed Sentry issues, not the whole surface area. The `.git`-exposure fix in
`sc-saas-admin` should be spot-checked against the other 6 repos' web-server configs — none of them were
audited for the same rewrite-rule gap this session, since the bug was found via a specific Sentry event, not a
systematic scan.

---

## 13. Second Sentry wave (2026-07-31 → 2026-08-03) — a platform-wide live incident, ~90 more issues triaged, a real access-control gap closed, and a cross-2-repo CSS consolidation

Picking up where §12 left off. §12 covered the Sentry rollout itself and its first 39-issue triage pass
(SAN-87 through SAN-125). This section covers everything since: a second, larger Sentry sweep (36 newly
unresolved issues at the time, filed as SAN-126 through SAN-221), a genuine live production incident found
mid-sweep, and two unrelated pieces of debt cleared alongside it (SAN-27, SAN-68). As with §12, treat
anything marked Done below as already root-caused and fixed — don't re-diagnose it.

**a. `sc-saas-backend` (SAN-126, SAN-138, SAN-143, SAN-154, SAN-189, SAN-190, SAN-191/192/193, SAN-194,
SAN-195/196 — all Done except SAN-189, parked Backlog).** Recurring theme: unguarded access after a
`LEFT JOIN`/optional field can legitimately be null or absent, same class as §12's cron-job findings.
`checkUsersOnline()` had an off-by-one (`<=` against `.length`) that read one element past the array end,
producing `undefined`/empty values passed straight through to `sc-saas-3rdparty-webservices`'s comet-chat
proxy — which is why one backend bug manifested as two different-looking Sentry issues in a downstream repo
(SAN-195/196, both closed by the same one-line fix). `getProfileDataByEmailOfGuestUser` silently overwrote
earlier form answers sharing a duplicate field label ("LinkedIn URL", "Other", etc.) — three separate Sentry
issues (SAN-191/192/193), one root cause. **SAN-189 (Handlebars template parse error breaking the bulk
pending-connection-reminder email) is a real functional bug, deliberately left in Backlog** — the crash was
wrapped in try/catch so it fails gracefully instead of crashing the cron, but the underlying malformed email
template still needs an admin-side content fix, out of scope for a code-only bug-fix pass.

**b. `sc-saas-frontend` (the large majority of SAN-126–221 — dozens Done, several deliberately parked).**
Same "optional chaining missing" pattern recurred across many components (`auth.guard`, dashboard-v2,
startup-information edit, startup-public-profile-v2, investor-dashboard effects, startup-kit-detail,
`getUserTypeArray`, multiple `*Fault` console.warn sites) — all fixed with `?.` guards matching the
already-established convention elsewhere in each file. Confirmed-third-party/unfixable, closed without a
code change after exhaustive grep-for-references verification: 8 "in-app-browser bridge" issues
(SAN-197–204) — `iabjs://`-scheme errors from Instagram/Facebook/TikTok's injected in-app-browser JS, not
this app's code. **Deliberately parked in Backlog, not fixed this pass:**
- **SAN-158 (Urgent) — `thub.sanchidev.in` is serving a non-production Angular build** (`SENTRY_ENVIRONMENT:
  local` in production traffic). Root cause narrowed to Jenkins bypassing this repo's npm build hooks
  entirely (confirmed via an existing code comment in `generate-build-info.js`), but the actual Jenkins job
  config isn't visible from this checkout — needs the CI/infra owner.
- **SAN-159 — capture tenant-verification failures as a fingerprinted Sentry issue + alert rule.** Needs a
  manual Sentry Alert Rule created in the dashboard UI, not something committable as code.
- **SAN-150 (Low) — lightGallery running with the default/invalid license key** (`0000-0000-000-0000`)
  platform-wide. Needs a licensing decision from whoever owns that vendor relationship, not a code fix.
- **SAN-219 — recurring 404 on `/users/profile-types`** across multiple tenants, regressed. Investigation
  pending SAN-158's Jenkins fix (suspected same root cause — a stale/dev build not carrying a route that
  exists in the real source).
- **SAN-221 — Sentry source-map upload wired up but not shipped.** `scripts/upload-sourcemaps.js` was
  written and verified end-to-end against a real production build (real `.map` files generated, real
  Sentry 401 on a fake token, correctly skips file deletion on failure) — but per SAN-158's finding above,
  a `postbuild` npm hook alone won't run under this repo's actual CI, so this needs an explicit Jenkins
  pipeline step + a real `SENTRY_AUTH_TOKEN` added to CI before it does anything in production. Also still
  open: SAN-160–166 (NG0100 `ExpressionChangedAfterItHasBeenCheckedError`, all in Todo, likely blocked on
  the same SAN-158 build-config investigation) and SAN-168–184 (17 webpack-dev-server compile-warning
  events — confirmed dev-server-only noise, not production-relevant, left in Todo rather than closed since
  they're harmless but not actioned either).

**c. `sc-saas-admin` + `sanchiconnect-saas-tenants-admin` (SAN-127, SAN-136/137, SAN-155 — all Done).** Same
`error_types`-noise class as §12. One genuine content-leak bug: `sc-saas-admin`'s auto-generate-AI-thesis
flow forwarded the analyzer service's raw HTTP response body (including e.g. a raw nginx 502 HTML page)
straight into the user-facing error message — fixed to show a generic message and log the raw body
server-side instead.

**d. `ai-startups-analyzer` (SAN-186, SAN-187 — Done).** A thesis-generation timeout and a Gemini quota
error were both leaking the raw provider exception into the API response — fixed to return a generic
message. **Separately confirmed (not a code bug):** the underlying Gemini quota exhaustion traces back to
the linked Google Cloud Billing account being fully closed (not just a payment-method issue) — reopening it
is a Google Cloud Console action outside what this session can do; flagged to the user directly.

**e. The live incident — SAN-188, `verify_tenant` intermittent 504s across many tenants.** What first looked
like a single-tenant issue (`hub.startupsingam.com`) turned out, on checking the raw Sentry event data
directly rather than assuming, to be hitting many unrelated tenant hostnames simultaneously, including
explicit 504 Gateway Timeouts — a platform-wide incident, not a one-off. Root cause: `global.service.ts`'s
tenant-lookup query uses a **leading-wildcard `LIKE '%hostname%'`** on `tenant.customDomain`/`tenant.domain`,
which cannot use a B-tree index (the wildcard prefix defeats index range-scanning), forcing a full table
scan on every single tenant-verification request platform-wide. **Fix shipped (safe-first, user's explicit
choice over the more invasive query-tightening option): added `@Index()` to `domain`, `customDomain`, and
`active` on `TenantUsersEntity`** (`sanchiconnect-saas-tenants`, commit `f66114b`) — zero semantic change to
the query itself, so this is a pure performance mitigation, not a behavior change. **The query logic itself
(the leading-wildcard `LIKE`) is deliberately left untouched and SAN-188 stays in Backlog** — tightening it
to an exact/anchored match is a real behavior change (could reject a currently-matching subdomain pattern)
that needs a design decision, not a quick fix, and the same query is the suspected root cause of the
still-open SAN-219 (frontend 404s) too. **Caveat on the index fix's durability:** every repo in this
workspace has `synchronize: true` with no formal migrations (see §5) — a schema-touching deploy could
silently drop this manually-added index on next restart; worth confirming this specific risk before
treating SAN-188 as durably closed.

**f. SAN-27 — a real access-control gap, closed.** `sc-saas-admin`'s `task_management` module
(`list.php`/`create.php`/`edit.php`/`details.php`) checked only `checkLoggedIn()` — none of the four routes
enforced the `task_management` tenant flag despite it existing and being read elsewhere (the dashboard
widget). A tenant with the flag explicitly disabled had full CRUD access to the module anyway. Fixed by
adding the repo's own established gate pattern (`if ($brandSettings['task_management'] == 0) { redirect to
/403 }`) to all four handlers, verified via `php -l` + a targeted grep confirming none of the four files are
`include()`d elsewhere as partials (ruling out an unexpected execution context for the new `exit()` call).
**Residual, smaller gap left open on purpose:** the sidebar nav entry still has no `feature_key`, so a
disabled tenant can still click into the module and land on `/403` — a missing UI affordance, not a missing
enforcement, and out of SAN-27's scope. `sc-saas-admin/modules/task_management/module.spec.md` is updated to
match (previously it documented the pre-fix state as an open "real gap" — now corrected).

**g. SAN-68 — the `aic-` CSS system, deduplicated across 2 repos, with a genuine second-pass catch.** The
`aic-` prefixed design system (built for AI Credits, reused in `finance_management`) was redefined inline,
near-duplicated, across 14 templates in `sc-saas-admin` (4 files, byte-identical, clean extraction) and
`sanchiconnect-saas-tenants-admin` (10 files, real drift: 5 different card-margin values, a font-size fork
between `ai_credits`/`finance_management`, one outright class-name collision). Consolidated into one shared
stylesheet per repo (`themes/default/assets/css/ai-credits-shared.css`, wired into each repo's existing
`header.php` CSS-bundling array), with real 576/768/992/1200 breakpoints added (none existed before —
confirmed via grep, only `@media print` rules existed anywhere in these files). Two things that are
per-tenant PHP-templated (not static CSS) correctly stayed inline: the `:root{--aic-primary...}` color block,
and — found only by reading the file's exact literal content rather than trusting a first-pass summary — a
second, easy-to-miss dynamic rule (`.aic-mhd`'s modal-header gradient), refactored to consume a new
`--aic-primary-75` CSS var so it too could become static. **A first review pass (selector-coverage only)
looked clean; a second, property-by-property diff against every page's pre-edit declarations caught 3 real
regressions the first pass missed** — a class-name collision leaking `uppercase`/`letter-spacing`/`display`
into 6 form labels on one page, a wrong canonical CSS-variable pick in a shared modal rule, and one page's
card-margin override that was simply forgotten. All three fixed and re-verified before shipping.
`finance_management/invoice_view.php` was deliberately left untouched — a wholesale-forked design system
(`--pc`/`iv-`/`inv-` naming, different alphas, uppercase badge suffixes), never a clean duplicate of the
`aic-` system to begin with. **Lesson for future consolidation work in this workspace:** a selector-only
diff is not sufficient to prove "nothing changed" — verify property-by-property against the pre-edit
original, not just "does every class still resolve somewhere."

**What's still open, for a future session to pick up rather than rediscover:** SAN-158/159/219/221 (frontend,
all blocked on Jenkins/infra access this session didn't have), SAN-150 (licensing decision), SAN-188 (query
redesign decision, index-only fix shipped), SAN-189 (admin-side email template content fix), SAN-140 (older
MySQL connection-pool issue, needs an infra decision, parked in an earlier session), SAN-160–166 (NG0100,
likely resolves alongside SAN-158), SAN-168–184 (webpack dev-noise, harmless).

---

## 14. Startup ID Creation Module + Digital ID Card (2026-08-12/13) — a full feature built end-to-end across all 3 core repos, 3 real flag-gating gaps found and closed, and one confirmed-still-open data gap

SAN-253/257 (Startup ID Creation Module) and its Digital ID Card feature, plus the related SAN-312/313/314/317
Location Master removal-and-replacement work, were built end-to-end this session across `sc-saas-admin`,
`sc-saas-backend`, and `sc-saas-frontend`. This section is the workspace-level map of what now exists, the
real bugs found along the way (several independent of each other), and what's still genuinely open — read
this before re-investigating any of the below from scratch.

**a. What exists now, per repo.**
- **`sc-saas-admin`**: Format Builder (drag-and-drop segment composer — COUNTRY_CODE/STATE_CODE/YEAR/
  DISTRICT/SUB_DISTRICT/SPOKE/SERIAL_NO segments, live sample preview, delimiter config), Card Design Builder
  (layer-based front/back template editor — `static_asset` + `bound_field` layers, drag-to-position, S3
  asset upload), and a Settings page (the tenant's `startup_recognition_enabled` toggle plus a Country/State
  Code panel that upserts the single `state_master` row and wires it into
  `startup_recognition_id_config.state_master_id`). Location Master Import gained file-upload support (not
  just Source URL), an async detached-CLI-worker architecture (mirroring
  `cli/regenerate_startup_recognition_ids.php`'s own established pattern), and an O(n) hash-indexed matching
  rewrite replacing an earlier O(n²) per-row-SQL approach the user explicitly rejected mid-session ("i think
  its not a good approach"). `[Source: sc-saas-admin/modules/startup_recognition_management/module.spec.md,
  sc-saas-admin/modules/developer/module.spec.md]`
- **`sc-saas-backend`**: `GET /startups/digital-id-card` (new endpoint, `StartupService.getDigitalIdCard()`),
  District/Sub-District segment resolution (`resolveCityDistrictContext()`, new `DistrictsRepository`/
  `SubDistrictsRepository`), and the round-entry generation trigger in `program-management.service.ts`.
  Deliberately has **no controller** for the format-config/card-template/state-master data itself — those
  stay admin-configured, read/written directly by `sc-saas-admin`'s own Medoo connection, the same
  established pattern as `id_cards`/`master_data` elsewhere in this codebase. `[Source:
  sc-saas-backend/src/modules/startup-recognition-id/module.spec.md]`
- **`sc-saas-frontend`**: a new `AccDigitalIdCardComponent` (`/account/edit/digital-id-card`) rendering the
  admin-designed card as a generic layer list, with Download-as-Image/PDF via `html-to-image` + `jsPDF`, and
  a new recognition-ID eligibility gate on program applications (`ProgramPublicApplyComponent`).
  `[Source: sc-saas-frontend/src/app/modules/account/module.spec.md,
  sc-saas-frontend/src/app/modules/programs/module.spec.md]`

**b. Real, independent bugs found and fixed this session** (beyond ordinary feature-building):
- **A NestJS boot-time DI crash-loop**: `ProgramsManagementModule` duplicates `StartupRecognitionIdGenerationService`
  as a raw provider (an established pre-existing pattern in this codebase, not something this session
  introduced) but was missing `CitiesRepository`/`DistrictsRepository`/`SubDistrictsRepository` once those
  became new constructor dependencies — crash-looped the live backend in production until fixed.
- **Two independent `html-to-image` export bugs on the frontend**: (1) the library throws trying to read
  `.cssRules` off cross-origin stylesheets (Google Fonts etc.) while embedding web fonts, silently blocking
  the whole PNG/PDF export — fixed with `skipFonts: true`. (2) The library doesn't reliably respect
  `border-radius`/`overflow:hidden` clipping from the source DOM at a scaled `pixelRatio` — both the outer
  card boundary AND each individual layer's own rounding had to be re-applied by hand on the exported bitmap
  via a `destination-in` canvas composite, not trusted to the library.
- **A resolution-mechanism inconsistency in `sc-saas-admin`'s regenerate-all flow**: `srIdRegenerateAll()`
  resolved `state_master` from each startup's own stale `state_id` column (only ever an *output* of a prior
  generation, so `null` until a startup has successfully generated at least once) instead of from
  `startup_recognition_id_config.state_master_id` like fresh generation correctly does — so a format-change
  regenerate silently produced no visible change for any startup that had never yet resolved a state_master,
  even after the tenant properly configured one. Fixed to resolve once from the config, matching fresh
  generation, and to write `state_id` back onto the startup row for consistency going forward.
- **A missing template variable hid an entire admin UI section**: `modules/startup-detail.php` never set
  `$tpl->brandSettings` (only `modules/common.php` sets it globally, and this specific module never inherited
  that instance correctly) — since `sparkAdminTpl` has no `__isset()`, the view's
  `isset($this->brandSettings[...])` check silently evaluated false regardless of the real tenant flag,
  hiding the whole "Startup Recognition ID" panel on every startup's detail page for every tenant, flag on or
  off. One line fixed it; confirmed via a temporary inline HTML debug comment (added and removed same
  session) rather than guessed.
- **Font Awesome version mismatch**: two new segment-type icons (`fa-map-marker-alt`, `fa-calendar-alt`) used
  Font Awesome 5 class names in a codebase running FA **4.7.0** — silently failed to render (no error, just a
  missing icon), producing inconsistent tag spacing that read as "alignment broken" rather than "wrong icon
  library." Verified the fix's replacement names (`fa-map-marker`, `fa-calendar`) actually exist in this
  project's specific vendored `font-awesome.min.css`, not assumed from memory.
- **Missing `uuid` on two new raw-Medoo inserts**: `state_master` and `startup_recognition_id_config` are
  TypeORM entities with a JS-side `@BeforeInsert()` uuid generator that only fires through TypeORM — any
  insert via this repo's own PHP/Medoo connection bypasses it entirely. This repo has an established
  `gen_uuid()` convention for exactly this situation (already used correctly elsewhere in this same module,
  e.g. `format_builder.php`'s regeneration-log insert) that the two new insert sites simply missed. Fixed
  with both a forward fix (set `uuid` on insert) and a backfill (set it on update too, if still missing on an
  existing row) — the general fix shape worth knowing about if any *other* new insert against a TypeORM
  entity table is ever added from this repo's PHP side.
- **Three real server-side flag-gating gaps, found by a dedicated adversarial audit** (see §c below):
  `format_builder.php` (`previewFormat`/`getAffectedCount`/`saveFormat`), `card_design_builder.php`
  (`uploadAsset`/`saveTemplate`), and `settings.php`'s `saveStateMaster` were all gated only by
  `srIdCheckRole(true)` (a role check), never re-checking `startup_recognition_enabled` (the tenant flag)
  server-side — despite each page's own UI hiding itself when the flag is off, a Developer Admin on a
  flag-off tenant could reach any of these by direct POST and mutate `startup_recognition_id_config`,
  `state_master`, or `digital_id_card_template`, or upload arbitrary S3 assets, for a feature the tenant
  hasn't enabled. This is the exact "checked at render time, not re-validated on the POST handler" bug class
  this same module's own code comments already warn about elsewhere (a pattern this workspace's module-spec
  sweeps — see §10 — have found repeatedly across multiple repos). Fixed with the same explicit
  `if (empty($brandSettings['startup_recognition_enabled']) || ...) { exit; }` check already used correctly
  in `edit_program_round.php`'s `generate_recognition_id` handler and `startup-detail.php`'s
  `generateStartupRecognitionId` handler — added alongside the existing role check, not in place of it,
  matching this repo's own established defense-in-depth convention (role checks are similarly duplicated
  file-level + per-handler throughout this module).

**c. A dedicated cross-repo flag-gating audit was run before calling this feature done**, prompted directly
by a user request ("check all the updates... are gated with tenant key startup_recognition_enabled... so
that any existing functionality not broken for any existing client"). Three parallel agents, one per repo,
each verified every SR-ID/Digital-ID-Card code path added this session:
- `sc-saas-backend`: **0 gaps** — `getDigitalIdCard()` checks the flag first, before touching any
  repository; the only caller of `generateForStartup()` (`program-management.service.ts`'s `updateRound()`)
  gates on the flag before ever calling it; the DI fix and base64-asset fix are both flag-independent
  wiring/downstream changes with no behavioral effect of their own.
- `sc-saas-frontend`: **0 gaps** — the nav entry requires both `ACCOUNT_TYPE.STARTUP` and the flag; the route
  itself has no flag guard (consistent with this repo's documented "no route-level flag guard, ad hoc per
  component, backend is the real gate" convention) but the component degrades gracefully via `data.enabled`
  on direct-URL access; one confirmed benign detail — a flag-off tenant landing on the URL directly still
  fires one API call that the backend safely no-ops, not a functional gap.
- `sc-saas-admin`: **3 real gaps found and fixed** (see §b above). Also confirmed, as an explicit product-
  scope finding rather than a bug: the new `freeze_applications` round toggle is *intentionally*
  flag-independent (a generic round-freeze concept, no "unfreeze" UI, direct DB edit only for correction) —
  meaning flag-off tenants DO get one genuinely new capability (the ability to freeze a round and have that
  block Kanban drag-and-drop, both client- and server-side) that didn't exist before this session. This is a
  deliberate scope decision this audit surfaced for confirmation, not something the audit itself judged right
  or wrong.

**d. Still genuinely open — a real data gap, not a code bug.** District/Sub-District ID segments resolve to
empty for every real startup today, and this is **confirmed structural, not a missing feature**: a real
source file (`location-master-final.json`, checked directly) has 150,541 city records with `state_id`/
`country_id` but **zero** have `district_id`/`sub_district_id` populated — there is currently no data
anywhere in this workspace linking a city to a district/sub-district, for any city. Separately, real LGD
(Local Government Directory) district/sub-district codes are numeric (e.g. district code `603`, sub-district
code `2925`), not short letter abbreviations like the "GOM"/"UDPR" reference example used during this
session's requirements discussion — that reference was always an illustrative mockup, not a literal target
once real government data is involved. Closing this gap needs either a real city→district/sub-district
mapping data source (none currently available) or a scoped, explicit product decision to source/enter it
for a smaller subset (e.g. one tenant's own state) — flagged back to the user rather than fabricated.

---

## Change Log

- 2026-08-13 | Added §14 — the Startup ID Creation Module + Digital ID Card feature (SAN-253/257, plus the
  related SAN-312/313/314/317 Location Master removal-and-replacement), built end-to-end across all 3 core
  repos this session. Seven independent real bugs found and fixed along the way (a NestJS boot-time DI
  crash-loop, two separate `html-to-image` export bugs, a state_master resolution inconsistency in the
  admin's regenerate-all flow, a missing template variable that silently hid an entire admin UI section
  regardless of the tenant flag, a Font-Awesome-version icon mismatch, and a missing `uuid` convention on two
  new inserts). A dedicated 3-agent cross-repo flag-gating audit (prompted by explicit user request) found
  backend and frontend fully clean, but 3 real server-side flag-gating gaps in `sc-saas-admin`
  (`format_builder.php`, `card_design_builder.php`, `settings.php`'s `saveStateMaster` — role-checked but
  never re-checking the tenant flag, the same "checked at render, not on the POST handler" class §10 already
  flagged elsewhere in this workspace) — found and fixed. One real, confirmed-open data gap remains:
  District/Sub-District segments resolve empty for every real startup, traced directly to zero of 150,541
  real city records anywhere in this workspace having a district/sub-district link — a genuine missing data
  source, not a code defect, flagged back to the user rather than fabricated.
- 2026-08-03 | Added §13 (second Sentry wave, 2026-07-31→2026-08-03): ~90 more Sentry-sourced issues triaged
  (SAN-126–221) across all repos, the SAN-188 platform-wide `verify_tenant` 504 incident (root cause + a
  safe-first index fix, query redesign deliberately deferred), SAN-27 (a real access-control gap in
  `sc-saas-admin`'s `task_management` module, closed), and SAN-68 (the `aic-` CSS system deduplicated across
  `sc-saas-admin` + `sanchiconnect-saas-tenants-admin`, including a second review pass that caught 3 real
  regressions a first, selector-only pass had missed). Corrected `sc-saas-admin`'s
  `modules/task_management/module.spec.md`, which had documented SAN-27's bug as an open "real gap" — it now
  reflects the fix. This catch-up pass was itself prompted by a direct user question ("are you updated the
  spec knowledge... what we have build in last 2 weeks?") that surfaced the gap: this document, all 7
  `specs/*-module-specs-index.md` files, and an unknown number of individual module specs had drifted stale
  against ~2 weeks of real commits (verified via `git log` across all 7 repos + a Linear query against actual
  current issue states, not assumed from memory).
- 2026-07-30 (final update this day) | The §12 Sentry fix pass shipped: after a full review pass (which caught
  2 real regressions before commit — see §12), all 4 touched repos' fixes were committed to a dedicated
  per-repo branch, merged `--no-ff` into `ai_native_setup`, and pushed — `sc-saas-backend`
  (`fix/sentry-logger-error-object-gap` → `4084661f`), `sc-saas-admin` (`fix/sentry-issues-2026-07-30` →
  `a5e4ad79`), `sanchiconnect-saas-tenants-admin` (`fix/sentry-issues-2026-07-30` → `2b2e1ac`),
  `sc-saas-frontend` (`fix/sentry-issues-2026-07-30` → `5da9e5cf`). All 30 code-fixed Linear issues moved
  Backlog/In Review → Done to match. §12's body text above is updated to reflect this shipped state rather
  than "uncommitted."
- 2026-07-30 (later same day) | User confirmed the 10-step Developer Guide loop (§77-93 of the workspace
  `CLAUDE.md`'s "Specs" section, adopted 2026-07-27) is mandatory for **every** task/issue, not just
  spec-driven feature work — prompted directly by this session's own Sentry 39-issue fix pass (§12) not
  fully following it (no per-repo branches for 3 of 4 repos touched, no automated tests added, no Gap
  Register update). Codified into `CLAUDE.md` with an explicit "Standing process" subsection spelling out
  all 10 steps and clarifying that the lightweight `/bug-fix` path still requires branching-per-repo and
  Linear-state updates — "lightweight" only exempts the feature-spec document and Gap Register ceremony, not
  verification or version control hygiene. Also clarified this applies to batch fix passes (many small
  issues in one session), not just single large features — no blanket exemption for volume.
- 2026-07-30 | Added §12 — full Sentry.io observability rollout across all 7 repos (errors/perf on all,
  structured Logs only where the SDK supports it, CaptureConsole substitute elsewhere), the real multi-week
  downtime incident it caused/surfaced (SAN-76→85, three independent PHP/Node dependency-vs-runtime
  mismatches, already fixed in earlier sessions), the Sentry MCP connection (confirmed non-durable — expired
  mid-session once already), the bulk import of all 39 then-unresolved Sentry issues into Linear
  (SAN-87→125), and this session's full triage pass resolving every one of them — 22 real code fixes across
  `sc-saas-backend`/`sc-saas-admin`/`sanchiconnect-saas-tenants-admin`/`sc-saas-frontend` (all uncommitted,
  awaiting manual review), plus honest no-fix closures for genuinely non-actionable/environmental findings.
  Single most consequential finding: `sc-saas-admin`'s DB-connection-exhaustion issue was actually `.git`
  reconnaissance scanning exploiting a rewrite-rule gap — fixed, but full-history exposure isn't ruled out
  and needs a manual web-server-log check this session couldn't perform. Listed 3 concrete next-step
  opportunities the pass's findings point to but didn't cover (the `error_types`-noise pattern, the
  async-timing-race pattern, and the `.git`-exposure pattern, each worth a wider sweep beyond just the repos
  that happened to have a filed Sentry issue).
- 2026-07-20 | Added §11 — closed the last remaining module-spec gaps workspace-wide (101 new
  `module.spec.md` files across 4 sessions: 38 in `sc-saas-admin`, 3 in `sc-saas-backend`, 52 in
  `sc-saas-frontend`, 2 in `sanchiconnect-saas-tenants`, 6 in `sanchiconnect-saas-tenants-admin`), and
  regenerated (or, for `sanchiconnect-saas-tenants-admin`, created for the first time) all 7 repos'
  module-specs-index files, independently re-verifying 0-gap coverage in every repo along the way. Added 6
  new §6 security bullets from findings surfaced during this final sweep, the most severe being
  `sanchiconnect-saas-tenants-admin`'s completely unauthenticated `csv/export.php`/`import.php` (full DB
  dump/insert on the shared platform DB, tracked as Linear SAN-42, still unfixed) — arguably the single
  worst finding across this entire multi-session audit effort.
- 2026-07-17 | Added §10 and new §6 security bullets — synced this root synthesis with the module-level
  (`module.spec.md`, all 139 files across 7 repos) re-verification and adversarial re-verification passes
  done in the individual product repos (committed to their own `ai_native_setup` branches). Most
  consequential: two separate repos (`sc-saas-admin`, `sanchiconnect-saas-tenants-admin`) each have an
  ungated `sql_query` arbitrary-SQL-execution action; `facility_management`'s authenticated routes aren't
  actually feature-gated; `ecosystem-facilities` silently can't do External Hub lookups; a real
  `shortIo` accept/reject URL swap bug; and the methodology finding that an adversarial re-check of modules
  previously marked "verified accurate" found real gaps in 16 of 18 (89%) sampled — meaning most of the
  ~125 originally "no changes" modules workspace-wide are still unverified beyond a demonstrated-unreliable
  single pass.
- 2026-07-16 (later same day) | Added §9 — enumerated the SanchiPowerpitch sibling workspace's four repos by
  name (previously only `power-pitch-sanchiconnect-api` was named anywhere in this workspace's docs), confirmed
  its location on disk, and corrected a wrong claim from this workspace's repo-map reference doc (2026-07-15)
  that `power-pitch-sanchiconnect-admin` had no meaningful commits — it has 12, dated 2022-2023, just no
  activity since then until a docs-only commit in 2026-06.
- 2026-07-16 (later same day) | Full re-verification pass across all 7 repos' own `knowledge.md`/`design.md`/
  `database.md`/`api.md` (28 files), not just this workspace-level synthesis — one dedicated agent per repo,
  each re-checking every specific claim against current code and fixing confirmed drift directly. Net effect:
  dozens of precise counts/line-citations corrected (mostly drift from same-day commits shifting line numbers,
  not conceptual errors), and two genuinely new findings worth surfacing at this level: (1) `sc-saas-admin`
  shipped a **Bulk Email Attachments** feature (2026-07-15, after the original 2026-07-14 pass) with S3
  upload/inline-vs-link delivery but **no malware-scanning provider wired up** — every attachment is
  permanently `PENDING` scan status and sends proceed anyway, an accepted product decision, not a bug, but
  worth knowing platform-wide; (2) `sc-saas-3rdparty-webservices` actually exposes **34 routes, not 20** as
  every doc previously stated, and has a real, confirmed config-wiring bug — `OTP_EXPIRATION_TIME_IN_MINUTES`
  is required at boot (Joi) but `configuration.ts` never maps it to the key `AppConfigService.otpExpirationTime`
  reads, so the env var silently has zero effect and `sms.service.ts` always uses its hardcoded 10-minute
  fallback. See each repo's own docs for full detail; not deep-diving either into this synthesis since both are
  single-repo findings without a second-repo consumer.
- 2026-07-16 | Independent re-verification pass: spot-checked 6 of this document's most load-bearing claims
  directly against current code (not re-trusted from the 2026-07-14 synthesis alone) — all 6 confirmed exactly
  as stated: `sc-saas-admin`'s two direct `sc-saas-3rdparty-webservices` call sites (§3.1), the
  `easebuzz_callback.php` direct call into `sanchiconnect-saas-tenants` (§3.1), `sanchiconnect-saas-tenants-admin`'s
  two direct `sc-saas-backend` calls (§3.2), the bundled Adminer console with the plaintext DB-password link
  (§6), the 5-of-6 AJAX-handlers-skip-login finding (§6), and the hardcoded live-looking API keys in
  `global.repository.ts` (§6). **One correction**: the ai-credits Easebuzz webhooks are gated by
  `InternalApiKeyGuard` *and* HMAC signature verification — not unauthenticated as `sanchiconnect-saas-tenants`'s
  own `CLAUDE.md` stated until this pass (now fixed there). Also fixed 5 other confirmed-stale numbers this
  pass surfaced across per-repo `CLAUDE.md` files that this July 14 synthesis had already flagged internally
  but which hadn't propagated to the actual `CLAUDE.md` files themselves: `sc-saas-backend` module count
  (51→58), `sc-saas-frontend` NgRx store count (~38→34), `sc-saas-3rdparty-webservices`'s Swagger-gate
  condition and "called only by backend" framing, and `sanchiconnect-saas-tenants-admin`'s standalone/JWT/SendGrid
  claims (§(a) above already refuted these on 2026-07-14; the `CLAUDE.md` files themselves weren't corrected
  until now). Added `sanchiconnect-saas-tenants-admin`'s new Tenant Data Export feature (built this session,
  see that repo's own `knowledge.md` §h) as a new architectural data point.
- 2026-07-14 | Initial workspace-level synthesis pass. Read all seven repos' `knowledge.md` in full, plus
  spot-checked `design.md` (tenants, frontend — the two `verify_tenant`/`tenant-settings` breakage traces)
  and `database.md`/`api.md` section headers across all seven repos to confirm structure before citing.
  Connected the AI-Credits three-mutator finding across `sanchiconnect-saas-tenants`, `sc-saas-admin`, and
  `sanchiconnect-saas-tenants-admin`. Connected the three call-graph contradictions
  (`sc-saas-3rdparty-webservices`, `sanchiconnect-saas-tenants-admin`, `sc-saas-admin`'s undocumented
  fourth-repo call) into one corrected call-graph table. Stated the four-way tenancy-model split as a
  platform architectural fact. Consolidated six independently-surfaced security findings. Confirmed the
  `synchronize: true`/no-migrations pattern is present in both NestJS repos, not a one-off. Confirmed no
  repo has Docker/CI/CD/IaC. Checked the workspace `CLAUDE.md`'s blast-radius graph against all seven
  repos' findings — most of it holds; three specific edges are stale or missing. Existing workspace
  `README.md` was read and found broadly consistent with these repos' own `CLAUDE.md` framing (still
  useful as an onboarding doc) but is stale in one respect: it lists only five/six repos and predates the
  addition of `sanchiconnect-saas-tenants-admin` as a seventh repo — flagged for the maintainer's attention
  in this pass's final report rather than rewritten here, per this task's instruction to be conservative
  with `README.md`.
