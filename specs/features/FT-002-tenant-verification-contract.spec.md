---
id: FT-002
title: Tenant Verification Contract
repos:
  - sanchiconnect-saas-tenants
  - sc-saas-backend
  - sc-saas-frontend
  - sc-saas-admin
status: draft
contracts:
  api:
    - GET /public/global/verify_tenant/:hostname — returns full TenantUsersEntity projection; consumed by sc-saas-frontend at boot (sanchiconnect-saas-tenants owns)
    - GET /public/global/tenant-settings/:hostname — returns tenant config and feature flags; consumed by sc-saas-backend at bootstrap (sanchiconnect-saas-tenants owns)
  flags:
    - All boolean columns on TenantUsersEntity — the response payload IS the feature-flag source of truth
tenants_modules:
  - sanchiconnect-saas-tenants/src/modules/global/module.spec.md
  - sanchiconnect-saas-tenants/src/modules/tenants/module.spec.md
backend_modules:
  - sc-saas-backend/src/core/services/module.spec.md
  - sc-saas-backend/src/core/guards/module.spec.md
frontend_specs:
  - sc-saas-frontend/src/app/core/domain/module.spec.md
  - sc-saas-frontend/src/app/core/service/module.spec.md
admin_modules:
  - sc-saas-admin/modules/config/module.spec.md
updated: 2026-06-18
---

# FT-002: Tenant Verification Contract

## Summary

The tenant verification contract is the most critical shared interface in the SanchiSaaS platform. It is defined by two public endpoints in `sanchiconnect-saas-tenants/src/modules/global/global.controller.ts` and consumed at startup by every other service. `GET /public/global/verify_tenant/:hostname` is called by the Angular frontend on every cold boot to learn the backend URL (`apiUrl`), branding fields, and the full feature-flag map. `GET /public/global/tenant-settings/:hostname` is called by each `sc-saas-backend` instance at process startup to populate its internal `AppConfigService` and `saasFeatures` map. The PHP admin panel does not call either endpoint — it reads the same data directly from the tenants MySQL database. Because all four repos depend on field names returned by this contract, any schema change in `TenantUsersEntity` must be treated as a breaking API change and coordinated across all consumers before deployment.

## Flow sequence

1. **Frontend cold boot** — Angular app loads, immediately dispatches a call to `GET /public/global/verify_tenant/:hostname` (hostname derived from `window.location.hostname`). No auth token exists yet.

2. **Frontend stores brand slice** — The response is mapped into the `brand` NgRx store. Fields consumed include: `apiUrl` (used as the base URL for all subsequent backend calls), `name`, `logo`, `domain`, `primary_industry`, `sidebar_color`, `new_dashboard_header_color`, `menu_type`, and the full feature-flag boolean map stored under `features` (modeled by `IFeatures` in `brand.model.ts`). All feature gates in Angular templates and guards read from `brand.features.<flag_name>`.

3. **Frontend calls backend** — Every subsequent HTTP call uses `apiUrl` from the brand slice as the base URL. The frontend never hard-codes a backend hostname.

4. **Backend bootstrap** — On process start, `sanchiconnect.service.ts` calls `GET /public/global/tenant-settings/:hostname` with the value of the `HOSTNAME` env variable. The response populates `AppConfigService` (branding, config values) and the `saasFeatures` map (feature flags keyed by the `Feature` enum in `core/constants/enum.ts`).

5. **`FeatureGuard` gates routes** — Every protected backend route decorated with `@UseGuards(FeatureGuard)` reads from `saasFeatures` at request time. If a flag is absent from the map (because it was not in the bootstrap response, or was `null`), the guard treats it as disabled and returns 403.

6. **Admin panel resolves tenant** — `sc-saas-admin/config/config.php` runs a Medoo `$mainDatabase->get('tenant_users', ['api_url', 'database_name', ...], ['admin_domain' => $currentHost])` on every request to select the correct tenant context. It reads the same data the REST endpoints serve, but via direct SQL, with no contract versioning.

7. **Admin uses `api_url`** — The admin panel constructs cURL calls to `sc-saas-backend` using `api_url` retrieved in step 6. Any branding or flag state the admin needs is also read from the same direct-DB query.

## Contract ownership

