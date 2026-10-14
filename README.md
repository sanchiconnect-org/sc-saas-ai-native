# SanchiSaaS

Multi-tenant SaaS platform for startup incubators and accelerators. Built as a **poly-repo** — seven independently-versioned, independently-deployed repositories that together form a single product.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐  ┌────────────────────────────────┐
│  sanchiconnect-saas-tenants  (Control Plane / Cockpit)          │◄─┤  sanchiconnect-saas-tenants-   │
│  Source of truth for feature flags + tenant provisioning        │  │  admin (Platform Operator UI)  │
│  NestJS 9 · TypeORM · MySQL (shared, row-per-tenant)            │  │  PHP · Medoo — reads/writes    │
└────────────┬────────────────────────────┬───────────────────────┘  │  the cockpit DB directly       │
             │ verify_tenant / settings   │ bootstrap config         └────────────────────────────────┘
             ▼                            ▼                            (shares the cockpit DB directly,
┌────────────────────────┐   ┌────────────────────────────────────┐    no API calls between them)
│  sc-saas-frontend      │   │  sc-saas-backend                   │
│  End-user PWA          │◄──│  Business API (REST)               │
│  Angular 13 · NgRx     │   │  NestJS 8 · TypeORM · MySQL        │
│  PWA · TypeScript      │   │  One deployment per tenant         │
└────────────────────────┘   └────┬──────────────────┬────────────┘
                                  │ API calls         │ SMS/email/video
                                  │                   │ chat/URL/docs
                    ┌─────────────▼──────┐  ┌─────────▼──────────────┐
                    │  sc-saas-admin     │  │  sc-saas-3rdparty-     │
                    │  Admin panel (ops) │  │  webservices           │
                    │  PHP · Medoo       │  │  Integration gateway   │
                    └──────────┬─────────┘  │  NestJS 9 · TypeScript │
                               │ scoring    └────────────────────────┘
                    ┌──────────▼─────────┐
                    │  ai-startups-      │
                    │  analyzer          │
                    │  Python · FastAPI  │
                    └────────────────────┘
