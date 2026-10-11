---
id: SAN-633
title: "NG0100 on mentor-intro.component class bindings (dev-mode only)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-633
sentry:
  - SC-SAAS-FRONTEND-AX
repos: [frontend]
commit: "none — dev-mode only, cannot reproduce in production"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-633 — dev-mode-only NG0100, post-render class-binding mutation

## Root cause
`MentorIntroComponent` template class/ngClass bindings tied to form-validity state that changes after
the initial checked render, during an async subscription in `ngOnInit` — same "value mutated after
render" class as SC-SAAS-FRONTEND-5J. Cannot reproduce in a production build (enableProdMode strips the
checkNoChanges assertion).

## Fix
Low priority: same general remediation as SC-SAAS-FRONTEND-5J — avoid synchronous mutation during the
same CD pass. Exact subscription not pinned to one line.

## Related
SC-SAAS-FRONTEND-5J (same failure class).

## Verification
Confirmed the binding pattern via code read; matches the documented NG0100 dev-mode-only pattern.
