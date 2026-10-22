---
id: SAN-1975
title: "Unknown column 'NaN' on profile_views still firing after SAN-1872: deploy lag (SC-SAAS-BACKEND-3M)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1975
sentry: [SC-SAAS-BACKEND-3M]
repos: [backend]
related: [SAN-1872, SAN-1926, SAN-1754, SAN-405]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1975: 3M is deploy lag

## Investigation
* **Latest event:** 2026-10-21 16:39 UTC, production, `failed_table=profile_views`, `INSERT INTO profile_views(... user_id, profile_type, profile_id) VALUES (DEFAULT, ?, ..., ?, ?, ?)`, `app_start_time` 2026-10-14.
* **Tags over 14 days:** all 45 tagged events are `profile_views`. The 29 untagged ones stop at 2026-10-10, before the build that carries the SAN-1152 `attachFailedQuery` tagging. No other table appears.
* **Only one write path:** `UserRepository.trackProfileView()` (`src/modules/user/repositories/user.repository.ts` ~1289) is the only `profile_views` write. `notifications` and `app.utils` only read.
* **The fix is not deployed:**
  * The SAN-1872 fix `acfeb44a` (`toPositiveIntOrNull()` on `userId`/`profileId`) is on `ai_native_setup_vishali`.
  * `git merge-base --is-ancestor acfeb44a origin/main` → not an ancestor. Same for `origin/development` and `origin/stagingdemo`.
  * `origin/main` still has `userId: profileViewDto.userId ?? null`.
  * The newest `origin/main` commit is 2026-10-11, and the production process started 2026-10-14, so production runs code without the fix.

## Root cause
There is no second write path. Production lacks the SAN-1872 fix, which is not yet on any branch that deploys to production (SAN-1926).

## Fix
None in code.

## Blast radius / existing-flow impact
None (no change).

## Verification
* The branch checks are quoted above.
* `npm run gates` for the slice: lint 0, test 0, test-floors 0, openapi-floors 0, build 1, unguarded-routes 0. The build failure is pre-existing and unrelated: `deploy-migrate.ts:139` (see SAN-1976).

## Ops follow-ups
* Promote `ai_native_setup_vishali` → `ai_native_setup` → `development` → `stagingdemo` → `main` and redeploy production (SAN-1926).
* After the deploy, resolve 3M. Reopen if an event arrives with an `app_start_time` after the deploy: that would mean a second path.

## Related
SAN-1872, SAN-1926, SAN-1754, SAN-405.
