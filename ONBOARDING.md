# Onboarding — SanchiSaaS AI-Native Workspace

This gets a teammate's machine to the same state as the reference workspace: **8 repos total** — the 7 product repos, plus this workspace-root repo (`sc-saas-ai-native`) carrying the Claude Code layer (root `CLAUDE.md`, `.claude/` commands & agents, `specs/`) that makes this an "AI-native" setup rather than a plain poly-repo checkout.

**Read this in order — Part 1 is a hard prerequisite for Part 2 to make sense.**

---

## Part 1 — Understand the layout

1. **The 7 product repos** (`sanchiconnect-saas-tenants`, `sc-saas-backend`, `sc-saas-frontend`, `sc-saas-admin`, `ai-startups-analyzer`, `sc-saas-3rdparty-webservices`, `sanchiconnect-saas-tenants-admin`) — each its own git repo with its own GitHub remote, versioned/deployed independently (poly-repo, not a monorepo).
2. **The workspace-root repo** (`sc-saas-ai-native`) — `CLAUDE.md` (constitution), `.claude/commands/*.md`, `.claude/agents/*.md`, `.claude/hooks/`, `.claude/settings.json`, `specs/`, plus reference docs (`knowledge.md`, `design.md`, `database.md`, `api.md`, `README.md`, `AGENTS.md`, `AI-NATIVE-SETUP.md`, `ONBOARDING.md` — this file). **This is a real, clonable git repo** — `git clone`s directly *as* the workspace root folder itself (not into a subfolder of it), and the 7 product repos then get cloned as subfolders *inside* it. Its own `.gitignore` already excludes those 7 subfolder names, so nesting independent git repos inside this repo's working tree is intentional, not an accident — each nested repo keeps its own separate `.git`, history, and remote.

Don't skip the workspace-root repo — without it you get a normal poly-repo checkout with no slash commands, no subagents, no cross-repo invariant docs, and no specs.

---

## Part 2 — Set up your machine

