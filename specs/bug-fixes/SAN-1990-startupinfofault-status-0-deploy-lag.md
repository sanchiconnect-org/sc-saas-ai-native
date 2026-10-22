---
id: SAN-1990
title: "startupinfoFault 0 Unknown Error on firstwings startup profile (SC-SAAS-FRONTEND-3M) — releases predate SAN-569"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1990
sentry: [SC-SAAS-FRONTEND-3M]
repos: [frontend]
related: [SAN-569, SAN-604, SAN-674, SAN-1978]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1990: 3M is deploy lag

## Investigation
* **Latest event:** `startupinfoFault( Http failure response for …/startups/startup-information: 0 Unknown Error )`, release `bcf88383d` (2026-10-02), firstwings, Safari/Mac, 2026-10-19 08:40:41, `level: warning`, `logger: console`.
* **Network drop, not this endpoint:** the same trace `f0750bae…` failed `programs-management/` and `community-wall/posts/me/stats` in the same second (SAN-1978 / FRONTEND-1).
* **The fix in current code:** `StartUpService.getStartUpInfo()` (`core/service/startup.service.ts:109-119`). Since SAN-569 (`cac790292`, 2026-10-05), it only warns when `fault.status && fault.status < 500`. A status-0 failure is toasted ("Error getting startup info!") and not logged.
* **Ancestry:** `cac790292` is on `origin/main` and `ai_native_setup_vishali`. It is in none of the 30-day releases that fired: `7ee8544e6`, `9dde12280`, `bcf88383d`, `8446f479e`, `33244b02e`, `488fd59a5`, `51eb6706` (all `merge-base --is-ancestor` → no).
* **Code at the release:** `git show bcf88383d:src/app/core/service/startup.service.ts` line 109 still has the unconditional `console.warn(startupinfoFault…)`.

## Fix
None needed.

## Blast radius / existing-flow impact
None (no change).

## Verification
* `git merge-base --is-ancestor cac790292 <release>` → `no` for each of the 7 releases above.
* `cac790292` on `origin/main` → `yes`.

## Recommended close
Close as deploy lag. Firstwings needs a build containing `cac790292`.