```

**Blast radius:** `tenants → backend → {frontend, admin}`. `sanchiconnect-saas-tenants-admin` shares the cockpit MySQL DB directly with `sanchiconnect-saas-tenants` — a schema change in one can break both simultaneously — but makes no API calls in either direction. The AI analyzer and the 3rdparty webservices gateway are both leaf nodes — neither calls back into any other SanchiSaaS repo.

---

## Repositories

### 1. `sanchiconnect-saas-tenants` — Control Plane (Cockpit)

**Stack:** NestJS 9 · TypeORM · MySQL (single shared DB, one row per tenant)

The upstream source of truth for the entire platform. It owns two things nothing else may override:

- **Feature flags** — every boolean feature toggle is a column on the `tenant_users` table. The snake_case column name is the contract string that backend, frontend, and admin all reference. Adding, renaming, or removing a flag here must be propagated to all three consumers.
- **Tenant provisioning** — stores per-tenant config including the `apiUrl` of that tenant's backend deployment, database credentials, SMTP settings, and subscription state.

**Exposes two critical endpoints consumed by other repos:**
- `GET /public/global/verify_tenant/:hostname` — called by the frontend on load to get the tenant's brand config, feature flags, and `apiUrl`.
- `GET /public/global/tenant-settings/:hostname` — called by the backend at bootstrap to load its own config and feature flags into memory.

**Connects to:**
- `sc-saas-backend` — backend calls this at startup to bootstrap itself; a cockpit outage prevents backend from starting.
- `sc-saas-frontend` — frontend calls this on every page load to resolve the tenant before making any business calls.
- `sc-saas-admin` — admin reads the cockpit DB directly (via `$mainDatabase`) to look up tenant credentials and select the correct per-tenant database.

> Highest blast radius in the system. A breaking change here can take down backend, frontend, and admin simultaneously.

---

### 2. `sc-saas-backend` — Business API

**Stack:** NestJS 8 · TypeORM · MySQL · JWT auth · AWS S3 / CloudFront

The central REST API that all clients talk to for business data. Owns the API contract — every controller path, HTTP method, request DTO, and response shape is a cross-repo commitment.

**One deployment = one tenant.** There is no tenant column on any entity and no per-query tenant guard. Instead, tenant config and feature flags are loaded once at bootstrap from the cockpit and held in memory for the lifetime of the process. This means each tenant runs their own isolated backend instance pointed at their own MySQL database.

**Key responsibilities:**
- Application management (startups, investors, mentors, corporates)
- Program and round management
- User auth and session management (JWT; optional single-session enforcement)
- File storage via AWS S3 + CloudFront signed URLs
- Feature-gated routes via `@Features([...]) + @UseGuards(FeatureGuard)`

**Connects to:**
- `sanchiconnect-saas-tenants` — reads cockpit at bootstrap via `sanchiconnect.service.ts`; depends on cockpit being reachable on first start.
- `sc-saas-frontend` — frontend discovers the backend's `apiUrl` from the cockpit response and routes all business calls here.
- `sc-saas-admin` — admin calls this API via `api_server_url` for all business operations (application listings, ratings, program management, etc.).

> Changing a controller path, method, or DTO shape is a cross-repo change. Always check frontend services and admin cURL callers before merging.

---

### 3. `sc-saas-frontend` — End-User PWA

**Stack:** Angular 13 · NgRx 13 · TypeScript · Service Worker (PWA) · npm

The end-user-facing Progressive Web App. Serves cohort members, startup founders, investors, and mentors. Installable as a PWA on mobile and desktop.

**Startup sequence:**
1. On load, calls the cockpit `verify_tenant` endpoint using `location.hostname` to identify which tenant is being accessed.
2. Receives `IBrandDetails` — contains branding, the `features` map (feature flags), and the `apiUrl` of this tenant's backend.
3. Dispatches brand details to NgRx global store and localStorage.
4. All subsequent business calls go to the backend at that dynamic `apiUrl`.

This means the same frontend build serves every tenant — the tenant is resolved at runtime from the hostname, not baked in at build time.

**Connects to:**
- `sanchiconnect-saas-tenants` — calls `verify_tenant` on every load; the cockpit's response shape (`IBrandDetails`, `IFeatures`, `apiUrl`) is a hard dependency. If the cockpit changes the response shape, `brand.model.ts` breaks.
- `sc-saas-backend` — all business API calls go to the `apiUrl` received from the cockpit. If a backend controller or DTO changes, the matching service in `core/service/` breaks.

---

### 4. `sc-saas-admin` — Admin Operations Panel

**Stack:** PHP · Medoo ORM · sparkAdminTpl · AWS S3

The internal operations dashboard used by the SanchiConnect team to manage tenants, programs, application rounds, startup evaluations, and AI-powered scoring runs. Not exposed to end users.

**Dual-database architecture:** Admin always holds two connections simultaneously:
- `$mainDatabase` — connects to the cockpit (tenants) DB to look up tenant rows and select the correct per-tenant database credentials.
- `$database` — connects to the selected tenant's own MySQL database for all business data operations.

**Key responsibilities:**
- Program and application round management
- Bulk application review and rating
- AI scoring run orchestration (upload CSV → start scoring → poll status → finalize → view results)
- Re-scoring and result export (CSV, XLSX)
- Tenant provisioning support

**Connects to:**
- `sanchiconnect-saas-tenants` — reads cockpit DB directly (not via API) to resolve tenant credentials and select `$database`.
- `sc-saas-backend` — calls the business API via `api_server_url` for all application/program data.
- `ai-startups-analyzer` — drives the full scoring lifecycle: uploads CSV, starts background scoring, polls status, triggers finalization, and fetches results. Admin is the only caller of the analyzer.

---

### 5. `ai-startups-analyzer` — AI Scoring Service

**Stack:** Python 3.10+ · FastAPI · SQLAlchemy (async, aiomysql) · MySQL · OpenAI / Anthropic / Gemini

A standalone LLM-based scoring service that evaluates startup applications against a program's criteria. Called exclusively by `sc-saas-admin` — it never initiates contact with any other repo.

**How it works:**
1. Admin uploads a CSV of applicant submissions + an evaluation thesis.
2. The analyzer slices the CSV into batches of configurable size (default: 5 applicants per LLM call).
3. Optionally enriches each applicant with live web data (Serper.dev search + Firecrawl website scrape) before scoring.
4. Calls the configured LLM provider (OpenAI, Anthropic, or Gemini) for each batch; parses structured scores and justifications from the response.
5. Admin polls `/get-response-status/` for progress, then calls `/finalize-analysis/` to merge all batch results into a single scored output.

**Scoring contract (frozen):** The model outputs scores on a 0–500 scale. These are divided by 100 and returned as 1–5. This conversion (`_coerce_rating()` in `routes.py`) is the only place the scale mapping happens and must never change — all historical scores stored in the admin DB were persisted using this formula.

**Supports re-scoring:** Admin can re-score a subset of applicants without re-running the whole set. A finalize step merges new ratings additively, deduplicating by `submission_id`.

**Connects to:**
- `sc-saas-admin` — the only caller. Admin drives the entire lifecycle (upload → start → poll → finalize). The analyzer never pushes results back; admin polls.
- LLM providers (OpenAI / Anthropic / Gemini) — one active provider at a time, set by `DEFAULT_PROVIDER` env var.
- Serper.dev + Firecrawl — optional enrichment APIs; both are best-effort and never block scoring if unavailable.

---

### 6. `sc-saas-3rdparty-webservices` — Integration Gateway

**Stack:** NestJS 9 · TypeScript · axios · nodemailer · short.io SDK · convertapi SDK

A stateless microservice that centralises every third-party API integration in one place. Instead of spreading API keys and SDK dependencies across other repos, the backend's `core/services/` layer calls this gateway over HTTP for all external communications. The gateway talks to the actual provider and returns a normalised response.

**No database, no auth on its own endpoints.** It is an internal service — relies on network/firewall isolation. Never expose it publicly without adding auth middleware.

**Seven integration categories:**

| Module | Provider | What it does |
|---|---|---|
| `sms` | Auth.key.io | Send OTP SMS |
| `sendGrid` | SendGrid | Email delivery (primary) |
| `ses` | SMTP / AWS SES | Email delivery (fallback, supports per-call custom SMTP) |
| `cometChat` | CometChat | Real-time chat — user/group/message management |
| `videoSDK` | VideoSDK | Video meeting creation + session management (v1 + v2) |
| `shortIo` | Short.io | URL shortening + encrypted authenticated action links |
| `convertKit` | ConvertAPI | Document conversion (PPT → PNG) |

**Authenticated action links** — the `shortIo` module uses AES-256-CBC encryption (`ENCRYPTION_KEY`) to embed user tokens and UUIDs into short links sent via email, so recipients can take authenticated actions (accept connection, join meeting, view profile) without a separate login step.

**Connects to:**
- `sc-saas-backend` — the only caller. Backend holds the gateway's base URL in `saasSettings[SaaSSettingKey.THIRD_PARTY_SERVICE_BASE_URL]` (loaded from the cockpit at bootstrap). All six of the backend's integration service files (`sms.service.ts`, `ses-email.service.ts`, `video-sdk.service.ts`, `comet-chat.service.ts`, `url.service.ts`, `convertapi.service.ts`) call this gateway exclusively — no other repo calls it.
- External providers (Auth.key.io, SendGrid, CometChat, VideoSDK, Short.io, ConvertAPI, Amazon S3) — one-way outbound only.

> `ENCRYPTION_KEY` must never be rotated without a plan — all Short.io action links already delivered to users will break immediately.

---

### 7. `sanchiconnect-saas-tenants-admin` — Tenants Control-Plane Admin UI

**Stack:** PHP · Medoo ORM · sparkAdminTpl (QUCod framework)

The platform-operator-facing admin panel over the **cockpit** (tenants) database — used by SanchiConnect staff to provision tenants, manage platform operator roles, configure global settings, and manage AI-credits packages/orders. Not to be confused with `sc-saas-admin`, which is the tenant-facing ops panel over each tenant's own business DB.

**Single database connection** — unlike `sc-saas-admin`'s dual-DB setup, this repo only ever talks to the cockpit DB (no per-tenant `$database` connection, since it has no tenant-scoping concept of its own).

**Key responsibilities:**
- Tenant provisioning and settings (`tenant_users`, `organizations` tables — owned by `sanchiconnect-saas-tenants` but edited here via a generic dynamic CRUD engine)
- Platform operator accounts and roles (`spa_admin_users`, `spa_admin_roles`)
- Global settings, email/API configuration (`spa_settings`, `spa_email_settings`, `spa_api_core_management`)
- AI-Credits management (packages, orders, grants, task rates)
- Tenant data export/backup (CSV/Excel/ZIP, per-category)

**Connects to:**
- `sanchiconnect-saas-tenants` — shares its MySQL database directly (not via API); a TypeORM migration there can break Medoo queries here and vice versa.
- `sc-saas-backend` — makes direct, unconditional calls: editing a `tenant_users` record fires `PATCH api/v1/public/global/saas/settings` against that tenant's own live backend deployment.

> Leaf node from the outbound-API perspective (nothing else calls it), but tightly coupled at the database layer to `sanchiconnect-saas-tenants` — treat schema changes there as breaking changes here too.

---

## Repository Access

All seven repositories are private and hosted under the [sanchiconnect](https://github.com/sanchiconnect) GitHub organization. You need collaborator access to each repo you intend to work on.

### Requesting access

1. Make sure you have a GitHub account.
2. Go to the repository page you need access to:

   | Repo | GitHub URL |
   |---|---|
   | `sanchiconnect-saas-tenants` | github.com/sanchiconnect-org/sanchiconnect-saas-tenants |
   | `sc-saas-backend` | github.com/sanchiconnect-org/sc-saas-backend |
   | `sc-saas-frontend` | github.com/sanchiconnect-org/sc-saas-frontend |
   | `sc-saas-admin` | github.com/sanchiconnect-org/sc-saas-admin |
   | `ai-startups-analyzer` | github.com/sanchiconnect-org/ai-startups-analyzer |
   | `sc-saas-3rdparty-webservices` | github.com/sanchiconnect-org/sc-saas-3rdparty-webservices |
   | `sanchiconnect-saas-tenants-admin` | github.com/sanchiconnect-org/sanchiconnect-saas-tenants-admin |

3. Share your GitHub username with an existing organization owner and ask them to send you a collaborator invite from **Settings → Collaborators and teams** on each repo you need.
4. Accept the invite from your GitHub notifications or the email GitHub sends you.

### Cloning after access is granted

Once invited, clone all repos into the same parent directory so workspace-level tooling works correctly:

```bash
mkdir SanchiSaaS && cd SanchiSaaS
git clone https://github.com/sanchiconnect-org/sanchiconnect-saas-tenants
git clone https://github.com/sanchiconnect-org/sc-saas-backend
git clone https://github.com/sanchiconnect-org/sc-saas-frontend
git clone https://github.com/sanchiconnect-org/sc-saas-admin
git clone https://github.com/sanchiconnect-org/ai-startups-analyzer
git clone https://github.com/sanchiconnect-org/sc-saas-3rdparty-webservices
git clone https://github.com/sanchiconnect-org/sanchiconnect-saas-tenants-admin
```

> You do not need access to all seven repos to contribute. Request only the repos relevant to your work. The blast-radius order (tenants → backend → frontend / admin) is a good guide — start with the repos furthest downstream from your change. `sanchiconnect-saas-tenants-admin` also depends on the cockpit's DB schema, so treat it as living alongside `sanchiconnect-saas-tenants` when requesting access.

---

## Local Development

### sanchiconnect-saas-tenants (Cockpit)

Before starting, create a local MySQL database for the cockpit and configure your `.env`:

```bash
# In MySQL
CREATE DATABASE sanchiconnect_tenants;
```

```env
# .env (sanchiconnect-saas-tenants)
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=your_password
DB_DATABASE=sanchiconnect_tenants
```

Then install and start:

```bash
cd sanchiconnect-saas-tenants
npm install
npm run start:dev      # NestJS watch mode
```

TypeORM `synchronize` is enabled — the schema is created automatically on first run. No manual migrations needed locally.

### sc-saas-backend (Business API)

Before starting, create a local MySQL database for the tenant you are developing against and configure your `.env`:

```bash
# In MySQL — one database per tenant
CREATE DATABASE sanchiconnect_client_local;
```

```env
# .env (sc-saas-backend)
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=your_password
DB_DATABASE=sanchiconnect_client_local

