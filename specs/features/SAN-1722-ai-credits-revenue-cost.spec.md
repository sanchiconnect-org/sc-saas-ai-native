---
id: SAN-1722                    # lowest per-repo issue; set: SAN-1722 tenants, SAN-1723 analyzer, SAN-1724 admin, SAN-1725 tenants-admin
title: AI Credits Revenue & Cost (P&L) incl. Serper + Firecrawl
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/project/ai-credits-revenue-and-cost-pandl-incl-serper-firecrawl-5d0f4391b560
owner: nirmal.s@sanchiconnect.com
repos: [tenants, ai-startups-analyzer, admin, sanchiconnect-saas-tenants-admin]
contracts:
  api:
    - "ai-startups-analyzer CostSummary (finalize-analysis + generate-thesis responses) gains serper_calls:int and firecrawl_scrapes:int (default 0). Additive; existing fields unchanged. Consumer: sc-saas-admin."
  flags: []
  events: []
tenant_scoping: true
depends_on: [FT-005]
created: 2026-10-06
---

# AI Credits Revenue & Cost (P&L) incl. Serper + Firecrawl

## Problem
Management wants to see what AI evaluation earns and costs. Revenue from AI Credits is recorded (`ai_credit_orders`), and LLM
cost is recorded per run and per ledger DEBIT (`llm_cost_usd`). But the analyzer's **enrichment** calls, which are
**on in production** (`ENABLE_ENRICHMENT=1`, confirmed by the product owner 2026-10-06), are **not counted or priced anywhere**:
- **Serper** (`google.serper.dev/search`): 1 search per applicant.
- **Firecrawl** (`api.firecrawl.dev/v1/scrape`): 1 scrape per applicant that has a website.

Thesis enrichment can also make 1 search + 1 scrape per `generate-thesis` call.

There's also no report putting revenue next to the full cost.

## Decisions (product owner, 2026-10-06)
- **Owner:** Nirmal Singh (single owner, multi-repo).
- **Starting cost settings** (editable by operators):
  - Serper **$1.00 per 1,000 searches**
  - Firecrawl **$0.0053 per scrape**
  - USD→INR **85**
  - Payment gateway fee **2%**
- **The analyzer reports counts only.** Prices live in tenants-admin settings, so price changes never need an analyzer deploy.

## Evidence (code, 2026-10-06)
- **Enrichment code:** `ai-startups-analyzer/api/app/core/enrichment.py`
  - `_search_serper()` and `_scrape_firecrawl()` each make one POST through `_post_json()`, which retries up to
    `ENRICH_MAX_RETRIES` on 429/5xx.
  - `enrich_applicant()` runs the search when `search_active()`, plus the scrape when `website_active()` and a website exists.
  - `enrich_entity()` is used for thesis enrichment.
- **Per-batch cache:** `routes.py` `_load_or_build_enrichment()` caches per batch in `enrichment.json`, so a cache hit makes 0 calls.
- **LLM cost:** `Batch.cost_usd`/tokens are rolled up in `finalize-analysis` into `CostSummary`, which is also returned by
  `/generate-thesis/`. Prices come from `app/core/pricing.py`.
- **Ledger:** `sc-saas-admin/includes/ai_credits_functions.php` writes `llm_*` from `$costData` in `settleAiCredits()`
  (analysis) and `debitAiCreditsInstant()` (thesis, rescore retries).
- **Revenue:** `ai_credit_orders.amount_inr` is the package price **before GST** (`ai-credits.service.ts`: `amountInr:
  pkg.priceInr`, `grandTotal` = price + tax). GST lives on `ai_credit_invoices`.

## Design
### 1. tenants (SAN-1722)
- `AiCreditLedgerEntity` gains `serper_calls INT NULL` and `firecrawl_scrapes INT NULL`. NULL means not tracked.
- The change is additive. This repo writes neither column.

### 2. ai-startups-analyzer (SAN-1723)
- **Counting:** count **billable** calls, meaning a final HTTP 2xx after retries. A failed call (error after retries) counts 0.
  - The counter is a `ContextVar`-scoped `EnrichmentUsage` (`enrichment.track_usage()`). It is incremented inside `_post_json()`
    right after `raise_for_status()`, so a 2xx with an unusable body still counts, because it was billed.
  - `diagnostics()` (operator probe) is deliberately not counted.
- **Storage:** run-level, on `Analysis.serper_calls` / `Analysis.firecrawl_scrapes`, **not per Batch**.
  - Pre-enrichment (`_pre_enrich_and_score`) covers every batch of a run in one pass, so a per-batch split doesn't exist.
  - All three passes atomically add to the row (`_add_enrichment_usage`, shielded write): pre-enrich, the per-batch fallback in
    `_load_or_build_enrichment`, and `/re-enrich/`. A cache hit makes 0 calls.
  - The columns are added on boot by `_sync_missing_columns()`, so no SQL migration is needed.
- **Response:** `finalize-analysis` copies the run totals into `CostSummary`. `generate-thesis` reports its own call's counts.
- **No prices** in the analyzer.
- **Tests:** `api/tests/test_enrichment_usage.py` (stdlib unittest + `httpx.MockTransport`, no network).

