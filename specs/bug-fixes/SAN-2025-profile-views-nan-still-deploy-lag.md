---
id: SAN-2025
title: "Unknown column 'NaN' on profile_views: SAN-1872 now on development, still not on main"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2025
sentry: [SC-SAAS-BACKEND-3M]
repos: [backend]
related: [SAN-1754, SAN-1872, SAN-1926, SAN-1975]
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2025: 3M is still deploy lag

## Investigation
* 57 production events in 14 days. The newest, on 2026-10-23, were 14 events within 2 s on `-180` and one at 11:21 on `-211` (`app_start_time` 2026-10-14).
* Every event has `failed_table=profile_views` and the same INSERT as before. `UserRepository.trackProfileView()` is still the only writer, and `profile_type` is an enum string, so it can't produce an unquoted NaN.
* `acfeb44a` (SAN-1872) is an ancestor of `origin/development`, `ai_native_setup` and `ai_native_setup_vishali`. It is **not** an ancestor of `origin/stagingdemo` or `origin/main` (`6e7ca5c8`, 2026-10-11). It has moved one stage since SAN-1975.
* `origin/main:src/modules/user/repositories/user.repository.ts:1278` still has `userId: profileViewDto.userId ?? null`.

## Root cause
Production runs code without the fix.

## Fix
None in code.

## Blast radius / existing-flow impact
None.

## Verification
The branch checks above.

## Ops follow-ups
Promote development → stagingdemo → main and redeploy (the SAN-1926 track). Reopen only if a 3M event arrives with an `app_start_time` after that deploy.