# Must point to your local cockpit instance
SANCHI_CONNECT_API_BASE_URL=http://localhost:3000/
```

Then install and start:

```bash
cd sc-saas-backend
npm install
npm run start:dev      # NestJS watch mode
# Swagger docs available at /api/docs (local only)
```

The backend calls the cockpit at startup to bootstrap itself — the cockpit must be running first.

### sc-saas-frontend (PWA)

```bash
cd sc-saas-frontend
npm install
npm start              # ng serve --configuration local → http://localhost:4200
```

### sc-saas-admin (Admin Panel)

PHP application — serve via your local PHP server (Apache/Nginx + PHP). Configure `config/config.php` with the tenant DB credentials and `api_server_url` pointing to the backend.

### sc-saas-3rdparty-webservices (Integration Gateway)

This service has no database — no `CREATE DATABASE` step needed. Copy `.env` and fill in third-party API keys:

```bash
cd sc-saas-3rdparty-webservices
npm install
cp .env.example .env   # no .env.example exists yet — create .env manually
```

Minimum required `.env` to start (fill in keys for the integrations you need locally):

```env
NODE_ENV=development
PORT=3002
FRONTEND_URL=http://localhost:4200
ENCRYPTION_KEY=<32-char-base64-string>

# Add keys only for providers you need locally:
SENDGRID_KEY=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
CCHAT_REGION=us
CCHAT_APPID=
CCHAT_AUTHKEY=
CCHAT_RESTAPIKEY=
VIDEOSDK_REGION=us
VIDEOSDK_API_KEY=
VIDEOSDK_API_SECRET=
VIDEOSDK_API_ENDPOINT=https://api.videosdk.live
SHORT_IO_KEY=
SHORT_IO_DOMAIN=
SHORT_IO_DOMAIN_ID=
CONVERTAPI_APIKEY=
CONVERTAPI_APISECRET=
AUTHKEYIO_APIKEY=
AUTHKEYIO_SENDERID=
AUTHKEYIO_OTPTEMPLATEID=
MESSAGE_API_URL=
AMAZON_S3_ENDPOINT=
AMAZON_REGION=
AMAZON_ACCESS_KEY_ID=
AMAZON_SECRET_ACCESS_KEY=
AMAZON_S3_BUCKET=
```

```bash
npm run start:dev      # NestJS watch mode → http://localhost:3002
# Swagger docs available at /api/docs (non-production only)
```

Then point the backend at it by adding to the backend's `.env`:

```env
THIRD_PARTY_SERVICE_BASE_URL=http://localhost:3002/api
```

### ai-startups-analyzer (AI Scoring)

```bash
cd ai-startups-analyzer/api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # → http://localhost:8000
# or from repo root:
./start.sh                      # starts analyzer + Next.js frontend together
```

### sanchiconnect-saas-tenants-admin (Tenants Control-Plane Admin UI)

PHP application — shares the same cockpit MySQL database as `sanchiconnect-saas-tenants`, so point it at the same local DB you created for the cockpit above.

```bash
cd sanchiconnect-saas-tenants-admin
php composer.phar install   # vendor/ is not committed
cp .env.example .env        # fill DB creds (same DB as the cockpit), JWT key, AWS keys, role IDs
```

Serve via your local PHP server (Apache/Nginx + PHP); `.htaccess` rewrites every URL to `index.php?action=…`.

---

## Key Concepts

### Tenancy model

- **Cockpit** (`sanchiconnect-saas-tenants`): single shared MySQL database, one row per tenant keyed by `domain`.
- **Backend** (`sc-saas-backend`): one deployment per tenant. Tenant config and feature flags are loaded once at bootstrap from the cockpit and held in memory — there is no tenant column on entities.
- **Admin** (`sc-saas-admin`): uses `$mainDatabase` (cockpit DB) for tenant lookup and `$database` (per-tenant client DB) for business data.
- **Tenants Admin** (`sanchiconnect-saas-tenants-admin`): single connection, straight to the cockpit DB — no per-tenant concept of its own. It's a platform-operator tool operating on global cockpit data (tenant rows themselves), not per-tenant business data.

### Feature flags

Feature flags are boolean columns on `TenantUsersEntity` in the cockpit repo. The snake_case column name is the contract string used everywhere:

- **Cockpit** — defines the column (source of truth)
- **Backend** — `Feature` enum in `src/core/constants/enum.ts`
- **Frontend** — `IFeatures` interface in `src/app/core/domain/brand.model.ts`
- **Admin** — constants in `config/config.php`

Adding, renaming, or removing a flag requires propagating the change to all four locations.

### Authentication

JWT-based. Token delivered as cookie (`accessToken`) with Bearer fallback. The `single_session_login_enabled` feature flag toggles server-side session tracking in the backend.

### AI Scoring

The analyzer scores startup applications on a 0–500 internal scale, returned to admin as 1–5 (÷ 100, 2 decimal places). This conversion lives exclusively in `_coerce_rating()` in `routes.py` and must never be changed — all historical scores depend on it.

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `initial_development` | Active development |
| `main` | Production |

Each repo is versioned and deployed independently. Never assume an atomic cross-repo change — coordinate and stage deploys in dependency order: **tenants → backend → frontend / admin**.

---

## Cross-Repo Rules (Hard)

1. **Flag names are owned by `tenants`.** Any add/rename/remove must propagate to backend, frontend, and admin.
2. **The API contract is owned by `sc-saas-backend`.** Controller and DTO changes must be verified against frontend services and admin cURL callers.
3. **The tenant-verification shape is owned by `tenants`** (`verify_tenant` / `tenant-settings` response, including `apiUrl`). Both the backend bootstrap and `brand.model.ts` depend on it.
4. **Every new query in a tenant-scoped repo must enforce the tenant scoping rule.** Cockpit: filter by `domain`. Admin: select per-tenant DB via `admin_domain`. Backend: rely on bootstrap-loaded config — never hardcode another tenant's host. (`sanchiconnect-saas-tenants-admin` has no scoping rule of its own — it's a platform-level tool over global cockpit data, not per-tenant data.)
5. **Never commit secrets.** `.env`, key material, and credentials stay out of git. Exception: `sc-saas-backend/cloudfront-*.pem` is intentional and required.
6. **`sanchiconnect-saas-tenants-admin` shares the cockpit MySQL DB directly with `sanchiconnect-saas-tenants`.** A schema change (migration, column rename) in one must be validated against the other — there's no API boundary between them to catch drift.
