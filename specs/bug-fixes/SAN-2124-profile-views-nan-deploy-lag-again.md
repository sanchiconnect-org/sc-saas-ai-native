---
id: SAN-2124
title: "Unknown column 'NaN' still firing — SAN-1872 on main since 10-27, prod backend started 10-14"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2124
sentry: [SC-SAAS-BACKEND-3M]
repos: [backend]
related: [SAN-1754, SAN-1872, SAN-1926, SAN-1975, SAN-2025]
commit: none — deploy lag
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2124: 3M is deploy lag (fix now on main)

## Investigation
* SAN-1872 (`acfeb44a`) is now on origin/main via `cc8fb88d` (10-27), as well as development, stagingdemo and ai_native_setup. It has moved forward since SAN-2025.
* The latest 3M event (2026-10-27 09:01Z) is production, with `app_start_time` 2026-10-14 and `failed_table=profile_views` on the same INSERT that SAN-1872 fixed.
* Other NaN paths: the only `profile_views` write (`user.repository.ts:1317-1323`) already uses `toPositiveIntOrNull`, and the only `.increment()` (`verification.repository.ts:116`) takes no request input.

## Open (ops)
Redeploy the prod backend from main and watch 3M go quiet.
