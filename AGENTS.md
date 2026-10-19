# SanchiSaaS — Workspace AGENTS.md

Last updated: 2026-07-14

A framework-agnostic conventions file for anyone — human or AI agent — working across this poly-repo. This
is workspace-level and different in scope from any single repo's own `AGENTS.md`: it covers what's true
*across* the seven repos, not the conventions specific to one. Read the workspace `CLAUDE.md` first (the
constitution); this file is a tighter, task-oriented companion to it. `[AS-IS]` unless tagged.

---

## 1. The poly-repo rule

Seven independently-versioned, independently-deployed Git repos, each with its own `.git`, dependencies,
and deploy pipeline. **Never assume an atomic cross-repo change.** A change spanning two or more repos must
be coordinated and staged in dependency order — the blast-radius order (`tenants → backend →
{frontend, admin}`, with `ai-startups-analyzer` and `sc-saas-3rdparty-webservices` as leaf nodes in the
outbound direction) is the right default staging order, but see §3 below before trusting it as complete.

No repo in this workspace has Docker, CD, or infra-as-code: deployment is manual/ops-run (Jenkins)
everywhere. CI exists since October 2026 (P-SAN-75): every repo runs `ci.yml` (`scripts/gates.sh`) and a
secret scan, and the cross-repo contract workflows (`flags`, `tenant-contract`, `scoring-contract`,
`api-contract`) catch the mechanical cross-repo breaks (flag names, the tenant-verification shape, the scoring
scale, breaking API changes). They do not catch behavioural breaks, so an uncoordinated change is still risky.
See `docs/DEPLOYMENT.md`.

---

## 2. Cross-repo invariants (from the workspace CLAUDE.md — restated here for a fast reference)

1. **Flag names are owned by `tenants`** (`TenantUsersEntity` boolean/enum columns, ~180 of them). The
   snake_case column name is the contract string everywhere. Propagate add/rename/remove to: backend
   `Feature` enum, frontend `IFeatures`, admin `config.php` constants. Use `/trace-flag` first. Note: the
   `verify_tenant` endpoint exposes flags via a **hand-maintained** `.select()` + object-literal (two manual
   edits per new flag); `tenant-settings` exposes them via **reflection** over every boolean column (one
   edit). These are not the same mechanism — a `/trace-flag` check against one does not confirm the other.
2. **The API contract is owned by `sc-saas-backend`** (controllers + class-validator DTOs, `api/v{n}`).
   Check any controller/DTO change against: frontend `core/service/*`, `sc-saas-admin`'s cURL/Guzzle
   callers, **and `sanchiconnect-saas-tenants-admin`'s cURL callers** (a third, newly-confirmed consumer —
   see §5 below). Use `/audit-contract`.
