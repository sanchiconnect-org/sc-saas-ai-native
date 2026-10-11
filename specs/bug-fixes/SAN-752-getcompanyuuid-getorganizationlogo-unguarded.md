---
id: SAN-752
title: "getCompanyUUID/getOrganizationLogo fully unguarded — same family as already-fixed getOrganizationName"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-752
sentry:
  - SC-SAAS-BACKEND-2S
  - SC-SAAS-BACKEND-2T
repos: [backend]
commit: sc-saas-backend@a433055e (branch ai_native_setup_aman only — see Rollout)
created: 2026-09-10
updated: 2026-09-10
---

# SAN-752 — getCompanyUUID/getOrganizationLogo null guards

## Root cause

Both `getCompanyUUID()` and `getOrganizationLogo()` (`app.utils.ts`) switch on `user.accountType` and
read straight off the relation (`user.program_office.uuid`, `user.startup.uuid`, etc.) for all 8
account types, with zero optional chaining — unlike their sibling `getOrganizationName()`, already
guarded. Both reached via `ConnectionsService` (`getConnectionsListBasic` / `getConnectionsRequestByType`).
Same family as SAN-554's `getOrganizationNameWithMentorNull` — a recurring pattern in this file of
some switch-on-accountType helpers guarded and some not.

## Fix

Added `?.` to every branch of both functions.

## Blast radius

None.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `sc-saas-backend@a433055e`. **Reverted from `ai_native_setup`** on 2026-09-10 at explicit
user request (see SAN-751's doc for the mechanics — same commit, same revert) — kept live **only on
`ai_native_setup_aman`** (merge commit `70740f24`).

## Open questions

Worth a dedicated pass over the rest of `app.utils.ts` for the same guarded/unguarded inconsistency
rather than waiting for each one to surface individually in Sentry.
