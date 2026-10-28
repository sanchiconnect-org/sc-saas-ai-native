---
id: SAN-2115
title: "LMS reports page: 'Subquery returns more than 1 row' (1242)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2115
sentry: [SC-SAAS-ADMIN-18]
repos: [admin]
related: []
commit: none from this ticket; fixed by admin@35a61d87 (Nirmal Singh)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2115: already fixed upstream

## Investigation
* 18: 1 event, 2026-10-26 09:26 UTC, `/learning_management/reports`.
* Cause: an unused per-course `completed_users` subquery in `modules/learning_management/reports.php`. It grouped by learner, so it returned one row per learner and failed as soon as two learners completed the same course.
* Nirmal removed it in `35a61d87` (2026-10-27 02:45 UTC), after the event. The commit is on `origin/development` and all `ai_native_setup*` branches, but not on main.
* The remaining select-list subqueries are plain `COUNT(*)` with no GROUP BY, which always return one row.

## Fix
None needed.
