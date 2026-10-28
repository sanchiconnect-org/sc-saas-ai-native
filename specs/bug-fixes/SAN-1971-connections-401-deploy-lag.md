---
id: SAN-1971
title: "connections 401 still reaching Sentry (SC-SAAS-FRONTEND-2J) — releases predate SAN-1673"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1971
sentry: [SC-SAAS-FRONTEND-2J]
repos: [frontend]
related: [SAN-1673, SAN-1925, SAN-1011, SAN-1665, SAN-504, SAN-366, SAN-1978]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1971: 2J 401s are deploy lag

## Investigation
* **The fix:** SAN-1673 `bd95b012c` (2026-10-06) drops a thrown `Http failure response for …: 401` in `src/main.ts` `beforeSend` (current line ~288).
  * On `origin/main`: yes.
  * On `ai_native_setup_vishali`: yes.
* **14-day events by release** (Sentry discover, `issue:SC-SAAS-FRONTEND-2J`):

| release | date | events | has `bd95b012c` |
|---|---|---|---|
| bcf88383d | 10-02 | 41 | no |
| 51eb6706 | 08-18 | 39 | no |
| dab63831 | 09-03 | 23 | no |
| 90bde7be0 | 09-14 | 16 | no |
| 33244b02e | 09-19 | 12 | no |
| 9dde12280 | 09-25 | 11 | no |
| 5be83672, 64cf4cb26, 046862a8, c25f902a8, 3865a064, 837b49587, e267a0303 | 08-14 … 10-01 | 32 | no |
| 022eafd6 (latest event, sineedge `meetings/pending-acceptance: 401`) | 07-31 | 4 | no |
| 3fe291506, 218edca78, 5d44db4f | 10-07 … 10-11 | 4 | **yes**, and **none** of these 4 are 401s |

* **The 401 traffic is deploy lag / stale PWA.** Every 401 is on a release built before the filter. The latest event ran a 2026-07-31 bundle on 2026-10-22, which is the SAN-1925 stale-service-worker case.
* **The 4 post-fix events are a different signal.** 2J is a catch-all group for every thrown `Http failure response`. On post-fix releases it only got:
  * `users/team-members: 409` (app.sanchiconnect.com `/account/edit/team`);
  * `programs-management/code/tri1264: 404` (trise). Fixed under SAN-1978 (`program-code-details` error callback).
  * `mentorship/auto-entry: 403` (supernova `/calender`).
* The interceptor already handles every 401 (clears session, toasts, redirects to `/auth/login`). Users are not affected.

## Fix
None needed for the 401s.

## Blast radius / existing-flow impact
None (no change).

## Verification
- `git merge-base --is-ancestor bd95b012c <release>` for all 17 releases in the 14-day window → only 3fe291506 / 218edca78 / 5d44db4f contain it.
- Sentry discover `issue:SC-SAAS-FRONTEND-2J release:[those 3]` → 3 rows: 409 team-members, 404 programs-management/code/tri1264, 403 mentorship/auto-entry (no 401).

## Recommended close
* Close as deploy lag.
* The fix reaches users when production tenants get a build containing `bd95b012c` and the service worker updates (SAN-1925).
* Prod tenants seen here still run `bcf88383d` and older.

## Open (not in scope)
* Unhandled 409 on `users/team-members` (team edit page).
* Unhandled 403 on `mentorship/auto-entry` (calendar).
* Both are separate missing error callbacks if they recur on current releases.
