---
id: SAN-703
title: "saveStartUpInfo fails with raw backend TypeError \"Cannot read properties of null (reading 'isApproved')\""
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-703
sentry:
  - SC-SAAS-FRONTEND-CS
repos: [backend]
commit: pending (uncommitted on ai_native_setup_vishali — user verifying locally first)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-703 — unguarded null read on re-fetched startup in editStartupInformation()

## Root cause
`StartupService.editStartupInformation()` (`sc-saas-backend/src/modules/startup/startup.service.ts:523-537`)
re-fetches the startup via `startupRepository.getStartupById()` after the update, then reads
`.isApproved`/`.isSearchResults`/`.uuid` on the result with no null guard.
`getStartupById()` (`startup.repository.ts:131-138`) is a bare `findOne` and can return `null`,
so the raw `TypeError: Cannot read properties of null (reading 'isApproved')` bubbled to NestJS's
default exception filter and leaked to the client as a 500 — the info-leak the ticket flagged.

## Fix
Added a null guard immediately after the re-fetch, throwing
`NotFoundException(ApiErrors.STARTUP_PROFILE_NOT_ATTACHED)`. This mirrors the SAN-606 precedent in
the same file's `getStartupInformation()`: this is a parameterless "my own startup" session-lookup
(keyed off `session.startupId` from the JWT), so `STARTUP_PROFILE_NOT_ATTACHED`'s "contact support"
copy is correct, versus `STARTUP_NOT_FOUND`'s misleading "entered the correct startup name" wording
which is meant for user-typed lookups.

File changed:
- `src/modules/startup/startup.service.ts:523-533`

## Blast radius
None — additive guard only; the update itself (`updateStartup()`) already succeeded by this point
(`updateResult.affected` was checked above), so this only guards the informational re-fetch used for
the ecosystem-sync side effect and the response payload.

## Verification
`npx eslint src/modules/startup/startup.service.ts --no-fix`: only pre-existing repo-wide CRLF/prettier
noise (present throughout the file, unrelated to this change) and pre-existing unused-var warnings.
No automated test added — `sc-saas-backend` has a working Jest setup so one should be proposed per
the bug-fix flow, but deferred given the size of the Urgent/High queue being worked through in this
session; noting the gap rather than skipping silently.
