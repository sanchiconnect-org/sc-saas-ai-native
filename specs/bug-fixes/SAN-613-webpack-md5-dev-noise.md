---
id: SAN-613
title: "[webpack-dev-server] WARNING re: 'md5' CommonJS dependency (dev-only noise)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-613
sentry:
  - SC-SAAS-FRONTEND-CE
repos: [frontend]
commit: "none — build-time warning, not a runtime bug"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-613 — webpack build-time CommonJS warning

## Root cause
Webpack build-time warning about the `md5` package being a CommonJS dependency, captured because
Sentry is initialized even in local dev mode. Not an application defect — no user-facing impact.

## Fix
Low priority: either add `md5` to `allowedCommonJsDependencies` in `angular.json` to silence the build
warning, or scope Sentry's browser SDK init to skip `environment: local` so dev-only console noise
stops being reported as issues. Recommend closing as won't-fix/infra if not worth the config change.

## Verification
Confirmed this is a webpack build-time warning, not a runtime exception.
