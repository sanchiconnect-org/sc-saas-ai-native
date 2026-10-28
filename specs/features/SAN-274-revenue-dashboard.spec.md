---
id: SAN-274
title: Revenue dashboard — FY revenue, 30/60/90/120-day pipeline and overdue invoices
type: feature
status: canceled  # 2026-10-19: AI-Native CRM project shut down, never implemented (Linear issue Canceled)
linear: https://linear.app/sanchiconnect/issue/SAN-274/leadership-sees-total-fy-revenue-the-306090120-day-pipeline-and
owner: sandeep.k@sanchiconnect.com
repos: [sanchiconnect-saas-tenants-admin]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: false
depends_on: [SAN-270, SAN-271]
created: 2026-08-07
---

# Revenue dashboard — FY revenue, 30/60/90/120-day pipeline and overdue invoices

Linear issue **SAN-274**, in the [AI-Native CRM project](https://linear.app/sanchiconnect/project/ai-native-crm-client-pipeline-revenue-intelligence-and-invoice-f33e4c9fa226). Governed by **AI-Native CRM BRD v1.0** §5.5 (Revenue Dashboard) and master criterion **AC-14**.

Single repo: `sanchiconnect-saas-tenants-admin`. The issue carries `Repo: Tenants-Admin`; the one-repo-per-task guardrail applies (`specs/spec-authoring-practices.md:88`).

> **This spec is NOT approvable as written.** The Open questions below are non-empty, and OQ-1 is a blocking correctness decision, not a detail. Read "The blocker" first.

## Problem

Leadership assembles FY Revenue by hand from Notion for board reporting — slow, and wrong when the manual formula is applied inconsistently (BRD P1, P3). SAN-270 put the client/deal records in a database; nothing yet turns them into a single revenue view.

## The blocker — there is no FY Revenue value in this repo to aggregate

Evidenced, not inferred:

- **`crm_deals` has no `fy_revenue` column.** Its full column list is `database/migrations/2026_08_07_SAN-270_crm_registry.sql:79-102`: `deal_amount` (total ACV), `payment_terms`, `contract_start`, `contract_end`, `next_invoice_due`, `contract_status`, `renewal_probability`, `version`, `deal_notes`, `attachments`. `deal_amount` is ACV for a contract period — it is **not** FY revenue, which depends on which prepaid instalments fall inside 1 Apr – 31 Mar.
- **No revenue calculation exists anywhere in this repo.** `grep` for `fy_revenue` across the workspace returns nothing outside issue prose.
- **The canonical formula lives in unbuilt work in another repo.** BRD §5.3.2 (FY Revenue) and §5.3.4 (rolling 30/60/90/120-day windows) are routed to **SAN-263 and SAN-264**, labelled `Repo: Tenants` (`specs/features/ai-native-crm-pending-linear-issues.md:206` names them as the owners of "the revenue calculations themselves"). `sanchiconnect-saas-tenants` is not cloned on this machine, and neither issue is built.
- **The BRD PDF is not in this workspace either** — `SanchiConnect_AI_CRM_BRD_v2.pdf` is cited as the source (`specs/features/ai-native-crm-pending-linear-issues.md:6`) but is not present on this machine. `[NOT SPECIFIED IN SOURCE]` — the exact §5.3.2 text is therefore unavailable here and **must not be reconstructed from memory**.

So the dashboard has nothing to sum. Three options, stated honestly:

| Option | What it means | Cost |
|---|---|---|
| **A — recompute the formula in PHP here** | `includes/crm_revenue_functions.php` implements §5.3.2/§5.3.4 from `crm_deals`, dashboard sums its output | Unblocked immediately, but produces a **second implementation of a formula whose NFR demands zero variance**, in a second language, against a first implementation (SAN-263) that doesn't exist yet and will be written later by someone else. AC-14 is exactly the check that catches such drift — and it catches it in front of Finance, after the fact. |
| **B — store a computed FY Revenue per deal** | Add `crm_deals.fy_revenue` (+ window columns), populated by something else; dashboard does `SUM()` only | Matches AC-14's own instruction ("aggregate the same values the records expose, do not re-derive them") and reduces the dashboard to arithmetic that cannot drift. But **the producer does not exist**: SAN-263 is in a repo that has no TypeORM entity for `crm_*` and does not own those tables (`module.spec.md:140`). Adding a column with no writer ships a permanently-zero tile. |
| **C — one calculator, owned here, consumed by both the client record and the dashboard** *(recommended)* | Declare the M3 revenue engine part of this repo alongside the data it reads; a single function is called by both the per-client FY Revenue display and the dashboard tile, so the two are the same code path by construction | Requires a **cross-repo ownership decision** to re-route SAN-263/SAN-264 out of `sanchiconnect-saas-tenants`. That is the same collision already recorded for `crm_invoices` vs SAN-266 (`specs/features/SAN-270-crm-client-deal-registry-admin.spec.md:113-115`) — the CRM data model was deliberately placed in this repo, so the code that reads it arguably belongs here too. |

**Recommendation: Option C**, on the strength of one fact — AC-14 cannot be satisfied by *any* arrangement in which the tile and the per-client figure are produced by different code. Option C is the only one of the three that makes them the same code by construction rather than by discipline. **This is an ownership decision across two repos, so it is OQ-1, routed to the dev lead, and this spec cannot be approved until it is answered.** Do not start implementation on the assumption of C.

## Acceptance criteria

Restated from the issue, with deliverability marked. `[BLOCKED]` items depend on OQ-1 and/or on data that does not exist yet.

- [ ] **AC1** — the dashboard renders a Total FY Revenue tile whose value comes from exactly one revenue source function, never inline SQL in the template. `[BLOCKED on OQ-1]`
- [ ] **AC2** — four further tiles: Revenue Next 30d / 60d / 90d / 120d, each a rolling window from the date of page load. `[BLOCKED on OQ-1]`
- [ ] **AC3** — an Overdue Invoices tile showing both a count and a rupee value. `[BLOCKED on OQ-3 (definition) and on `crm_invoices` having rows]`
- [ ] **AC4** — for a fixed dataset, the Total FY Revenue tile equals the sum of the per-client FY Revenue figures, to the paisa, verified by a reconciliation script that reads both through the same source function and asserts a zero difference. `[BLOCKED on OQ-1]`
- [ ] **AC5** — with the BRD §5.3.3 reference data loaded, the total reads **₹44,70,200**. `[BLOCKED — see below]`
- [ ] **AC6** — every tile links through to the client-level rows behind it, and the linked view's own total equals the tile. `[Deliverable — but not via the existing `?conditions=` mechanism; see the per-repo plan]`
- [ ] **AC7** — a tile never shows a figure computed on a previous request: every value is queried at render time, no value is stored in `$_SESSION`, and no HTTP caching header is set on the page. `[Deliverable]`
- [ ] **AC8** — a Leadership role sees the aggregate tiles but cannot reach `crm_invoices.payment_reference`. `[NOT DELIVERABLE as stated — see "Known gaps"]`

**AC5 cannot pass today.** `crm_clients`, `crm_deals` and `crm_invoices` are all at **0 rows** — SAN-270 left its test rows removed (`specs/features/SAN-270-crm-client-deal-registry-admin.spec.md:78`) and SAN-271's importer is built but **has not been run**, because the Notion export has not been supplied (`specs/features/SAN-271-import-existing-clients.spec.md:26-28`). Until SAN-271 runs, every tile correctly reads ₹0, and AC5 is untestable rather than failing.

## Design decisions

### DD-1 — Custom module, NOT the config-driven counter engine

This is the "which pattern" call the issue implicitly asks for. **Follow `modules/finance_management/invoices.php`** (a bespoke module with its own template and its own menu seeder), **not** `modules/index.php` / `modules/dashboards.php` (the `spa_dashboard_counters`-driven engine). Five reasons, each from code:

1. **The counter engine can only do one aggregate over one column of one table.** `getDashboardCounters()` dispatches to `$database->count|sum|avg|min|max($counterV['table_name'], $counterV['act_column'], $finalConditions)` — `includes/core_functions.php:2248-2266`. No joins, no expressions, no per-row formula. FY Revenue is not a `SUM()` of any single existing column.
2. **Its date filtering is hardcoded to `created_at`.** `getDBDateFormat()` opens with `$dateField = "created_at";` (`includes/core_functions.php:2035`) and every branch keys off it. The windows SAN-274 needs key off `next_invoice_due` / `due_date`, which are business dates, not row-creation dates. Its `this_year` is also the **calendar** year (`MAKEDATE(YEAR(CURDATE()), 1)`, `:2098-2104`), not the Indian FY starting 1 April.
3. **A counter renders no drill-down.** `generateCounter()` emits a `<div>` with an `<h2>` and optional edit buttons — no anchor to any record list (`includes/counter_generator.php:44-53`). AC6 would need new code regardless.
4. **On the demo host the counter engine multiplies every result by a random number.** `if(hostname == "adm.demo.sanchiapp.com"){ $counter['result'] = $counter['result'] * rand(43, 55); }` — `includes/counter_generator.php:40-42` (`hostname` is `$_SERVER['SERVER_NAME']`, `config/config.php:27,32`). Reusing `generateCounter()` for a figure Finance reconciles would silently randomise it on that host. **AC4 and AC5 are incompatible with that helper.**
5. **Counter config is writable with only a CSRF token.** `modules/ajax/spa_actions.php` includes `common.php` and checks `verifyCSRFToken()` (`:43-46`) before `add_counter`/`edit_counter`/`delete_counter` (`:91,147,164`) — there is no `checkLoggedIn()` in that file, a repo-wide pattern documented at `sanchiconnect-saas-tenants-admin/CLAUDE.md:63`. A board-reported total must not be reconfigurable through an endpoint with no login gate.

The counter engine's one genuinely useful feature — per-role tile visibility via a `roles` JSON of `spa_admin_roles.id` values (`includes/core_functions.php:2270-2274`) — is re-implemented directly in the custom module rather than inherited (see DD-3).

### DD-2 — AC7 is satisfied by the existing architecture, not by new cache-busting

Nothing in this panel caches dashboard figures. `getDashboardCounters()` executes its aggregate on every call (`includes/core_functions.php:2248-2266`), invoked per request from `modules/index.php:51` and `modules/dashboards.php:192`. The only caching headers in non-vendor code are in `thumb/compress.php` and `modules/filemanager/download.php` — neither touches these pages. There is no APCu/memcache/file cache layer in the repo.

The one thing that **does** persist across requests is the dashboard's selected period: `$_SESSION['CurrentSearchType']` (`modules/dashboards.php:25-31`). AC7's rule for this module is therefore: **store nothing derived in `$_SESSION`** — a window selection may be a `$_GET` parameter, never a session value, so two operators cannot see different periods under the same tile labels.

### DD-3 — Role visibility is enforced in the module, at table granularity

Table access is already role-gated: `modules/table.php:21-24` calls `checkTableAccess($table_name)`, which reads the `tables` JSON off the session role row and 403s (`includes/core_functions.php:1601-1613`). The revenue dashboard module reuses that gate for its drill-downs and adds its own role check at the top, following `modules/finance_management/invoices.php:9-13`.

What this **cannot** do is hide a single column from one role — see "Known gaps".

### DD-4 — No `spa_form_layouts` row for any `crm_*` table

Restated because this work adds screens over the CRM tables: opening "Customize form layout" on a `crm_*` table creates a layout row and blanks its Add/Edit form (`sanchiconnect-saas-tenants-admin/CLAUDE.md:38`, `specs/features/SAN-270-crm-client-deal-registry-admin.spec.md:60-62`). This spec adds **zero** rows to `spa_form_layouts`.

## Per-repo plan

### sanchiconnect-saas-tenants-admin

Dependency order. Steps 2–4 are blocked on OQ-1; step 1, 5 and 6 are not.

1. **`includes/crm_revenue_functions.php` — new.** The single revenue source. Public surface (names indicative, shape not):
   - `crmFyRevenueTotal($database, $fyStart)` → one figure
   - `crmFyRevenueByClient($database, $fyStart)` → the per-client rows the total is a sum of
   - `crmPipelineWindow($database, $days)` and `crmPipelineWindowByClient($database, $days)` for 30/60/90/120
   - `crmOverdueInvoices($database)` → `array('count' => n, 'value' => x)` and its per-client counterpart

   **Non-negotiable invariant, and the whole point of AC-14:** each total function returns `array_sum()` over the rows its own `*ByClient` counterpart returns. The tile and the drill-down are then the same query by construction, not by agreement. A reviewer should be able to see this in one screenful.

   Every standalone entry point must set the timezone from `spa_settings` before any date call — `date_default_timezone_get()` fatals on this machine ("Timezone database is corrupt"); the app dodges it via `date_default_timezone_set($timezone)` in `includes/core_functions.php:1210-1212` and SAN-271's importer had to do the same (`specs/features/SAN-271-import-existing-clients.spec.md:107-109`). FY boundaries and rolling windows are entirely date arithmetic — this is not optional here.

2. **`modules/crm/revenue_dashboard.php` — new.** `checkLoggedIn()`, `include modules/common.php`, role gate in the shape of `modules/finance_management/invoices.php:6-13`, then six calls into (1), then `$tpl->render(...)`. No SQL in this file, no arithmetic in the template.

3. **`themes/default/html/crm/revenue_dashboard.php` — new.** Six tiles, each an `<a>` to its drill-down. **Does not call `generateCounter()`** (DD-1 reason 4). Conventions: block comments `/* */`, `count($arr) > 0` not `!empty()`, no `isset()`/`empty()` on `$this->` magic props (`CLAUDE.md:76-78`). jQuery is footer-loaded — any inline script defers on `window.addEventListener('load', …)`.

4. **`modules/crm/revenue_drilldown.php` + `themes/default/html/crm/revenue_drilldown.php` — new.** AC6.

   **Why not the existing `?conditions=` mechanism:** `generatePageUrlParams()` keys parsed conditions by **column name** — `$allConditions[$conditionsbyExplode[0]] = array("condition" => …, "value" => …)` (`includes/core_functions.php:2865-2881`). Two conditions on the same column therefore collide and the second overwrites the first, so a bounded range (`next_invoice_due >= today AND <= today+30`) **cannot be expressed in the URL**, even though `convertConditionsToDbArray()` supports `more_than_equal_to` / `less_than_equal_to` individually (`:2661-2690`). A one-sided `?conditions=next_invoice_due:less_than_equal_to:<date>` on `/table/crm_deals` would also silently include everything already past due. Windowed drill-down needs its own view; a `stage`- or `contract_status`-style single-value drill-down could reuse `/table/crm_*?conditions=…` and should.

5. **`modules/crm/setup_menu.php` — new.** Idempotent seeder in the shape of `modules/finance_management/setup_menu.php:19-97`: inserts a sidebar entry with `external_link = "crm/revenue_dashboard"`, which `getMenus()` resolves to `_admin_url . "/crm/revenue_dashboard"` (`includes/core_functions.php:1653-1657`). Skips if present. **Does not** touch `spa_dashboard_counters` or `spa_form_layouts`.

6. **`database/migrations/…_SAN-274_revenue_dashboard_indexes.sql` — only if profiling shows it is needed.** `crm_deals` already indexes `next_invoice_due` and `contract_end`, and `crm_invoices` already indexes `status` and `due_date` (`2026_08_07_SAN-270_crm_registry.sql:97-99`, `2026_08_07_crm_full_data_model.sql:66-69`). Expect no new index at 28 clients. **No new table, no new column** unless OQ-1 resolves to Option B, in which case that column and its writer are a separate issue.

**Not in this repo, not in this spec:** the FY Revenue / rolling-window formula itself while it remains SAN-263/SAN-264 in `sanchiconnect-saas-tenants`. If OQ-1 resolves to Option A or C, those issues must be re-scoped or re-labelled in Linear first — not absorbed silently here.

## Contracts & invariants

- **Flags:** none. This repo has no feature-flag mechanism; visibility is role-based (`spa_admin_roles`).
- **API:** none. No REST endpoint is added or consumed. Note the panel is not inert in general — `modules/edit.php` fires a live `PATCH api/v1/public/global/saas/settings` at a tenant's backend when a `tenant_users` row is edited (`CLAUDE.md:70`) — but no path in this spec touches `tenant_users`.
- **Events:** none.
- **Invariants at risk:** none of the six. Nothing here touches flag names (#1), the `sc-saas-backend` API contract (#2), the tenant-verification shape (#3), the auth model (#4), or the PowerPitch contract (#6). Invariant #5 (tenant scoping) does not apply — this is a platform-level tool with no tenant-scoping rule (`CLAUDE.md:88`, `module.spec.md:192`), and `tenant_scoped: false` is set accordingly: the `crm_*` tables are SanchiConnect's own client book, not any tenant's data.
- **Shared-DB caution:** the tenants MySQL DB is shared with `sanchiconnect-saas-tenants` (NestJS/TypeORM). This spec adds **no** table and **no** column, so it introduces no schema-collision risk. That protection disappears the moment OQ-1 resolves to Option B.
- **New endpoint auth model, stated explicitly** (workspace guardrail on unauthenticated endpoints): `modules/crm/revenue_dashboard.php`, `revenue_drilldown.php` and `setup_menu.php` are page routes through `index.php`, each starting with `checkLoggedIn()` plus a role check. **No AJAX handler is added under `modules/ajax/`** — that directory's files are CSRF-gated but not login-gated (`CLAUDE.md:63`), and revenue figures must not be reachable that way.

## Test plan

This repo has no test suite and no CI (`CLAUDE.md:7`); the workspace "guardian" skill does not exist. Substituted verification, in the shape SAN-270 and SAN-271 used:

- **Lint:** `php -l` on every edited/added PHP file.
- **Reconciliation script (AC4)** — `database/seeds/` style standalone script: loads a fixture into `crm_clients`/`crm_deals`/`crm_invoices`, calls each total function and its `*ByClient` counterpart through `includes/crm_revenue_functions.php`, and asserts `total - array_sum(byClient) === 0.00` for all six tiles. Must also assert the drill-down view's own footer total equals the tile. Fixture rows removed afterwards; all `crm_*` tables confirmed back to 0, as SAN-270/271 did.
- **Boundary cases the fixture must contain** (all legitimate per the SAN-270 migration comments): a deal with `contract_end IS NULL` (open-ended — must not be treated as zero-revenue, `2026_08_07_SAN-270_crm_registry.sql:74-78`); a client with two deals from a renewal (`version` > 1); a client with no deal at all (SAN-271 AC6 imports these); an invoice exactly on the window boundary date; a paisa-level amount that would expose float rounding — `deal_amount` is `DECIMAL(14,2)`, so comparisons must not go through PHP floats.
- **AC7:** load the page twice with a row changed in between; the second load must reflect the change. Confirm no `Cache-Control` header is emitted by the module and no derived value is written to `$_SESSION`.
- **AC8:** log in as each configured role and confirm what is and is not reachable — expected to fail as stated; record the result rather than working around it.
- **Environment note for whoever runs the above:** MySQL here runs **without `STRICT_TRANS_TABLES`** (`SELECT @@SESSION.sql_mode` returns only `ANSI_QUOTES`), so a bad insert coerces rather than errors — fixture setup must verify what actually landed, not assume the insert failed loudly (`specs/features/SAN-270-crm-client-deal-registry-admin.spec.md:82-88`).
- **cross-repo:** none required — single repo, no contract touched. `/audit-contract`, `/trace-flag` and `/check-isolation` all no-op for this change; run none of them as a gate, and say so rather than claiming a green gate that was never meaningful.

## Rollout

1. Land `includes/crm_revenue_functions.php` + the module + template, unreferenced by any menu. Nothing is visible.
2. Run `modules/crm/setup_menu.php` once, in the shape of the finance seeder. The dashboard appears for permitted roles only.
3. All tiles read ₹0 until SAN-271's import runs. **Do not treat ₹0 as a defect and do not seed placeholder data to make the dashboard look alive** — SAN-271 AC6 established that missing data stays blank rather than invented, and a fabricated total on a board-reporting screen is worse than an empty one.
4. Reconcile against Finance's manual sum (AC4/AC5) only after the real import lands and its own reconciliation reports 0 mismatched.

No migration, no flag, nothing to roll back beyond deleting the menu row.

## Out of scope

- The FY Revenue and rolling-window formulas themselves (SAN-263, SAN-264 — different repo, unbuilt).
- Invoice generation and the Overdue lifecycle transition (SAN-266, SAN-267, SAN-268) — the Overdue tile reads whatever `crm_invoices` holds; nothing here creates or ages an invoice.
- Other pipeline views. The Renewals Radar is its own pending issue (`specs/features/ai-native-crm-pending-linear-issues.md:40-60`).
- Charting beyond the tiles; exporting the dashboard (both explicitly out per the issue).
- Any operator UI for `crm_invoices` — deliberately not engine-registered (`module.spec.md:147`), and its own pending issue (build order #14).
- Row-level per-Account-Manager filtering — the gap SAN-270 left open (below), and a separate issue.

## Known gaps

**AC8 is not deliverable in this repo as written**, for two independent reasons:

1. **There is no Leadership role, and roles are not app-definable.** The configured set is `super_admin`, `reviewer`, `recruitment_partner`, `jury`, `developer`, `program_manager`, `analyst` — each a `define()` of an ENV-supplied ID at `config/config.php:125-145`, matched against `$_SESSION['admin_roles']['code']` (`includes/core_functions.php:577-589`) or `['id']` (`:2270-2274`). `grep -i leadership` across the repo returns hits only in `vendor/`. A Leadership role means a new `spa_admin_roles` row **and** a new ENV-backed constant deployed to every environment — an ops/config change, not a code change, and one nobody in this spec is authorised to invent.
2. **Column-level visibility does not exist.** Access control here has exactly two granularities: menus and tables (`spa_admin_roles.menus` / `.tables` JSON, `getMenus()` at `includes/core_functions.php:1615-1723`, `checkTableAccess()` at `:1601-1613`), plus boolean permission flags. The column list a table view renders comes from `spa_table_view_admin.table_columns` via `getTableColumns()` (`:1077-1114`, read at `modules/table.php:122-123`) — **one global list per table, with no role dimension**. So `crm_invoices.payment_reference` (`2026_08_07_crm_full_data_model.sql:60`) can be hidden from everyone or shown to everyone; "hidden from Leadership specifically" needs a new mechanism.

   The blunt instrument that *is* available — denying Leadership `crm_invoices` table access — also removes the Overdue Invoices drill-down that AC3/AC6 require for the same role. The two criteria are in direct tension.

   The mitigation actually available today: `crm_invoices` is **not** registered with the generic CRUD engine, so `payment_reference` is currently rendered nowhere at all. AC8 is satisfied *incidentally* until the invoice UI issue (build order #14) ships — which is not the same as being enforced, and must not be recorded as delivered.

This is the same class of gap as **SAN-270's AC8** (per-operator row filtering), which was **not delivered** for exactly this reason and was explicitly ruled a separate issue rather than folded in (`specs/features/SAN-270-crm-client-deal-registry-admin.spec.md:117-121`). Do not assume any row- or column-level scoping exists — none does.

**Recommended:** carve AC8 out of SAN-274 into its own `Repo: Tenants-Admin` issue covering (a) a Leadership role and (b) a role dimension on column visibility, since (b) touches `modules/table.php` and therefore **every** business table in the panel — a blast radius well beyond one dashboard.

## Open questions

A non-empty list means this spec is not approvable. OQ-1 blocks implementation outright; the rest block specific criteria.

- **OQ-1 (dev lead) — Where does the FY Revenue / rolling-window calculation live, given that the data it reads is owned by this repo and the issues that specify it (SAN-263, SAN-264) are labelled `Repo: Tenants`?** Choose A (recompute in PHP here), B (store a computed value per deal plus name its writer), or C (recommended — declare the M3 revenue engine part of `sanchiconnect-saas-tenants-admin` and re-scope SAN-263/264 accordingly). AC-14 demands zero variance between the tile and the per-client figure, and only C makes them the same code path by construction. This is the same ownership collision already recorded for `crm_invoices` vs SAN-266 — deciding both together would be sensible. **Nothing in the per-repo plan beyond step 1's file skeleton should start before this is answered.**
- **OQ-2 (product owner) — What is the FY boundary and which date decides a payment's FY?** Indian FY (1 Apr – 31 Mar) is assumed throughout but is `[NOT SPECIFIED IN SOURCE]` here, since the BRD PDF is absent from this machine. Also: is a deal's revenue attributed by *payment/instalment date* or by *contract period covered*? The SAN-270 migration is explicit that contracts are prepaid and `contract_end` is a deactivation date, never a payment date (`2026_08_07_SAN-270_crm_registry.sql:74-78`) — the two attributions therefore give different FY totals for the same deal.
- **OQ-3 (Finance) — What exactly is "overdue", and which amount does the tile show?** `crm_invoices.status` has an `Overdue` enum value (`2026_08_07_crm_full_data_model.sql:58`) but nothing sets it yet — the A2 automation is SAN-268, unbuilt. Is the tile `status = 'Overdue'`, or computed live as `due_date < today AND status IN ('Sent', …)`? And is the value `total_amount` (incl. GST) or `net_payable` (after TDS)? Both columns exist; they differ.
- **OQ-4 (Finance) — Does the ₹44,70,200 in AC5 include GST?** `crm_deals.deal_amount` is documented as "Total ACV" with no GST flag, while `crm_invoices` carries `amount_excl_gst`, `gst_amount` and `total_amount` separately. A tile built on one basis will never reconcile against a manual sum built on the other, and this is precisely the reconciliation AC4 puts in front of Finance.
- **OQ-5 (product owner) — Do the 30/60/90/120-day windows nest or partition?** i.e. does the 60d tile include the first 30 days (cumulative) or cover days 31–60 only? "Revenue Next 60d" reads cumulative, but the four tiles then sum to more than the pipeline, which will be questioned the first time someone adds them up.
- **OQ-6 (dev lead + product owner) — Is AC8 accepted as carved out of this issue?** Per "Known gaps", it needs a Leadership role (an ENV/DB config change across environments) and a role dimension on column visibility that would touch `modules/table.php` and therefore every table in the panel. Confirm it moves to its own issue rather than being reported as delivered because `crm_invoices` happens to be unregistered today.

## Linear

**No Linear records were created or modified for this spec** — the workspace is at its free-tier issue limit (`specs/features/ai-native-crm-pending-linear-issues.md:8`), and SAN-274 already exists under the AI-Native CRM project, assigned to Sandeep, `Repo: Tenants-Admin` + `Feature`, priority High (2), state Backlog. No new project or issue is warranted: this spec covers exactly one repo and one existing issue.

When OQ-1 is answered, two follow-up issues are expected — the AC8 carve-out, and whatever re-scoping SAN-263/SAN-264 need. Both require Linear capacity that does not currently exist.

---

## Implementation addendum (2026-08-07) — built and verified

**OQ-1 resolved by the dev lead: Option A — duplicate the canonical formula in PHP in this repo.** The drift risk that option carries is accepted, and mitigated rather than ignored (see below). OQ-2/3/4/5 were closed from the BRD text itself, which the drafting pass did not have on disk:

| OQ | Resolution | Source |
|---|---|---|
| OQ-2 | India FY, Apr 1 → Mar 31, resolved dynamically from today. Revenue attributed by **installment payment date**, not period covered. | BRD §5.3.1, §5.3.2 |
| OQ-3 | Overdue = Sent and unpaid more than **3 days** past due. Computed live rather than trusting `crm_invoices.status`, since SAN-268's A2 automation that would set it is unbuilt. Tile shows `total_amount`. | BRD §5.4 |
| OQ-4 | FY Revenue is **ex-GST** — `deal_amount` is ACV, and the BRD's ₹44,70,200 derives from ACV. GST exists only at invoice level. | BRD §5.3.3, §5.4 |
| OQ-5 | Windows are **cumulative**, not partitioned: `floor((W − daysUntil) / periodDays) + 1` means 30d ⊂ 60d ⊂ 90d ⊂ 120d. The tiles overlap and must never be summed — stated on the page itself. | BRD §5.3.4 |
| OQ-6 | AC8 carved out, as with SAN-270's AC8. Needs its own issue. | — |

### Files

| File | Role |
|---|---|
| `includes/crm_revenue_functions.php` | The single revenue source — FY revenue, rolling windows, overdue, per-client and totals, plus `crmRevenueSelfCheck()` |
| `modules/crm/revenue_dashboard.php` | Controller. No SQL, no arithmetic. |
| `themes/default/html/crm/revenue_dashboard.php` | Six tiles + inline FY breakdown + overdue table |
| `modules/crm/revenue_drilldown.php` + template | AC6 for the windowed tiles |
| `database/migrations/2026_08_07_SAN-274_revenue_dashboard_menu.php` | Idempotent menu entry under the CRM parent |

### How AC-14 is guaranteed

Every `*Total()` is literally `array_sum()` over its own `*ByClient()` counterpart. The tile and the drill-down are the same code path, so they cannot drift apart — the requirement holds by construction rather than by discipline.

### Drift mitigation for the duplicated formula

`crmRevenueSelfCheck()` runs the BRD §5.3.3 reference values through this implementation using synthetic deals (no database reads) and **renders its result on the dashboard itself**. If this PHP implementation ever diverges from the canonical values, whoever is reading the numbers sees a red banner saying so, rather than the divergence sitting in a test log. When SAN-263 ships, reconcile the two implementations or delete one — do not leave both.

### Verification (2026-08-07)

- `php -l` clean on all five new PHP files.
- **Formula self-check: 9/9** against BRD §5.3.3 anchors, including both named regressions — Govt of Chhatisgarh **₹0** and SINE Edge **₹3,19,200**.
- Boundary probes correct: half-yearly last payment Mar 29 2026 → ₹0; one-time Mar 31 2026 → ₹0; one-time Apr 1 2026 → ₹1,45,000; monthly open-ended from Apr 1 2026 → ₹1,20,000.
- **End-to-end against all 20 BRD reference clients loaded into the live DB: total = ₹44,70,200 exactly, 0 per-client mismatches (AC5 PASS).**
- **AC4 PASS** — `crmFyRevenueTotal()` ≡ sum of `crmFyRevenueByClient()`.
- Menu migration idempotent; test rows removed, tables back to 0.

No automated test suite was added — this repo has none and no CI.

### Finding — a one-day change in `contract_end` moves ₹4,85,000

Because the contract end date is never itself a payment date, an annual contract ending **exactly** on its anniversary excludes that anniversary payment:

```
start 2025-10-01, end 2026-10-01  ->  FY 26-27 = ₹0
start 2025-10-01, end 2026-10-02  ->  FY 26-27 = ₹1,10,000
```

BRD §5.3.3 gives Startup Singam and CII-CIES Renew only as "Oct 2025 → Oct 2026", yet expects the full ACV for both — so both contracts must end *after* the anniversary. Together they are worth **₹4,85,000, about 11% of the ₹44,70,200 total**. The exact dates must come from the Notion source before AC5 can be signed off on real data. Tracked as SAN-271 OQ-C.

### Finding — the shared counter engine fabricates numbers on the demo host

`includes/counter_generator.php:40-42`:

```php
if(hostname == "adm.demo.sanchiapp.com"){ $counter['result'] = $counter['result'] * rand(43, 55); }
```

Any dashboard built on `spa_dashboard_counters` would show randomised revenue on that host. This is the primary reason SAN-274 is a custom module rather than counter config (DD-1). **The same multiplier affects every existing counter tile on that host** — worth its own issue.

### Operational dependency worth knowing

The rolling-window tiles read `next_invoice_due`. A stale value that has drifted into the past yields `daysUntil = 0` and therefore contributes to *every* window — correct per the BRD formula, but it inflates the forecast. Keeping that field current is SAN-268's A4 automation. Until A4 ships, the windows are only as accurate as manual maintenance of `next_invoice_due`.
