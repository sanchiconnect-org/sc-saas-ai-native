---
id: SAN-751
title: "editStartupInformation crashes for team members — re-fetch keyed on owner userId instead of startupId"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-751
sentry:
  - SC-SAAS-BACKEND-2R
repos: [backend]
commit: sc-saas-backend@a433055e (branch ai_native_setup_aman only — see Rollout)
created: 2026-09-10
updated: 2026-09-10
---

# SAN-751 — editStartupInformation team-member crash

## Root cause

`startup.service.ts`'s `editStartupInformation()` re-fetches the just-updated startup via
`getSatrtupFromUserId(session.userId)` — keyed on the startup's **owner** `userId` column. The actual
update two lines above is keyed on `session.startupId` (already validated earlier in the same
function). For a **team member** (not the primary owner) editing the startup, `session.userId`
doesn't match the owner column, so the re-fetch returns `null` even though the update itself
succeeded — and the subsequent `updatedStartupInfo.isApproved` read crashes.

## Fix

Swapped the re-fetch to `getStartupById(session.startupId)` — same entity shape (both plain
`findOne` on `StartupEntity`), keyed on an identifier already known valid for any team member.

## Blast radius

None for the primary-owner case (unchanged result); fixes the team-member case entirely.

## Verification

`tsc --noEmit` clean. No existing test suite for `startup.service.ts`.

## Rollout

Committed `sc-saas-backend@a433055e`. **Deliberately reverted from `ai_native_setup`** on 2026-09-10
at explicit user request (history rewritten via `git reset --hard` + force-push to `00d4ff30`, so
`a433055e` no longer exists on that branch at all) — kept live **only on `ai_native_setup_aman`**
(merge commit `70740f24`). SC-SAAS-BACKEND-2R was re-marked unresolved in Sentry to reflect this.

## Open questions

This fix is intentionally NOT on the shared `ai_native_setup` branch. Anyone deploying from
`ai_native_setup` will not have this fix until it's explicitly re-applied there.
