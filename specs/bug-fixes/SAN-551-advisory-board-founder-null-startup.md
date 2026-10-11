---
id: SAN-551
title: "StartupAdvisoryBoardService/StartupFounderService crash on null startup lookup"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-551
sentry:
  - SC-SAAS-BACKEND-2A
  - SC-SAAS-BACKEND-29
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-551 — advisory-board/founder list crash on null startup

## Root cause

Both `getAdvisoryBoardsList()` and `getFoundersList()` call `getStartupById(session.startupId)` then
check `if (!startup.id)` — but if the repository call itself returns `null`, accessing `.id` crashes
before the check runs. Sibling method `addAdvisoryBoard()` in the same file already does this
correctly (`if (!startup)`); the list-fetching methods just missed the pattern.

## Fix

Changed both checks to `if (!startup)`:
- `startup-advisory-board.service.ts:155`
- `startup-founder.service.ts:154`

## Blast radius

None — only changes behavior for the previously-crashing null case, which now throws a clean
`NotFoundException` instead.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
