---
id: SAN-270
title: Client & deal registry screens in the tenants-admin panel
type: feature
status: canceled  # 2026-10-19: AI-Native CRM project shut down, never implemented (Linear issue Canceled)
linear: https://linear.app/sanchiconnect/issue/SAN-270/an-account-manager-can-add-and-edit-a-client-and-its-deal-terms-from-a
owner: sandeep.k@sanchiconnect.com
repos: [sanchiconnect-saas-tenants-admin]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: false
depends_on: []
created: 2026-08-07
---

# Client & deal registry screens in the tenants-admin panel

Governed by **SanchiConnect · AI-Native CRM BRD v1.0** §5.1 (Client Record and Deal Record required fields) and §6 (data model). Part of the [AI-Native CRM project](https://linear.app/sanchiconnect/project/ai-native-crm-client-pipeline-revenue-intelligence-and-invoice-f33e4c9fa226).

## Problem

Account Managers maintain client and contract data in Notion because there is no screen to maintain it anywhere else. Every field the revenue engine depends on is entered somewhere the system cannot read, and corrections never make it back (BRD P4).

## Acceptance criteria

Mirrors SAN-270 exactly. Verified 2026-08-07 — **33 checks pass, 1 known gap**.

- [x] AC1 — a client can be added with name, organisation type, primary contact, account manager, stage, GSTIN, PAN; the form refuses to save when any is blank
- [x] AC2 — contacts can be added to a client and one marked primary
- [x] AC3 — a deal can be added with deal amount, payment terms, contract start, contract end, next invoice due; contract end may be blank
- [x] AC4 — Contract Status and Account Health are read-only, never editable form fields
- [x] AC5 — a client's deals are visible on its detail page, including expired ones
- [x] AC6 — editing preserves every untouched field; nothing is silently blanked
- [x] AC7 — the client list is searchable by name and filterable by stage, organisation type, account manager
- [ ] **AC8 — an Account Manager sees only their own accounts in the list — NOT DELIVERED.** See "Known gaps".

## Design decisions

### DD-1 — Fully separate CRM tables (decided 2026-08-07 by user; supersedes the issue's own framing)

Investigation found the CRM's "Client" and "Contact" concepts already have tables in the shared tenants MySQL DB: `organizations` (registered as **"Clients"** in this panel's sidebar via `$customTableHeadersTitles` in `modules/common.php:14-21`), plus `contacts`, `contracts`, `subscriptions`, `invoices`, `payments`.

**All of these are owned by the NestJS `sanchiconnect-saas-tenants` repo's `organizations` module** — confirmed in `specs/tenants-module-specs-index.md:62` and `knowledge.md:411-415`. Altering them is a cross-repo schema change and would breach the one-repo-per-issue guardrail on a `Repo: Tenants-Admin` issue.

Three options were put to the dev lead. **Chosen: fully separate `crm_*` tables**, standing on their own and not referencing `organizations`/`contacts`.

- **Benefit:** SAN-270 stays entirely inside `sanchiconnect-saas-tenants-admin`, touches zero NestJS-owned tables, and is deliverable without a companion issue.
- **Accepted cost:** the sidebar now carries two client lists — the existing "Clients" (`organizations`, tenant-provisioning orgs) and the new "CRM › Clients" (`crm_clients`, revenue/contract records). This is duplicate client identity, which is the problem BRD P4 exists to eliminate. **Recorded as a deliberate decision, not an oversight.** If the two lists later need reconciling, that is a new issue, not a defect in this one.

### DD-2 — Account Manager is a platform operator

`crm_clients.account_manager_id` references `spa_admin_users.id` (display field `name`). Account Managers are internal SanchiConnect staff, and `spa_admin_users` is this panel's operator table.

### DD-3 — Reuse the generic CRUD engine, do not write custom modules

`add.php` / `edit.php` / `table.php` / `detail.php` are one generic engine parameterised by table name, driven by `spa_data_management` field metadata. Registering the three tables there yields all four screens with no new controllers, matching how every other business table in this repo works.

### DD-4 — No `spa_form_layouts` rows for the CRM tables

Deliberate. Per this repo's CLAUDE.md landmine: `themes/default/html/add.php` renders fields *only* from configured sections once a `spa_form_layouts` row exists, with no fallback for unassigned columns — producing a blank form. A layout row is created the instant anyone opens "Customize form layout". The CRM tables ship with **no layout row**, so they render the flat field list. Do not open "Customize form layout" on `crm_clients` / `crm_contacts` / `crm_deals` without fully sectioning them in the same sitting.

## Per-repo plan

### sanchiconnect-saas-tenants-admin

