---
id: SAN-1734
title: "AI Credits ledger: LLM cost double-counted on _retry/_extra_ rows; thesis LLM cost never recorded"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1734 , https://linear.app/sanchiconnect/issue/SAN-1735
repos: [ai-startups-analyzer, admin]
commit: <pending, branch ai_native_setup>
created: 2026-10-06
updated: 2026-10-06
---

# SAN-1734 / SAN-1735: correct LLM cost on the AI Credits ledger

Follow-up to `specs/features/SAN-1722-ai-credits-revenue-cost.spec.md` (Known gaps). The Revenue & Cost page sums `ai_credit_ledger.llm_cost_usd`, so these bugs showed up directly as overstated (or missing) cost.

## Problem
1. **Rescore double-count:** a rescore is its own analyzer run. Its settle row and its `<run>_retry` debit row were both given the same run total, so the cost was counted twice.
2. **Re-queue double-count:** the analysis_list `<run>_extra_*` debit was given the run total again, repeating everything the first settle had already stored.
3. **Re-queue spend lost:** re-running a batch overwrote `Batch.cost_usd`. The run's earlier spend on that batch disappeared from every total.
4. **Thesis cost missing:** the thesis debit stored no LLM cost (`array()`).

## Root cause
The analyzer only reported the sum of the *current* batch costs, and nothing reported what a run had actually spent in total. The admin copied that sum onto every ledger row of the run. Classification: CODE_ERROR (an accounting model mismatch, not a charging bug: credits were always correct).

## Fix
**ai-startups-analyzer (SAN-1734)**
- **New file `app/core/spend.py`:**
  - `apply_batch_usage()`: before overwriting a batch that already held a successful call's usage, it adds the old usage to `Analysis.superseded_input_tokens` / `superseded_output_tokens` / `superseded_cost_usd`, in the same transaction. `_write_batch_status` now calls it.
  - `cumulative_totals()`: `cumulative_* = current + superseded`. It falls back to the current totals when there's no Analysis row.
- **`CostSummary`:**
  - It gains `cumulative_input_tokens`, `cumulative_output_tokens` and `cumulative_cost_usd`. These only grow.
  - The existing `input_tokens` / `output_tokens` / `cost_usd` are unchanged; the admin cost dashboard still reads them.
  - `generate-thesis` sets cumulative = its own call.
- **Schema:** the new columns are added on boot by `_sync_missing_columns()`.

**sc-saas-admin (SAN-1735)**
- **`aiCreditRunCostDelta($cost, $domain, $runRef)`** replaces `aiCreditEnrichmentCounts()`:
  - It stores `cumulative_*` minus what that run's DEBIT rows already hold (`ref`, `ref_retry`, `ref_extra_*`), floored at 0. The same delta also applies to the Serper/Firecrawl counts.
  - The three AI Analysis call sites merge it with `array_merge` (it must replace `input_tokens` / `cost_usd`; `+` would not).
- **`aiCreditCallCostData($cost)`:** the thesis debit now stores that call's model, provider, tokens and cost, plus its counts.
- **Unchanged:** an older analyzer response without `cumulative_*` or counts produces writes byte-identical to the code before SAN-1722. Credits charged and the wallet maths are untouched.

## Verification
- **Analyzer:** `./venv/bin/python -m unittest discover -s tests` runs 10 tests, all passing. The DB test runs only with `ANALYZER_TEST_DB_URL` pointing at a throwaway MySQL; it was run that way and passed (re-run of batch 1: superseded 1000 tok / $0.10, cumulative $0.45 vs current $0.35).
- **Admin, mock harness:** with an old analyzer response, writes are byte-identical to the pre-P&L code, with and without the count columns.
- **Admin, real MySQL 9.6 with the real `core/db.php` Medoo**, over a full lifecycle:

  | Step | Ledger row | LLM cost | Credits |
  |---|---|---|---|
  | runA settle | `runA` | $0.30 | 300 |
  | runA re-queue (one batch re-run) | `runA_extra_*` | $0.15 | 10 |
  | rescore runB, settle | `runB` | $0.20 | 150 |
  | rescore runB, retry | `runB_retry` | $0.00 | 15 |
  | thesis | `thesis_*` | $0.012 | 20 |

  - The ledger now totals **$0.662**, equal to the true spend. The old code would have recorded $1.05.
  - Credits charged (495 in total) are unchanged.
- **Not done:** a live end-to-end test against the deployed analyzer.

## Not changed
- **Historical rows:** ledger rows written before this fix keep their duplicated values. Later rows of the same run come out as 0 (the delta is floored), so they don't make it worse. Correcting the old rows needs a reviewed one-off data fix on the tenants DB, which hasn't been done.