- `sanchiconnect-saas-tenants` owns the response shape of both endpoints. The field names in the HTTP response are the literal column names from `TenantUsersEntity` (snake_case). This means the DB schema and the API contract are the same object — there is no DTO decoupling layer that could shield consumers from a column rename.
- `sc-saas-frontend` owns `brand.model.ts`. The `IFeatures` interface lists every flag name as a typed boolean property. A field added to `TenantUsersEntity` must also be added here; a field removed silently becomes `undefined` (TypeScript does not protect against missing server-side fields at runtime).
- `sc-saas-backend` owns `core/constants/enum.ts` (`Feature` enum) and `sanchiconnect.service.ts`. The enum entries must match the exact snake_case column names returned by `tenant-settings`. A mismatch means the flag is never found in `saasFeatures` and every `FeatureGuard` using it returns 403.
- `sc-saas-admin` owns `config/config.php` and all `$mainDatabase->get()` calls. These use string literals for column names. No type safety, no compile-time validation.
- **Enforced in CI since 2026-10-13/14 (P-SAN-75, SAN-1591/1592/1595):**
  - **Frozen shape:** the shape is frozen in `sanchiconnect-saas-tenants/contracts/tenant-verification.schema.json`, and the producer test `tenant-verification.contract.spec.ts` fails when the code returns anything else.
  - **Compile-time checks in the consumers:** the generated `contracts/generated/tenant-verification.ts` is copied into backend (`src/core/contracts/`) and frontend (`src/app/core/contracts/`). `enum.ts` and `brand.model.ts` then fail to compile when they declare a key the cockpit doesn't send.
  - **CI workflows:** `tenant-contract.yml` fails when a consumer reads a key the contract doesn't provide, or when a vendored copy drifts. `flags.yml` does the same for flag names, including admin's `config.php`.
  - **Admin's `$mainDatabase->get()` column strings are still unchecked.**

## Feature flags

The verification contract IS the feature-flag delivery mechanism. The full boolean column set from `TenantUsersEntity` is returned in the response of both endpoints. Key flags gated by this contract:

- `single_session_login_enabled` — read by backend; changes JWT session handling.
- `show_ecosystem` — read by frontend to show/hide ecosystem navigation; read by backend to gate ecosystem sync endpoints.
- `elastic_search` — controls whether search uses Elasticsearch or MySQL; backend and frontend must agree on the same value at runtime.
- `is_patent_hub`, `is_facility_hub` — read by frontend to render hub-specific UI sections.
- `intellectual_property_section`, `facility_management` — read by admin to show/hide management panels.
- Every flag returned with `null` (existing tenant, new column) rather than `false` passes through as-is to all consumers.

## Auth & access

- Both endpoints are fully public — no Authorization header, no API key, no IP allowlist.
- `GET /public/global/verify_tenant/:hostname` is called before any user has authenticated; requiring auth here would make the platform unbootable for new users.
- `GET /public/global/tenant-settings/:hostname` is called by the backend process at startup; requiring auth here would require the backend to possess a rotating secret during its own initialization, creating a bootstrapping paradox.
- The admin panel's equivalent access is a direct MySQL connection — authenticated at the DB level by the credentials in `config.php`, which were themselves read from the tenants DB.

## Cross-repo impact

A field rename in `TenantUsersEntity`:
1. The REST response field name changes immediately (no DTO abstraction).
2. `sc-saas-frontend` `IFeatures` — the old property name returns `undefined`; Angular template bindings that were `true` silently become falsy. Feature sections disappear with no error.
3. `sc-saas-backend` `Feature` enum — if the enum value matched the old name, `saasFeatures.get(Feature.OldName)` returns `undefined`; `FeatureGuard` blocks all routes gated by that flag.
4. `sc-saas-admin` `config.php` — `$mainDatabase->get()` with the old column name returns `null`; any admin logic depending on that value falls back to default or errors.

A field removal from `TenantUsersEntity`:
- Same as rename, but the old column disappears from both the DB and the response simultaneously.

The tenants service going down:
- Every `sc-saas-backend` restart fails to bootstrap → all backend deployments crash-loop.
- Every frontend cold boot fails → users see a blank app or error page.
- The admin panel continues to work (reads DB directly) as long as the tenants MySQL instance is up.

## Known issues

1. **Both endpoints are public with no rate limiting or hostname validation.** An unauthenticated caller can enumerate `verify_tenant` with arbitrary hostnames to discover which domains are provisioned as tenants and retrieve their full configuration. The response includes sensitive internal fields: `databasePassword`, SMTP credentials, and any other columns stored on `TenantUsersEntity`. A single HTTP GET against a guessable hostname yields credentials for that tenant's client database. There is no response projection (DTO) to strip sensitive fields — the full entity row is returned.

2. **Single point of failure for the entire platform.** If `sanchiconnect-saas-tenants` is unreachable (process crash, network partition, DB outage), every `sc-saas-backend` that restarts during that window fails to bootstrap, and every Angular frontend on every tenant fails to load. There is no local fallback, cached last-known-good response, or circuit-breaker. A 30-second tenants service restart causes a platform-wide outage for any pod that happens to restart concurrently.

3. **No contract versioning on the endpoints.** Both endpoints are at unprefixed paths (`/public/global/...`) with no API version segment. There is no mechanism to serve an old contract shape to a consumer that has not yet been updated. A breaking field change in `TenantUsersEntity` must be deployed atomically with all consumers — in a poly-repo with independent deploy pipelines, this is operationally impossible to do without a backward-compatibility window.

4. **`saasFeatures` map is populated once at backend startup and never refreshed.** If an operator changes a feature flag in the tenants DB while the backend is running, the change has no effect until the backend process restarts. There is no webhook, polling, or invalidation mechanism. Operators toggling a flag live will see no effect and may assume the system is broken, leading to repeated restarts or duplicate flag changes.