### 3. sc-saas-admin (SAN-1724)
- **`aiCreditEnrichmentCounts($cost, $domain, $runRef)`** (since replaced by `aiCreditRunCostDelta()`, SAN-1735) returns `[]`, so nothing changes, unless the analyzer sent counts AND
  the ledger columns exist (cached `SHOW COLUMNS` guard).
  - For a run, the analyzer counts are cumulative, so it returns only the part **not already on that run's DEBIT rows**
    (`$runRef`, `$runRef_retry`, `$runRef_extra_*`). Extra/retry debits therefore never count the same calls twice.
- **Call sites:** the three AI Analysis settle/debit sites add the result with `+`/`array_merge`. The thesis debit passes the
  thesis call's counts.
- **`aiCreditWithEnrichmentFields()`** appends the two keys to the ledger insert/update only when present.
- **No regressions:** signatures, call-site argument lists and charging are unchanged. Without counts, the ledger SQL is
  byte-identical to before, and deploying admin before tenants is safe.

### 4. tenants-admin (SAN-1725): AI Credits → Revenue & Cost
- **Settings:** `spa_settings` rows with `type=ai_credits_costs`: `usd_inr_rate`, `serper_usd_per_1000`, `firecrawl_usd_per_scrape`,
  `gateway_fee_pct`. Defaults as above; saved from the page.
- **Filters:** date range (default this month), tenant (domain), task type.
- **KPIs:**
  - **Revenue** = Σ paid `ai_credit_orders.amount_inr` (before GST).
  - **Gateway ₹** = revenue × fee %.
  - **Credits:** sold (Σ `credits_ordered`, paid), granted (ledger CREDIT/GRANT), used (ledger DEBIT by task).
  - **LLM ₹** = Σ `llm_cost_usd` × FX.
  - **Serper ₹** = Σ `serper_calls` / 1000 × $/1k × FX.
  - **Firecrawl ₹** = Σ `firecrawl_scrapes` × $/scrape × FX.
  - **Total cost** and **gross margin ₹ / %**.
- **Tenant × month table:** the same metrics plus the unspent wallet balance, with CSV export. Ledger rows with NULL counts are
  shown as "not tracked" (older runs), not as ₹0.
- **Unit economics:**
  - For each active package: ₹/credit (`price_inr / credits`), and revenue per applicant = ₹/credit × the
    `ai_analysis` credits_per_unit.
  - **Actual** average cost per applicant over tracked rows: (LLM + Serper + Firecrawl) ÷ applicants (`applicant_count`).
  - Margin per applicant, ₹ and %.
- **Rules:** read-only over the shared tenants DB, except the settings save. Same operator auth as the other AI Credits pages.

## Non-regression (primary acceptance)
- AI Analysis billing (reserve → settle, refund, instant debit, the 6 h reconcile) is unchanged. Proven by a before/after
  harness with no counts present.
- Analyzer responses are unchanged apart from the two new integer fields.
- No real Serper/Firecrawl/LLM calls in any test; HTTP is mocked.

## Verification (2026-10-06)
- **Analyzer:** 7/7 unit tests pass, all HTTP mocked. They cover:
  - search per applicant, scrape per website
  - failures after retries count 0
  - thesis 1+1
  - disabled = no calls
  - nested isolation
  - the `CostSummary` defaults
- **Admin:**
  - A mock-DB harness shows the ledger/wallet calls are **byte-identical to HEAD** with no counts, with or without the columns.
  - Run against a throwaway MySQL 9.6 (strict, ONLY_FULL_GROUP_BY) using the real `core/db.php` Medoo, the wallet maths is
    identical. Counts land as settle 30/25, then retry delta 4/2, thesis 1/1, and a lookalike run ref is not subtracted.
- **Tenants-admin:**
  - The page and CSV were run on the same MySQL, before and after the columns exist.
  - Every KPI was hand-checked: FX, Serper $/1k, Firecrawl $/scrape, gateway %, cost per applicant, package margin.
  - The "not tracked" banner and rows show correctly.
- **Tenants:** `tsc --noEmit` is clean.
- **Not done:** no live end-to-end run against a real analyzer or real tenants DB. Automated coverage exists for the analyzer
  only; the PHP repos have no test suite.

## Known gaps found while building: fixed by SAN-1734 / SAN-1735
- **LLM cost double-count on `_retry` / `_extra_*` rows, and re-queued batch spend being lost:** fixed. The analyzer now
  reports `cumulative_*` spend, and the admin stores a per-run delta (`aiCreditRunCostDelta`). See
  `specs/bug-fixes/SAN-1734-1735-ai-credits-ledger-llm-cost-double-count.md`.
- **Thesis LLM cost not on the ledger:** fixed (`aiCreditCallCostData`).
- **ZenxAI voice-call cost** is still not in the P&L (out of scope, labelled on the page).

## Rollout
1. Deploy tenants first: TypeORM `synchronize` adds the two ledger columns.
2. Deploy the analyzer: `_sync_missing_columns` adds the `analyses` columns on boot.
3. Deploy admin.
4. Deploy tenants-admin, then visit `/ai_credits/setup_menu` once. It now adds the missing "Revenue & Cost" sub-menu to an
   existing AI Credits menu.

Any order is safe. Each layer degrades to "not tracked" until the layer before it is live.

## Out of scope
- ZenxAI voice-call cost in the P&L (later).
- Per-tenant negotiated prices.
- Changing what tenants are charged.
- Back-filling counts for old runs.
