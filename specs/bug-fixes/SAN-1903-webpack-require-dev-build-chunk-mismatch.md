---
id: SAN-1903
title: "__webpack_require__ 'call' of undefined on thub dev build"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1903
sentry: [SC-SAAS-FRONTEND-HD]
repos: [frontend]
commit: none — no code defect, see Investigation
created: 2026-10-14
updated: 2026-10-14
---

## Investigation
One event, `environment: local`, on thub.sanchidev.in. Unhashed file names (`runtime.js`, `src_app_modules_account_account_module_ts.js`) mean a development build (SAN-158). Module 65588 (`consent.service`) was missing from the loaded runtime while lazy-loading the account module. That is a runtime/chunk version mismatch after a redeploy, which can't happen with hashed production file names.

## Fix
None. Resolved by SAN-158.
