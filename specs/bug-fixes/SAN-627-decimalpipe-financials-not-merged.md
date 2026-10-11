---
id: SAN-627
title: "Error: NG02100 in step-financials-info.component (decimalPipe) — already fixed, not yet merged to main"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-627
sentry:
  - SC-SAAS-FRONTEND-7J
repos: [frontend]
commit: "sc-saas-frontend@8b53d449 (SAN-524) — exists only on ai_native_setup_vishali, not merged to main"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-627 — DecimalPipe crash, fix exists but never merged to main

## Root cause
Unguarded `this.decimalPipe.transform(val, '1.0-0')` in `step-financials-info.component.ts`'s
`numberFormatterArray` valueChanges subscribe.

## Fix
Already fixed by commit `8b53d449` (SAN-524, 2026-08-26, wraps transform in try/catch) — but the
crashing release (`dab63831`) is built from `main`, and `8b53d449` is **not** an ancestor of it. The
fix exists only on `ai_native_setup_vishali`, never merged to `main`.

No new code needed — merge `ai_native_setup_vishali` (or cherry-pick `8b53d449`) into `main` and
deploy.

## Verification
Confirmed via `git merge-base --is-ancestor` that the fix commit is not an ancestor of the crashing
release's build.
