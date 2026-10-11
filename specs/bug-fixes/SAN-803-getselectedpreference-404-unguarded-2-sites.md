---
id: SAN-803
title: "[Sentry SC-SAAS-FRONTEND-H] getSelectedPreference 404 (my_preference/:id/program_office) unguarded on dashboard-v2 + preference-news — 181 users"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-803
sentry:
  - SC-SAAS-FRONTEND-H
repos: [frontend]
commit: pending (uncommitted on ai_native_setup_vishali — user verifying locally first)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-803 — unhandled getSelectedPreference() 404 (2 sites)

## Root cause
`GlobalService.getSelectedPreference()` (`sc-saas-frontend/src/app/core/service/global.service.ts:609-619`)
hits `news/my_preference/:profileId/:accountType` and its `catchError` re-throws with no toast. This
Sentry bucket (SC-SAAS-FRONTEND-H) is shared with SAN-112/SAN-369 (both Done, confirmed different
endpoints) — today's event is a distinct, unaddressed call site. Both callers subscribed with no
error callback, so a 404 (e.g. for the `program_office` account type) became an uncaught exception
on the dashboard widget and the news-preference flow.

## Fix
Converted both sites to `.subscribe({ next: (res) => {...}, error: () => {} })`, matching the
established SAN-366/369/375/504/507/509 pattern:
- `src/app/modules/dashboard-v2/components/dashboard-content/dashboard-content.component.ts:108`
- `src/app/modules/deeptech-news/preference-news/preference-news.component.ts:147`

## Not in scope
Why `program_office` gets a 404 on this preference route at all (likely a backend-contract gap) is
a separate question — out of scope for this frontend-only noise-suppression fix.

## Blast radius
None — purely additive error handling, `next`/success-path behavior unchanged at both sites.

## Verification
`npx tsc --noEmit --skipLibCheck` shows zero errors in either touched file. No automated test
added — same decision as SAN-804/805, noted as a gap.
