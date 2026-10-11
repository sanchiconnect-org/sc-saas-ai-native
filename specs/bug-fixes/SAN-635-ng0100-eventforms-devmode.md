---
id: SAN-635
title: "NG0100 on EventFormsComponent requiredFields ngIf (dev-mode only)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-635
sentry:
  - SC-SAAS-FRONTEND-1G
repos: [frontend]
commit: "none — dev-mode only, cannot reproduce in production"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-635 — dev-mode-only NG0100, requiredFields population race

## Root cause
`EventFormsComponent`'s template (`div_1_div_7_Template`) binds
`*ngIf="requiredFields.length > 0"`; `requiredFields` populates asynchronously after initial render,
flipping the ngIf post-check. Cannot reproduce in a production build (enableProdMode strips the
checkNoChanges assertion that raises NG0100).

## Fix
Low priority: initialize `requiredFields` synchronously before first render, or move population
earlier in the lifecycle.

## Verification
Confirmed the binding and async-population timing via code read; matches the documented NG0100
dev-mode-only pattern (see M1 milestone notes).
