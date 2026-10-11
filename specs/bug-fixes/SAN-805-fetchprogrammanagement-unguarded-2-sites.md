---
id: SAN-805
title: "[Sentry SC-SAAS-FRONTEND-2W] fetchProgramManagement() unguarded 504 on tracker + account-type sign-up — 163 users"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-805
sentry:
  - SC-SAAS-FRONTEND-2W
repos: [frontend]
commit: pending (uncommitted on ai_native_setup_vishali — user verifying locally first)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-805 — unhandled fetchProgramManagement() 504 (2 sites)

## Root cause
`PublicApiService.fetchProgramManagement()` (`sc-saas-frontend/src/app/core/service/public-api.service.ts:115-127`)
re-throws on error with no toast. This Sentry bucket (SC-SAAS-FRONTEND-2W) is shared with SAN-507
(Done, a different endpoint — `getPlatformEvents()`) — today's event is `programs-management`
(default `includeExternal=false`), a distinct call. Two `.subscribe()` calls hitting that default-args
form had no error callback, so a backend 504 became an uncaught exception on the tracker page and on
the account-type step of registration sign-up.

## Fix
Converted both sites to `.subscribe({ next: (res) => {...}, error: () => {} })`, matching the
established SAN-507 pattern and the shape `active-programs.component.ts` already uses for its own
`fetchProgramManagement('true')` call:
- `src/app/modules/tracker/tracker.component.ts:132`
- `src/app/modules/auth/pages/register/sign-up-forms/account-type/account-type.component.ts:157`

## Blast radius
None — purely additive error handling, `next`/success-path behavior unchanged at both sites.

## Verification
`npx tsc --noEmit --skipLibCheck` shows zero errors in either touched file. No automated test
added — same decision as SAN-804, noted as a gap rather than silently skipped.
