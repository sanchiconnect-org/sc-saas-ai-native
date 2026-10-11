---
id: SAN-807
title: "\"Consecutive HTTP\" performance issue on /forms/form/submit/* — no code defect, no action needed"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-807
sentry:
  - SC-SAAS-FRONTEND-D0
repos: [frontend]
commit: "none — not a code defect"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-807 — Sentry performance category, not a JS error

## Root cause
Not a code defect — Sentry performance-monitoring flag (`http_client` category, "Consecutive HTTP")
for sequential, non-parallelized HTTP calls on the form-submit flow. No user-impact signal (0 users).

## Fix
No code change. Consider a Sentry inbound filter for this category on this path if it keeps generating
noise. If genuinely worth optimizing later (e.g. parallelizing the form-submit request chain with
`forkJoin`), that's a separate performance task, not a bug fix.

## Verification
Confirmed via Sentry issue category (`http_client`) that this is a performance flag, not an error.
