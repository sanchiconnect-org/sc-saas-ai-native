---
id: SAN-271
title: Import SanchiConnect's existing clients into the CRM
type: feature
status: canceled  # 2026-10-19: AI-Native CRM project shut down, never implemented (Linear issue Canceled)
linear: https://linear.app/sanchiconnect/issue/SAN-271/all-28-existing-clients-are-in-the-crm-with-their-real-contract-terms
owner: sandeep.k@sanchiconnect.com
repos: [sanchiconnect-saas-tenants-admin]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: false
depends_on: [SAN-270]
created: 2026-08-07
---

# Import SanchiConnect's existing clients into the CRM

Governed by **AI-Native CRM BRD v1.0** §5.3.3 (reference verification table) and master criterion AC-01.

## Problem

The CRM is worthless empty. SanchiConnect's 28+ client accounts and ~₹4.5 crore of annualised contract revenue live in Notion; until they are in the CRM with correct field values, every downstream figure has nothing real to compute over.

## Status — importer complete, import not yet run

**The machinery is built, tested and ready. No real client data has been imported, because the Notion export has not been supplied.** The issue stays open until it lands.

## Acceptance criteria

- [ ] AC1 — all 28 clients exist with org type, GSTIN, PAN, stage, account manager populated — **blocked on the export**
- [ ] AC2 — each client's deal carries correct amount, terms and dates — **blocked on the export**
- [x] AC3 — clients with more than one contract term import as separate deals, not merged
- [ ] AC4 — PO spot-check of 5 random records — **blocked on the export**
- [ ] AC5 — the named reference clients import with their BRD §5.3.3 values — **mechanism verified against a fixture; awaiting real data**
- [x] AC6 — genuinely missing source data imports blank, not zero-filled and not invented
- [x] AC7 — re-running the import does not duplicate any client
- [ ] AC8 — Notion marked read-only or archived once verified — **an ops step, after the import**

## Design decisions

### DD-1 — GSTIN and PAN become nullable (decided 2026-08-07 by dev lead)

SAN-270 created `crm_clients.gstin`/`pan` as NOT NULL with `CHECK (<> '')`, per BRD §5.1 which marks both Required. AC6 requires missing values import blank. Direct conflict.

Resolved by making both nullable at the database level while keeping them mandatory where they matter: BRD §5.1 itself says GSTIN is "required for invoice generation" and PAN "for TDS compliance" — both invoice-time concerns, not client-creation ones. The `spa_data_management` **`required` rows are deliberately left in place**, so an operator adding a client through the Add form must still supply both. Only the bulk importer, which bypasses the form, may write blanks.

Migration: `database/migrations/2026_08_07_SAN-271_relax_client_tax_ids.php` (idempotent — inspects `information_schema`, since MySQL has no `DROP CHECK IF EXISTS`).

### DD-2 — CSV in, not a Notion API integration

The import is a one-way, one-time migration, not an ongoing sync. A documented CSV contract keeps it inspectable and re-runnable without credentials or a Notion dependency.

## Per-repo plan

### sanchiconnect-saas-tenants-admin

- `database/migrations/2026_08_07_SAN-271_relax_client_tax_ids.php` — DD-1
- `database/seeds/import_crm_clients.php` — the importer
- `database/seeds/crm_clients_import.example.csv` — the CSV contract, by example

**Importer behaviour**

| Concern | Handling |
|---|---|
| Blank source field | Stored `NULL`. Never `""`, never a stand-in. AC6's mechanical guarantee. |
| Idempotency | Clients match on `name`; deals on (client, `contract_start`, `payment_terms`); contacts on (client, `email`) or (client, `name`). Existing rows update in place. |
| Multiple terms per client | One CSV row per deal, repeating the client columns. Verified: CII-CIES → 1 client, 2 deals. |
| `contract_status` | Derived from `contract_end`, never read from source. |
| Unparseable date/amount | Reported as an error, not coerced — a wrong contract date silently corrupts every revenue figure downstream. |
| Unknown account manager | Falls back to the first operator **and says so** in the report. |
| Client with no contract data | Client imports, no deal fabricated (DSCI-NCoE, UPES Runway). |
| Reconciliation | Every run compares what landed against the BRD §5.3.3 table and prints OK / MISMATCH / ABSENT per client. |

