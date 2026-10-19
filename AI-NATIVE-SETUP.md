# AI-Native Setup — SanchiSaaS

This workspace is configured for AI-native development with Claude Code. SanchiSaaS is a **poly-repo**: four independently-cloned, independently-versioned, independently-deployed Git repos that together form one product. This document records what was created, where it lives, what is committed vs. local, and how to run and extend it.

## What was created

### Layered memory (CLAUDE.md)
- **`CLAUDE.md`** (workspace root) — the constitution: platform overview, blast-radius graph, the 6 cross-repo invariants, a "where do I look for X" index, and global guardrails.
- **`<repo>/CLAUDE.md`** — one per repo (all 7 repos: tenants, backend, frontend, admin, ai-startups-analyzer, sc-saas-3rdparty-webservices, sanchiconnect-saas-tenants-admin): purpose, exact run/test/build/lint commands, module map, conventions, and "contracts I own / consume".

### Workspace `.claude/` orchestration (root)
- **`settings.json`** — the four repos as `permissions.additionalDirectories`; allow read/test/lint freely; `ask` on `git push`/commit/deploy/publish; `deny` reads of secrets (`.env`, `*.pem`, `*.key`, `db_settings.php`) and writes to `.env`; the PreToolUse hook.
- **`settings.local.json`** — empty scaffold for your machine-specific overrides (gitignored).
- **`commands/`** — workspace slash commands (see below).
- **`agents/`** — subagents: the generic `cross-repo-reviewer` plus the four cross-repo intelligence primitives.
- **`hooks/guard-sensitive-files.sh`** — PreToolUse guard.

### Commands (`.claude/commands/*.md`)
| Command | Purpose |
|---|---|
| `/onboard` | Summarize the platform for a new contributor (reads all 7 CLAUDE.md). |
| `/catchup` | Summarize in-flight work across all 4 repos' branches (git status/log/diff). |
| `/cross-repo-review [scope]` | Review the pending diff against the 6 invariants before PRs (→ `cross-repo-reviewer`). |
| `/plan-feature <desc>` | Per-repo change plan (repos, modules, contract/flag impact, migrations, sequencing, tests) — no code. |
| `/trace-flag <flag>` | Trace a flag tenants→backend→frontend→admin, with orphans (→ `feature-flag-mapper`). |
| `/audit-contract [scope]` | Backend-vs-consumers API drift (→ `api-contract-auditor`). |
| `/check-isolation [scope]` | Tenant-scoping safety net (→ `tenant-isolation-reviewer`). |
| `/flag-impact <flag> rename\|remove` | Deploy-safe rename/remove plan across 4 repos (→ `flag-impact-planner`). |
| `/spec-new feature <id> \| module <repo>/<module>` | Scaffold a spec from template (→ `spec-author` for features). Features: asks which existing Linear project and who to assign, then creates a **milestone** in that project with one issue per repo, never a new project unless it has a lead, a target date and ~5 issues (SAN-1579). |
| `/spec-implement <id>` | Implement an **approved** feature spec across repos (→ `spec-implementer`). |
| `/from-linear <id>` | Read a Linear issue and kick off `/spec-new feature <id>`. Requires the Linear connector. |