1. **Migration** `database/migrations/2026_08_07_SAN-270_crm_registry.sql` — creates `crm_clients`, `crm_contacts`, `crm_deals`. Establishes a migrations directory; this repo previously had none.
2. **Field metadata** — `spa_data_management` rows: `required`, `relationship`, `date`, `email`, `phone`, `boolean_switch`, `hidden`.
3. **Menus** — one `CRM` parent in `spa_menu_management` with three table-backed children resolving to `/table/crm_*`.
4. **Header titles** — `$customTableHeadersTitles` entries in `modules/common.php` so the tables read as "CRM Clients" / "CRM Contacts" / "CRM Deals" rather than raw table names.

## Verification

Automated test coverage was **not** added — this repo has no test suite and no CI (per its CLAUDE.md), and the workspace "guardian" skill referenced by the Developer Guide does not exist yet. Substituted verification, run 2026-08-07:

- `php -l` clean on `modules/common.php` and the seed script
- A 34-check functional script against the live DB: real inserts/updates for client, contact and deal; uniqueness violation; NULL `contract_end`; partial-update field preservation; search and filter queries; metadata and detail-section shape. **33 pass, 1 fail (AC8, known gap).** Test rows created and removed; all three tables left at 0 rows.
- Seeder re-run confirms idempotency: 0 duplicate inserts on second run.
- Confirmed `spa_form_layouts` has **0** rows for `crm_*` — the DD-4 landmine guard.

### Finding — this MySQL server does not run in strict mode

`SELECT @@SESSION.sql_mode` returns just `ANSI_QUOTES`; **`STRICT_TRANS_TABLES` is off**. A missing `NOT NULL` value is therefore silently coerced to `''` rather than rejected — verified by an insert with no `name` succeeding and producing a blank-named row.

`NOT NULL` alone is not a real guard on this server. The migration adds `CHECK (col <> '')` constraints on `crm_clients.name`/`gstin`/`pan` and `crm_contacts.name` — MySQL 8.0.16+ enforces CHECK regardless of strict mode (server here is 8.0.46). Re-verified: the blank insert is now rejected.

**This affects every table in this panel, not just the CRM ones.** Worth a separate look at whether strict mode should be enabled server-wide — out of scope for SAN-270.

## Open questions

- **OQ-A (dev lead)** — should `crm_clients` eventually reconcile with `organizations`, and if so, which is authoritative? Deferred by DD-1; needs answering before the M5 pipeline views (SAN-272 … SAN-275) are built on top, or those views will show a different client set than the existing "Clients" screen.
- **OQ-B (PO)** — BRD §5.1 marks Primary Contact required on the client record, but a contact cannot exist before its client does. Implemented as: client saves without a contact, contact added immediately after. Confirm this is acceptable, or specify a combined create flow.
- **OQ-C (dev lead)** — AC8 (an AM sees only their own accounts) has no row-level scoping mechanism in the generic engine, which has no per-user filtering anywhere in this repo. See "Known gaps" below.

## Addendum — full CRM data model (2026-08-07, user-directed)

Beyond SAN-270's three tables, the remaining CRM data model was created in `database/migrations/2026_08_07_crm_full_data_model.sql`. Each table is grounded in a named BRD section or issue AC — none is speculative:

| Table | Required by |
|---|---|
| `crm_invoices` | BRD §6 Invoice entity / §5.4 Invoice Record |
| `crm_invoice_status_history` | SAN-267 AC7 — every state change recorded with actor |
| `crm_audit_log` | SAN-269 AC6/AC7 + BRD §8 Security |
| `crm_automation_log` | SAN-268 AC7 + BRD §8 Integration |
| `crm_ai_insights` | BRD §5.7 + §8 AI Transparency (the `signals` column) |
| `crm_tasks` | BRD §5.6 automation A3 — renewal task for the AM |

Verified with a 22-check script — **22 pass, 0 fail** — covering the `(crm_deal_id, due_date)` unique key (the DB-level guarantee behind master criterion AC-07), the TDS CHECK constraint (SAN-266 AC6), one-current-insight-per-entity, and FK cascade behaviour. All tables left at 0 rows.

**None of these six are registered with the generic CRUD engine — deliberately.** `crm_audit_log` must not be editable (SAN-269 AC7 requires it be untamperable through the application), the log and insight tables are written by automation and the AI layer rather than by operators, and `crm_invoices`' operator UI is a separate pending issue (build order #14). Registering a half-formed invoice screen now would pre-empt that issue.

### ⚠ Ownership collision to resolve

`crm_invoices` is the same concept as **SAN-266** (`Repo: Tenants`, assigned to Aman), which routes M4 invoice schema to the NestJS app. Both must not ship. Decide which repo owns invoice schema before SAN-266 starts, or the work is done twice and the two diverge.

## Known gaps

**AC8 is not satisfied by this change.** The generic table engine has no row-level, per-operator filtering, and this repo has no tenant-scoping rule at all (its CLAUDE.md states so explicitly — it is a platform-level tool). Delivering AC8 means either adding a scoping hook to `modules/table.php` (which affects *every* business table in the panel — a blast radius well beyond this issue) or writing a custom CRM module instead of using the generic engine.

Neither belongs inside SAN-270. **Raise as a separate issue** rather than folding it in.
