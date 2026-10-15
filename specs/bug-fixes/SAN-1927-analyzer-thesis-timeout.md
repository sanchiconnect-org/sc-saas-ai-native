---
id: SAN-1927
title: "generate-thesis times out at the 20s THESIS_LLM_TIMEOUT_S default (AI-STARTUPS-ANALYZER-4)"
type: bug-fix
status: todo
linear: https://linear.app/sanchiconnect/issue/SAN-1927
sentry: [AI-STARTUPS-ANALYZER-4]
repos: [ai-analyzer]
related: [SAN-186, SAN-187]
commit: none — not started (ai-startups-analyzer is not cloned in this workspace)
created: 2026-10-15
updated: 2026-10-15
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

## Fix
Not started. The code has to be checked out first. Options:
* Check the prod `THESIS_LLM_TIMEOUT_S` and `DEFAULT_PROVIDER`.
* Raise the timeout, keeping it within sc-saas-admin's caller timeout.
* Or trim the prompt for large forms (summarise or cap the field hints) or stream the response.

## Verification
Pending.
