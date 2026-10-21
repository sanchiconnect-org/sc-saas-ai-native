---
id: SAN-1927
title: "generate-thesis times out at the 20s THESIS_LLM_TIMEOUT_S default (AI-STARTUPS-ANALYZER-4)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1927
sentry: [AI-STARTUPS-ANALYZER-4]
repos: [ai-analyzer]
related: [SAN-186, SAN-187]
commit: ai-startups-analyzer (see the Linear handover note)
created: 2026-10-15
updated: 2026-10-21
---

# SAN-1927: thesis generation timeout on a large-form program

## Investigation (from Sentry only)
* **Event:** `HTTPException(504, "Thesis generation timed out — please try again.")` at `api/app/api/v1/routes.py:3354`.
  * `asyncio.wait_for(..., timeout=float(os.getenv("THESIS_LLM_TIMEOUT_S", "20")))` expired.
  * Regressed: 3 events on 2026-10-15, the last at 08:31 UTC (4 all-time; first seen 2026-07-31).
* **Request:** program "Horizon HealthTech 2026" (IIITD).
  * Large `form_fields` list plus conditional branch blocks (`has_branches: True`), so the prompt is big.
  * Enrichment returned nothing (`sources=[]`, empty `website_text`), so the LLM call alone took more than 20 s.
* **Earlier tickets:** SAN-186 (thesis timing out) and SAN-187 (Gemini quota), both Done.

## Root cause
The thesis LLM call ran on `executor`, the shared scoring thread pool (`ANALYZER_GLOBAL_CONCURRENCY`, default 10). Scoring batches from any tenant can hold every thread. The thesis call then queued behind them, and the queue wait counted against `THESIS_LLM_TIMEOUT_S` (20 s). So it returned 504 without the provider being slow. SAN-1920's prose-mode change did not touch this.

Raising the timeout is not an option. The admin's caller is capped at 25 s, under PHP's 30 s, and the worst case is already 8 s of enrichment plus 20 s of LLM.

## Fix
`api/app/api/v1/routes.py`: a dedicated `_thesis_executor` (`ANALYZER_THESIS_CONCURRENCY`, default 4) for the `generate_thesis` call. Scoring, the timeouts, the prompt and the API contract are unchanged. Documented in the analyzer's `CLAUDE.md` and `knowledge.md`.

## Verification
- New `api/tests/test_thesis_executor.py` fills the scoring pool, stubs the provider and enrichment, and sets `THESIS_LLM_TIMEOUT_S=1`.
  - With the fix it passes.
  - Without it, the call waits about 1 s and fails (504).
- `make gates`: ruff 0, test 0 (23 passing, floor 21).

## Open
- The production `DEFAULT_PROVIDER`, `THESIS_LLM_TIMEOUT_S` and thesis model are unchecked; that needs the analyzer host.
- The two other short prose endpoints (`generate-screening-summary`, `generate-prior-art`) still use the scoring pool.