Flags: `--dry-run` (parse, validate, report, write nothing), `--report-only` (reconcile what is already there), and `--emit-sql[=path]` (below).

### SQL output — `--emit-sql`

For running the import as plain SQL instead of through PHP:

```
php database/seeds/import_crm_clients.php <file.csv> --emit-sql
```

Writes `database/seeds/crm_clients_import.generated.sql` and touches no database. It reuses the importer's own normalisation, so the SQL carries identical blank→NULL, date-format and enum handling — regenerate it from the CSV rather than hand-editing, or the two paths drift.

The emitted SQL is re-runnable by construction: clients upsert via `INSERT … AS new ON DUPLICATE KEY UPDATE` on the UNIQUE `name`; contacts and deals use `INSERT … SELECT … WHERE NOT EXISTS`, with deals matched on (client, `contract_start`, `payment_terms`) so a renewal term lands as its own row instead of overwriting the base contract. Wrapped in `START TRANSACTION` / `COMMIT`.

The `NOT EXISTS` subqueries wrap the target table as `(SELECT * FROM …) alias` to sidestep MySQL error 1093.

Verified: applying the generated file twice left counts unchanged (8 clients / 7 deals / 1 contact both times), reconciliation 8 matched / 0 mismatched.

## Verification

Run 2026-08-07 against a fixture, on the live shared DB, with all fixture rows removed afterwards (all three tables confirmed back to 0).

- `php -l` clean.
- **Dry run** — 8 rows parsed, 7 deals, 1 correctly skipped, nothing written; reconciliation correctly reported all 20 reference clients ABSENT.
- **Live import** — 8 clients / 7 deals / 1 contact created. Reconciliation: **8 matched, 0 mismatched**, 12 absent (not in the fixture).
- **AC7 idempotency** — identical re-run produced **0 created, 8 updated**. No duplicates.
- **AC3 multi-deal** — CII-CIES imported as 1 client with 2 deals (₹250,000 expired, ₹375,000 active), `contract_status` correctly derived for each.
- **AC6** — DSCI-NCoE (no contract data) imported as a client with no fabricated deal; blank GSTIN/PAN stored NULL.

No automated test suite was added — this repo has none and has no CI. The above is a scripted functional run, not unit tests.

### Environment finding

`date_default_timezone_get()` **fatals** on this machine — "Timezone database is corrupt" — because no valid default timezone is configured. The app dodges it by setting the zone from the `spa_settings.timezone` row (`includes/core_functions.php:1212`). Any standalone script in this repo must do the same before touching a date function; the importer now does. Worth fixing at the PHP/ini level rather than per script.

## Open questions

- **OQ-A (PO)** — BRD §5.3.3 lists "CII-CIES" and "CII-CIES Renew" as two separate rows, i.e. two clients, but AC3 describes one client holding both terms. The importer supports either shape. Confirm which the PO wants before the real import, because it changes what "28 clients" counts.
- **OQ-B (PO)** — the BRD reference table names **20** clients; AC1 requires **28**. The other 8 exist only in Notion. The export must cover all 28.
- **OQ-C (Finance)** — several BRD rows give "In FY 26-27" or "—" rather than a date. Real dates must come from the Notion source; where the source has none, the PO decides rather than the importer approximating.

## What is needed to finish

1. Notion pipeline exported to CSV matching `crm_clients_import.example.csv`, saved as `database/seeds/crm_clients_import.csv`.
2. `php database/seeds/import_crm_clients.php database/seeds/crm_clients_import.csv --dry-run` — review the report.
3. Same command without `--dry-run`.
4. PO spot-checks 5 records (AC4); confirm reconciliation shows 0 mismatched.
5. Mark Notion read-only (AC8).
