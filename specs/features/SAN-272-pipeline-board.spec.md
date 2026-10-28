---
id: SAN-272
title: Pipeline board — Kanban of clients by stage
type: feature
status: canceled  # 2026-10-19: AI-Native CRM project shut down, never implemented (Linear issue Canceled)
linear: https://linear.app/sanchiconnect/issue/SAN-272/an-account-manager-can-move-a-client-through-the-pipeline-by-dragging
owner: sandeep.k@sanchiconnect.com
repos: [sanchiconnect-saas-tenants-admin]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: false
depends_on: [SAN-270, SAN-271]
created: 2026-08-08
---

# Pipeline board — Kanban of clients by stage

Governed by **AI-Native CRM BRD v1.0** §5.5 — "Kanban — Deal Stage". M5 Pipeline Views, Phase 5.

## Problem

Account Managers have no visual pipeline. Deal stage lives as a field in a row, so nobody can see at a glance how many accounts sit in Negotiation versus Renewal. Managing the pipeline means reading a table and editing fields one at a time.

## Acceptance criteria

Verified 2026-08-08 — **25 checks pass, 0 fail**.

- [x] AC1 — one column per stage: Prospect, Negotiation, Active, Renewal, Churned
- [x] AC2 — each card shows client name, ACV, account manager and account health
- [x] AC3 — dragging a card to another column changes the stage, and it survives a reload
- [x] AC4 — filterable by Account Manager, Organisation Type, and Active/Expired contract status
- [ ] **AC5 — an Account Manager sees only their own accounts — NOT DELIVERED**
- [x] AC6 — each column shows its card count and total ACV
- [x] AC7 — no visible degradation at 500 client records

## Design decisions

### DD-1 — The stage-update endpoint checks login, unlike the rest of this panel

`modules/crm/stage_update.php` calls `checkLoggedIn()` **and** `verifyCSRFToken()`.

This repo's own CLAUDE.md records that `modules/ajax/{crud_actions,email_actions,api_actions,spa_actions}.php` and `modules/aws/ajax.php` omit `checkLoggedIn()` and rely on CSRF alone. That is not an authentication check: `verifyCSRFToken()` compares the posted token against whatever the *current session* holds, and `index.php:26-28` mints a session and token for any request lacking one — so an anonymous visitor can load a public page, take the token it was handed, and POST successfully. The new endpoint deliberately does not inherit that pattern.

### DD-2 — Stage values are validated inside `crmSetClientStage()`, not at the call site

The whitelist lives with the write, so no present or future caller can put an arbitrary value in the column. Verified with an invalid stage, an injection-shaped string, a zero id and an unknown id — all rejected, with the stored stage unchanged.

### DD-3 — Board data and filters live in `includes/crm_revenue_functions.php`

Same reasoning as SAN-273 DD-2: the controllers call `checkLoggedIn()` and cannot be driven headlessly, so logic left inside them can only be checked by eye. `crmPipelineColumns()` and `crmSetClientStage()` are executable from a harness.

### DD-4 — Card ACV sums all of a client's deals; FY Revenue is not shown

A client holding a base contract and a renewal shows their combined value. FY Revenue is deliberately absent — a card answers "where is this account in the pipeline", and putting a revenue figure beside it invites being read as the dashboard's number when the two answer different questions.

### DD-5 — Optimistic move with revert on failure

The card moves immediately and the column headers recompute, then the POST goes out; if the server refuses, the card returns to its original column and a toast explains why. The alternative is a card that sits still for a network round trip on every drag.

Written in plain DOM APIs inside a `window.addEventListener('load', …)` wrapper, because inline scripts in this theme run before the footer-loaded jQuery.

## Per-repo plan — sanchiconnect-saas-tenants-admin

| File | Role |
|---|---|
| `includes/crm_revenue_functions.php` | `crmPipelineStages()`, `crmPipelineColumns()`, `crmSetClientStage()` added |
| `modules/crm/pipeline_board.php` + template | Board, filters, drag-and-drop |
| `modules/crm/stage_update.php` | POST endpoint — login + CSRF + whitelist |
| `database/migrations/2026_08_08_SAN-272_pipeline_board_menu.php` | Idempotent menu entry |

No schema change. `crm_clients.stage` already exists from SAN-270.

## Verification (2026-08-08)

- `php -l` clean on all five files.
- **25 checks pass, 0 fail** against a live fixture, all rows removed afterwards (tables back to 0).
  - AC1 — five columns in BRD order.
  - AC2 — cards carry name, ACV, account manager, health; ACV sums multiple deals (₹8,00,000 + ₹2,00,000 = ₹10,00,000).
  - AC3 — move persisted to the database and reflected on rebuild; move-back also verified.
  - AC4 — account manager → 3, org type Govt → 1, has-expired → 2, has-active → 3 (a client with no deals correctly excluded), combined filters → 1.
  - AC6 — Active column 2 cards / ₹11,50,000; a client with no deals contributes a card and ₹0.
  - AC7 — **500 clients + 500 deals: board built in 1,430 ms** against the remote database.
  - Security — invalid stage, injection-shaped stage, id 0 and unknown id all rejected with the stored value unchanged.
- Menu migration idempotent.

No automated test suite was added — this repo has none and no CI.

### Not verified

**The board has never been rendered, and the drag-and-drop has never been exercised in a browser.** The controller requires an authenticated session and no login credentials were available. Everything above tests the data and write layers; the JavaScript, the drop targets and the CSRF round trip are unverified. Load the page and drag a card before sign-off.

## Known gaps

**AC5 is not delivered — third occurrence of the same gap.** "An Account Manager sees only their own accounts unless they hold a wider role" needs per-operator row filtering, which this panel has no mechanism for: access control has exactly two granularities, menus (`getMenus()`) and whole tables (`checkTableAccess()`). The Account Manager selector on the board is a **view filter, not an access control**, and the board says so on the page.

This is the same blocker as SAN-270 AC8 and SAN-274 AC8. Three issues have now failed the same requirement. It should be lifted into one issue that adds a row-scoping mechanism, rather than being rediscovered per view — and that issue is a prerequisite for any CRM view with a role requirement.

## Open questions

- **OQ-A (product owner)** — should a drag be blocked or warned on for stage transitions that make no business sense, e.g. Churned → Prospect? Currently any column accepts any card.
- **OQ-B (dev lead)** — the row-scoping mechanism above: own issue, and what shape? It touches `modules/table.php` and therefore every business table in the panel.

## Out of scope

Cohort view and CSV export (SAN-275), Renewals Radar (pending), editing anything other than stage from the board, and AI health scoring — the board only renders the badge.
