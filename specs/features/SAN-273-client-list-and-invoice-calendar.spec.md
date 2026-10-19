---
id: SAN-273
title: Client list and invoice-due calendar
type: feature
status: canceled  # 2026-10-19: AI-Native CRM project shut down, never implemented (Linear issue Canceled)
linear: https://linear.app/sanchiconnect/issue/SAN-273/finance-can-scan-every-client-as-a-sortable-list-and-see-upcoming
owner: sandeep.k@sanchiconnect.com
repos: [sanchiconnect-saas-tenants-admin]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: false
depends_on: [SAN-270, SAN-271, SAN-274]
created: 2026-08-08
---

# Client list and invoice-due calendar

Governed by **AI-Native CRM BRD v1.0** §5.5 — "List — All Clients" and "Calendar — Invoice Due". Part of the AI-Native CRM project, M5 Pipeline Views, Phase 5.

## Problem

Finance cannot answer "which accounts are worth the most this year?" or "what is due to be invoiced in March?" without exporting data and sorting it by hand. There is no view that ranks clients by revenue, and no time-based view of when money is due.

## Acceptance criteria

Verified 2026-08-08 — **22 checks pass, 0 fail**.

- [x] AC1 — list shows client name, org type, payment terms, ACV, FY Revenue, contract status, next invoice due
- [x] AC2 — sorts by FY Revenue descending by default, and by any visible column
- [x] AC3 — filters by contract status
- [x] AC4 — calendar places each Next Invoice Due on its date, month and week views
- [x] AC5 — each calendar entry shows client name and installment amount
- [x] AC6 — calendar filters by amount above a threshold and Status = Active
- [x] AC7 — both views reflect a change without a manual refresh step beyond reloading
- [x] AC8 — both stay usable at 500 client records

## Design decisions

### DD-1 — The list is one row per deal, not per client

Four of the seven columns AC1 names (payment terms, ACV, contract status, next invoice due) are **deal** attributes, and a client may hold several deals — CII-CIES has a base contract and a renewal. Collapsing to one row per client would have to hide or arbitrarily pick between them. A client with a single deal, the common case, renders exactly as a client row would.

**For PO confirmation:** BRD §5.5 calls this "List — All Clients", which could be read as strictly client-level. The current shape is the only one that can show all seven columns honestly.

### DD-2 — Row building, sorting and filtering live in `includes/crm_revenue_functions.php`

`crmClientListRows()` and `crmInvoiceCalendarEntries()` hold the logic; the controllers only translate `$_GET` and render. This is not tidiness — the controllers call `checkLoggedIn()` and cannot be driven headlessly, so logic left inside them could only be checked by eye. Moving it out made AC2/AC3/AC6 executable in a test harness.

### DD-3 — FY Revenue comes from the same function the dashboard sums

The list reads `crmFyRevenueByClient()`, exactly as SAN-274's tiles do. The two views cannot disagree about any client's figure, which is the same structural guarantee that makes AC-14 hold.

### DD-4 — Sorting happens in PHP, not SQL

`fy_revenue` is computed, not stored, so it cannot be an `ORDER BY`. Every column sorts through one comparator over the in-memory row set. Measured at 500 records rather than assumed — see below.

### DD-5 — `min_amount` filters the installment, not the ACV

The calendar is about cash landing on a date, so the threshold applies to what is actually due that day. A ₹1,20,000 monthly contract shows ₹10,000 and is excluded by a ₹1,00,000 threshold; a ₹4,40,000 one-time shows its full amount.

## Per-repo plan — sanchiconnect-saas-tenants-admin

| File | Role |
|---|---|
| `includes/crm_revenue_functions.php` | `crmClientListRows()`, `crmInvoiceCalendarEntries()` added |
| `modules/crm/client_list.php` + template | Sortable list, status filter |
| `modules/crm/invoice_calendar.php` + template | Month/week grid, amount + active filters |
| `database/migrations/2026_08_08_SAN-273_list_calendar_menu.php` | Idempotent menu entries under the CRM parent |

No schema change. No new table, no new column.

## Verification (2026-08-08)

- `php -l` clean on all five files.
- **22 checks pass, 0 fail** against a live fixture, all rows removed afterwards (tables confirmed back to 0).
  - AC1 — one row per deal confirmed: 5 clients with 6 deals produced 6 rows; all 7 columns present.
  - AC2 — default order is FY Revenue descending; asc/desc verified for all 7 sortable columns.
  - AC3 — Active → 5 rows, Expired → 1 row, no leakage.
  - AC4/AC5 — 6 distinct due dates bucketed; Monthly ₹1,20,000 → ₹10,000, Half-Yearly ₹3,00,000 → ₹1,50,000, One-time ₹4,40,000 → full amount not a twelfth.
  - AC6 — threshold is inclusive `>=` and monotonic across 0 / 10,000 / 10,001 / 150,000 / 150,001 / 440,000 / 900,000; `active_only` excludes the Expired deal with zero non-active survivors.
  - AC8 — **500 clients + 500 deals: list built in 1,129 ms, calendar in 43 ms**, both against the remote shared database.
- Menu migration idempotent (2 inserted, then 0).

No automated test suite was added — this repo has none and no CI.

### Not verified

**The rendered pages have never been loaded.** Both controllers require an authenticated session and no login credentials were available, so the templates are unverified beyond `php -l` and route resolution (`/crm/client_list` and `/crm/invoice_calendar` both 302 to login, proving `index.php` resolves them). In a repo whose documented landmine is *forms silently rendering blank*, this gap matters — load both pages before sign-off.

## Known gaps

**The calendar plots only the next invoice per contract, not the full schedule.** `crm_deals` stores a single `next_invoice_due`, so navigating past that date shows an empty month even while the contract runs. This matches the BRD wording ("showing Next Invoice Due dates") and the data that exists, and the limitation is stated on the page itself. Projecting the full prepaid schedule forward from `contract_start` via `crmPeriodMonths()` would be a real improvement — worth its own issue.

`next_invoice_due` advances when an invoice is marked paid, which is SAN-268's A4 automation and unbuilt. Until it ships the field is only as current as manual upkeep, and a stale value drifted into the past will sit in the calendar's earliest visible day.

## Open questions

- **OQ-A (product owner)** — confirm DD-1: is one row per deal the right shape for "List — All Clients", or is a client-level roll-up wanted with deal detail behind a drill-down?
- **OQ-B (product owner)** — should the calendar project the full prepaid schedule rather than only the next due date? It changes the view from "what is invoiced next" to "what is expected all year".

## Out of scope

Kanban board (SAN-272), cohort view and CSV export (SAN-275), Renewals Radar (pending), editing records from either view, and the FY Revenue calculation itself (SAN-274).