### 2.1 Prerequisites
- [Claude Code CLI](https://docs.claude.com/claude-code) installed and signed in with your own account (subscription/API access is per-person, not shared).
- Node.js (for the 3 NestJS repos + Angular frontend), PHP ≥8.1 + Composer (for the 2 PHP admin repos), Python 3.10+ (for `ai-startups-analyzer`).
- GitHub access to the `sanchiconnect` org's repos below — request from whoever manages repo access if you don't have it yet.
- Access to wherever your team stores secrets (`.env` values, DB creds, API keys) — **none of these are in git**, ask your team lead for the secure channel (vault / 1Password / etc.).

### 2.2 Clone the workspace-root repo *as* your working folder

```bash
git clone https://github.com/sanchiconnect-org/sc-saas-ai-native.git ~/Desktop/Work/SanchiSaaS
cd ~/Desktop/Work/SanchiSaaS
git checkout ai_native_setup
```

Note the clone target: `sc-saas-ai-native`'s content lands directly in `SanchiSaaS/` (as `CLAUDE.md`, `.claude/`, `specs/`, etc. sitting right there) — you're not cloning it into a nested subfolder.

### 2.3 Clone the 7 product repos as subfolders inside it

```bash
git clone https://github.com/sanchiconnect-org/sanchiconnect-saas-tenants.git
git clone https://github.com/sanchiconnect-org/sc-saas-backend.git
git clone https://github.com/sanchiconnect-org/sc-saas-frontend.git
git clone https://github.com/sanchiconnect-org/sc-saas-admin.git
git clone https://github.com/sanchiconnect-org/ai-startups-analyzer.git
git clone https://github.com/sanchiconnect-org/sc-saas-3rdparty-webservices.git
git clone https://github.com/sanchiconnect-org/sanchiconnect-saas-tenants-admin.git

for d in sanchiconnect-saas-tenants sc-saas-backend sc-saas-frontend sc-saas-admin ai-startups-analyzer sc-saas-3rdparty-webservices sanchiconnect-saas-tenants-admin; do
  (cd "$d" && git checkout ai_native_setup)
done
```

Each of the 8 repos' active development branch is **`ai_native_setup`** (not `main`) — the commands above already check it out in all of them.

Resulting layout:

```
SanchiSaaS/                              ← this IS the sc-saas-ai-native repo's working tree
├── CLAUDE.md
├── AI-NATIVE-SETUP.md
├── ONBOARDING.md
├── README.md, AGENTS.md, knowledge.md, design.md, database.md, api.md
├── .gitignore                           ← already excludes the 7 subfolder names below
├── .claude/
│   ├── settings.json                    ← committed, keep as-is
│   ├── settings.local.json              ← gitignored/machine-specific; Claude Code creates yours as you go
│   ├── commands/*.md
│   ├── agents/*.md
│   └── hooks/guard-sensitive-files.sh
├── specs/
├── sanchiconnect-saas-tenants/           (separate repo, cloned in 2.3)
├── sc-saas-backend/                     (separate repo, cloned in 2.3)
├── sc-saas-frontend/                    (separate repo, cloned in 2.3)
├── sc-saas-admin/                       (separate repo, cloned in 2.3)
├── ai-startups-analyzer/                (separate repo, cloned in 2.3)
├── sc-saas-3rdparty-webservices/        (separate repo, cloned in 2.3)
└── sanchiconnect-saas-tenants-admin/    (separate repo, cloned in 2.3)
```

### 2.4 Per-repo dependencies and `.env`

Each of the 7 product repos' own `CLAUDE.md` documents its exact run/build/test/lint commands. In short:

| Repo | Install | Env setup |
|---|---|---|
| `sanchiconnect-saas-tenants` | `npm install` | copy `.env.example` → `.env`, fill DB/JWT creds |
| `sc-saas-backend` | `npm install` | same — also needs the cockpit's URL at bootstrap |
| `sc-saas-frontend` | `npm install` | `src/environments/environment.local.ts` — cockpit base URL |
| `sc-saas-admin` | `composer install` | `config/db_settings.php` (gitignored) — tenant DB creds |
| `sanchiconnect-saas-tenants-admin` | `composer.phar install` | copy `.env.example` → `.env` — DB, JWT, AWS keys, role IDs |
| `sc-saas-3rdparty-webservices` | `npm install` | `.env` — only fill keys for providers you'll test locally |
| `ai-startups-analyzer` | `pip install -r requirements.txt` (or `poetry install`) | `.env` — DB, `DEFAULT_PROVIDER`, provider API keys |

Get the actual secret values from your team's secure channel — never from git, never from another teammate's Slack message.

### 2.5 Open the workspace in Claude Code

1. Open the **`SanchiSaaS/` root folder** (not a repo subfolder) in VS Code / your editor.
2. Launch Claude Code from the root — accept the workspace-trust prompt so `.claude/settings.json`, commands, agents, and the hook activate.
3. Start a **fresh session** after this — file-based commands/agents load at session start (`/agents` can load them interactively without a restart).

### 2.6 Authenticate the MCP connectors (per-person, cannot be shared)

This workspace uses two MCP connectors — **Linear** (issue tracking) and **Sentry** (error monitoring). OAuth tokens are tied to your own account and can't be copied from another machine.

- Run `/mcp` inside a Claude Code session, select **Linear**, click **Authenticate**, complete the browser OAuth flow.
- Repeat for **Sentry**.
- Confirm both show `✔ Connected` via `/mcp` before relying on `/from-linear`, `/bug-fix`, or any Sentry-triage workflow.

### 2.7 Verify the setup

- `/onboard` — should produce a platform summary reading all 7 product repos' `CLAUDE.md` files without complaining anything is missing.
- Ask a real question referencing a Linear issue (e.g. "what's SAN-1 about?") — confirms the Linear connector.
- Ask "what are the latest unresolved issues in the sc-saas-frontend Sentry project?" — confirms the Sentry connector.
- Each product repo: run its documented lint/build command from its own `CLAUDE.md` and confirm it passes clean on a fresh checkout.
- `git remote -v` from the `SanchiSaaS/` root should show `origin` pointing at `sc-saas-ai-native` — confirms you're set up to commit/push doc updates (`knowledge.md`, specs, etc.) back to the right place, same as any other repo in this workspace.

---

## What you get once this is done

- **Workspace slash commands**: `/onboard`, `/catchup`, `/cross-repo-review`, `/plan-feature`, `/trace-flag`, `/audit-contract`, `/check-isolation`, `/flag-impact`, `/spec-new`, `/spec-implement`, `/from-linear`, `/bug-fix`.
- **Cross-repo subagents**: `cross-repo-reviewer`, `feature-flag-mapper`, `api-contract-auditor`, `tenant-isolation-reviewer`, `flag-impact-planner`, `spec-author`, `spec-implementer`.
- **The spec system** (`specs/features/*.spec.md`, `<repo>/src/<module>/module.spec.md`) with per-repo master indexes.
- **Guardrails**: a `PreToolUse` hook that blocks writes to secrets/keys and flags edits to flag-definition/API-contract files for a second look.
- **`knowledge.md`** — the running narrative of what's been built/found/fixed across the whole workspace over time (read its Change Log at the bottom first for the most recent state).

Full detail on all of the above lives in `AI-NATIVE-SETUP.md` and the root `CLAUDE.md`, both already in this repo.
