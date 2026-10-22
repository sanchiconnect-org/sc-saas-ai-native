---
id: SAN-1987
title: "Duplicate-label warning still grouped per label after SAN-1868: deploy lag (SC-SAAS-BACKEND-3P)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1987
sentry: [SC-SAAS-BACKEND-3P]
repos: [backend]
related: [SAN-1868, SAN-1664, SAN-750]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1987: 3P is deploy lag

## Investigation
* **Latest event:** 2026-10-20 10:21 UTC, production, `level: warning`, `app_start_time` 2026-10-14. It is still grouped by its own message text ("How did you get to know about us?", formId=1, submissionId=4246), not under the SAN-1868 fingerprint.
* **The SAN-1868 fix is not on main:**
  * `fingerprintDuplicateLabelWarning()` (`src/instrument.ts:193`, called from `scrubEvent`) is in `3473722f`.
  * `git merge-base --is-ancestor 3473722f HEAD` → yes. Against `origin/main` → no.
  * `origin/main:src/instrument.ts` has no `fingerprintDuplicateLabelWarning`.
* **No path is uncovered.** The only emit site is `src/modules/user/user.service.ts:1451`. Its text contains both substrings the fingerprint matches: `getProfileDataByEmailOfGuestUser: duplicate label` and `has conflicting values`.

## Root cause
Production runs a build without SAN-1868. The warning itself is intended: SAN-750 keeps it as a form-data-quality signal (tenant form 1 has two fields with the same label).

## Fix
None in code.

## Blast radius / existing-flow impact
None (no change).

## Verification
* The branch checks are quoted above.
* `npm run gates` for the slice: lint 0, test 0, test-floors 0, openapi-floors 0, build 1, unguarded-routes 0. The build failure is pre-existing and unrelated (see SAN-1976).

## Ops follow-ups
* Promote the backend branch to main and deploy (SAN-1926). New events then land in the single `guest-user-profile-duplicate-label-conflict` group. After that, resolve 3P and the other per-label groups.
* Optional: the tenant admin de-duplicates the "How did you get to know about us?" label on form 1.

## Related
SAN-1868, SAN-1664, SAN-750.