### Subagents (`.claude/agents/*.md`)
Read-only cross-repo primitives: `cross-repo-reviewer`, `feature-flag-mapper`, `api-contract-auditor`, `tenant-isolation-reviewer`, `flag-impact-planner` (Read/Grep/Glob/Bash). Spec agents: `spec-author` (Read/Grep/Glob/**Write** — writes the draft spec) and `spec-implementer` (full read/write/Bash — the only agent that edits app code, gated on `status: approved`). Each has a tight system prompt encoding the cross-repo wiring discovered in discovery.

### Spec system (`specs/`)
- **Templates:** `specs/feature.spec.template.md`, `specs/module.spec.template.md`.
- **Feature specs:** `specs/features/<id>-<slug>.spec.md` (workspace layer — features span repos). Frontmatter routes the work: `repos` (dependency order), `contracts` (api/flags/events), `tenant_scoped`, `depends_on`, `status` (draft→approved→in-progress→in-review→done). Non-empty **Open questions** ⇒ not approvable.
- **Module specs:** `<repo>/src/<module>/module.spec.md` (committed, only for real bounded contexts). Declare `owns`/`consumes` + the `tenant_scoping` mechanism. Master indexes (grouped by domain, links to every spec, security findings surfaced during authoring):
  - All 9 `sanchiconnect-saas-tenants` modules have specs (control plane — highest blast radius) as of 2026-06-18. Master index: `specs/tenants-module-specs-index.md`.
  - All 58 `sc-saas-backend` modules have specs as of 2026-06-17. Master index: `specs/backend-module-specs-index.md`.
  - All 26 `sc-saas-frontend` modules have specs. Master index: `specs/frontend-module-specs-index.md`.
  - All 22 `sc-saas-admin` modules have specs (PHP/Medoo/sparkAdminTpl) as of 2026-06-18. Master index: `specs/admin-module-specs-index.md`.
  - **`ai-startups-analyzer`**: 5 module specs (Python/FastAPI, scoring engine, AI provider facade, enrichment), master index at `specs/ai-analyzer-module-specs-index.md`, as of 2026-06-18.
  - **`sc-saas-3rdparty-webservices`**: 7 module specs (sms, sendGrid, ses, cometChat, videoSDK, shortIo, convertKit), master index at `specs/3rdparty-webservices-module-specs-index.md`, as of 2026-06-19.
- **Admin feature specs:** 12 feature specs exist for admin-facing work (FA-001 through FA-008) at `specs/features/FA-00X-*.spec.md`.
- **Tenants feature specs:** 4 feature specs exist for control-plane work (FT-001 through FT-004) at `specs/features/FT-00X-*.spec.md`.
- **AI analyzer feature specs:** 2 AI analyzer feature specs (FAI-001 Application Scoring, FAI-002 Enrichment & Thesis) at `specs/features/FAI-00X-*.spec.md`.
- **Lifecycle:** `/from-linear`→`/spec-new`→ author drafts → you approve → `/spec-implement` builds in dependency order, running `/audit-contract`, `/trace-flag`, `/check-isolation` as gates before `in-review`.

### Guardrail hook
`PreToolUse` on `Write|Edit|NotebookEdit` runs `hooks/guard-sensitive-files.sh`, which:
- **DENIES** writes to secret/key material (`.env`, `*.pem`, `*.key`, `credentials`, `db_settings.php`) — including the intentional `cloudfront-*.pem`, which must never be modified by the agent.
- **ASKS** (forces a second look) on edits to flag-definition / API-contract files: `tenant-users.entity.ts`, `global.controller.ts`/`global.service.ts`, backend `enum.ts`, frontend `brand.model.ts`, admin `config.php`, and backend `*.controller.ts` / `dto/*.ts` — with a reminder to run `/trace-flag` or `/audit-contract`.

## Committed-per-repo vs. workspace-local

- **Committed inside each repo (share with the team):** that repo's `CLAUDE.md` and any `<repo>/src/<module>/module.spec.md` (e.g. the new `sc-saas-backend/src/modules/auth/module.spec.md`). (Per-repo `.claude/` already existed in 3 repos with settings; left as-is aside from the path normalization noted below.)
- **Workspace-local (NOT in any repo's git):** the root `CLAUDE.md`, the entire root `.claude/` (settings, commands, agents, hooks), the `specs/` tree (templates + `specs/features/*` — feature specs span repos so they live at the workspace layer), `AI-NATIVE-SETUP.md`, and the root `.gitignore`. The root is not itself a git repo. If you later promote it to its own repo, `.gitignore` already excludes `settings.local.json` and the four nested product repos.

## How to run Claude in this workspace (VS Code)

1. Open the **`SanchiSaaS/` folder** in VS Code (the workspace root, `/Users/mac/Desktop/Work/SanchiSaaS`) — not an individual repo. The root `.claude/` is then the project config, so all commands, agents, and the hook load automatically and the four repos are in scope via `permissions.additionalDirectories`.
2. Open the **Claude Code extension** panel (or run it in the integrated terminal from the root). Accept the workspace-trust prompt so project skills/permissions activate.
3. **Restart / start a fresh session after this setup** — file-based subagents and commands load at session start (use `/agents` to load interactively without restarting).
4. Per-repo work still benefits: opening a repo subfolder, the nearest `CLAUDE.md` and `module.spec.md` apply; the hook and root commands remain available because they're discovered walking up to the root.

> **Linear:** `/from-linear` and the `feature` path of `/spec-new` need the Linear MCP connector **authenticated** (see "Linear connector" below). It is installed but not yet connected.

The primitives were dry-run against live code during setup and produced real findings (e.g. `learning_management` is wired tenants→backend→frontend but admin reads it via `$brandSettings` with no `config.php define()`; `notifications` contract is clean with 7 unconsumed cron/test routes; isolation holds on the sampled tenants/backend paths). The tooling works against the actual repos.

## Linear connector (paused — needs your action)
The Linear MCP server is **installed but not authenticated**. To connect it:
1. In Claude, open **Settings → Connectors** (or run `/mcp`), find **Linear**, and click **Connect**; authorize in the browser.
2. (CLI/headless alternative) the OAuth flow is also reachable via the `mcp__claude_ai_Linear__authenticate` tool — tell me to start it and I'll hand you the authorization URL.

Until connected, `/from-linear` will stop and ask you to connect rather than guess an issue's contents. The rest of the spec system works without Linear (author a spec from a description).

## How to extend

- **New command:** add `.claude/commands/<name>.md` with `description` (and optional `argument-hint`) frontmatter; the body is the prompt; reference args with `$ARGUMENTS` / `$1`. Keep commands thin — delegate heavy logic to a subagent.
- **New subagent:** add `.claude/agents/<name>.md` with `name` + `description` (and optional `tools`, `model`) frontmatter; the body is the system prompt. Restrict `tools` to the minimum (read-only primitives use `Read, Grep, Glob, Bash`).
- **New guardrail:** extend `hooks/guard-sensitive-files.sh` (add a `case` branch) — emit `deny` to block or `ask` to force review.
- **New feature spec:** `/spec-new feature <id>` (or `/from-linear <id>`). Resolve all **Open questions** and set `status: approved` before `/spec-implement`.
- **New module spec:** `/spec-new module <repo>/<module>` — only for real bounded contexts, not every folder. Keep `owns`/`consumes` honest; mark unknowns as `TODO` rather than guessing.
- **Prefer fewer, sharper tools.** If a command does too much, split it; if it's rarely useful, delete it.

## Done as part of this setup
- Normalized the three pre-existing per-repo `.claude/settings.json` from the old `/SanchiConnect/` path to `/SanchiSaaS/` (admin: 45 refs, backend: 1, frontend: 4) — all still valid JSON.

## Follow-ups surfaced (not changed — outside this task's scope)
- `sc-saas-backend/cloudfront-*.pem` is committed and required (confirmed) — left in place; the hook protects it from edits.
- Isolation dry-run flagged admin report-template / scrapper pages reading tenant data from the main DB — worth a real `/check-isolation` pass and a confirmation of those tables' ownership.
- `ip_management` is unused in `sc-saas-admin` (it gates IP via `intellectual_property_section`); confirm that divergence is intentional.
- `verify_tenant` endpoint returns the full `TenantUsersEntity` row, including plaintext `databasePassword` and SMTP credentials for every tenant — worth reviewing whether a scoped projection should be returned instead of the full entity row.