3. **The tenant-verification contract is owned by `tenants`** — but it is **two different routes for two
   different consumers**, not one contract: `sc-saas-backend`'s bootstrap depends on `tenant-settings`;
   `sc-saas-frontend`'s app-init depends on `verify_tenant`. They use different hostname-matching logic
   (substring vs. effectively-exact `LIKE`) and different flag-exposure mechanisms (see #1). A change that
   passes a smoke test against one consumer can still break the other.
4. **Auth is JWT** — but verify which mechanism actually applies before assuming uniformity:
   `sc-saas-backend` issues it via an httpOnly cookie (Bearer fallback); `sc-saas-frontend` actually reads
   it from that cookie, **not** from localStorage as its own `CLAUDE.md` currently (incorrectly) states;
   `sanchiconnect-saas-tenants` has **no JWT/session concept of its own at all** despite storing the
   `single_session_login_enabled` flag column on behalf of the backend; `sc-saas-3rdparty-webservices` has
   **no auth of any kind** on any endpoint (network-trust only); the two PHP admin panels use session-based
   RBAC, not JWT, with JWT constants defined-but-unused in both.
5. **Tenant scoping rule per repo** — and this is genuinely four different mechanisms, not one rule with
   four implementations (see `design.md` §1 for the full architectural statement): `tenants` filters by
   `domain`; `sc-saas-backend` relies on one-deployment-per-tenant with no per-query guard at all (a
   `domain` column exists on some entities but is never used as a query filter — it's a denormalized label
   for cross-tenant HTTP consumers); `sc-saas-admin` resolves a fresh per-tenant DB connection per request;
   `sanchiconnect-saas-tenants-admin` has **no tenant-scoping mechanism at all** (a stripped fork of
   `sc-saas-admin` with that logic deliberately disabled) except one leaf route (`modules/scrapper.php`)
   that reintroduces it ad hoc for cross-tenant reporting. Use `/check-isolation`.

---

## 3. Known cross-repo drift to watch for (six threads — see `knowledge.md` for the full narrative)

1. **AI-Credits schema has three independent direct mutators** (`sanchiconnect-saas-tenants` owns the
   schema and purchase-side; `sc-saas-admin`'s PHP owns reserve/settle/refund/debit; `sanchiconnect-saas-tenants-admin`'s
   PHP does direct admin CRUD on the same tables) — with no shared schema-versioning mechanism between any
   of the three. Before changing any `ai_credit_*` column, check all three codebases, not just the schema
   owner. See `database.md` §3.
2. **The documented call graph has three confirmed-wrong edges**: `sc-saas-3rdparty-webservices` is not
   "backend-only" (`sc-saas-admin` calls it directly, one route with no auth header);
   `sanchiconnect-saas-tenants-admin` is not "fully standalone" (it calls `sc-saas-backend` directly on
   every tenant edit); `sc-saas-admin` has undocumented direct edges to both the gateway and to
   `sanchiconnect-saas-tenants` itself (an Easebuzz webhook, routed outside its own dispatcher). See `api.md`'s
   real-call-graph table before assuming a repo's own "who calls me" section is exhaustive.
3. **Three tenancy models plus one stripped fork coexist** — do not carry one mental model of "tenant
   scoping" between repos. See §2 point 5 above and `design.md` §1.
4. **Security findings worth checking before touching adjacent code**: `verify_tenant`/`tenant-settings`
   plaintext-secret exposure (already known); per-tenant DB passwords in plaintext, now also read directly
   by `sanchiconnect-saas-tenants-admin`'s `scrapper.php`; hardcoded live API keys in
   `sanchiconnect-saas-tenants` seed data; plaintext OAuth secrets in `sc-saas-backend`'s
   `PaymentGatewaysEntity` (a working `CryptoService` exists but isn't used there); an unauthenticated
   Adminer console with an embedded live DB password in `sanchiconnect-saas-tenants-admin`; zero
   authentication anywhere in `sc-saas-3rdparty-webservices`; five of six sampled AJAX handlers in
   `sanchiconnect-saas-tenants-admin` skip the login check entirely. See `knowledge.md` §6 for the full list
   with citations — do not reproduce any of the underlying secret literals when referencing these.
5. **`synchronize: true` with no migrations is present in every NestJS repo**, not a one-off
   (`sanchiconnect-saas-tenants`, `sc-saas-backend`). Any entity change in either is a live, irreversible
   schema change on next deploy with no migration to revert — be deliberate, and re-read §1's finding before
   assuming a schema change is "just" a code change.
6. **No Docker, CI/CD, or infra-as-code anywhere in the workspace** — there is no automated gate that would
   catch any of the above before it reaches production. Manual coordination is the only safety net that
   exists today.

---

## 4. Specs and workspace commands

Work is driven by specs (`specs/features/<id>-<slug>.spec.md`, `<repo>/src/<module>/module.spec.md`), not
ad-hoc prompts — see workspace `CLAUDE.md` for the full flow (`/spec-new` → author → approve →
`/spec-implement`). Before opening a cross-repo PR, run the relevant gate command
(`/trace-flag`, `/audit-contract`, `/check-isolation`, `/cross-repo-review`) — and, given §3 point 2 above,
do not trust a repo's own "who calls me" documentation as the full list of callers when running these; cross-
check `api.md`'s real-call-graph table too.

---

## Change Log

- 2026-07-14 | Initial workspace-level AGENTS.md. Restated the workspace CLAUDE.md's five cross-repo
  invariants with the specific corrections/nuances each one's per-repo knowledge.md pass surfaced (the
  two-different-routes nature of the tenant-verification contract, the four-way tenancy-model split, the
  non-uniform auth model). Added the six known-drift threads as a tight reference so a future agent doesn't
  have to rediscover them from scratch.
