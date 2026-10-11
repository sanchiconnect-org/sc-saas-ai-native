---
id: SAN-220
title: "504 Gateway Timeout on forms-management/profile/data — serial per-form DB loop"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-220
sentry: [SC-SAAS-FRONTEND-2W]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-220 — forms-management/profile/data serial loop

## Root cause
Filed under Repo: Frontend (surfaced as a frontend HTTP-failure Sentry event), but the actual endpoint (`GET forms-management/profile/data/:profileType/:profileUUID`) and its 504 originate in `sc-saas-backend`, tenant `api.ecosystem.firstwingsconnect.com`.

`FormsService.getCustomFormProfileData()` (`form-management.service.ts`) looped over every form returned for the profile's user type with a plain `for...of` and three sequential `await`s per iteration (`getProgramByIds`, `getProgramsByIds`, `getProfileFormSubmission`) — zero concurrency. For a profile/tenant with enough forms configured, total latency scales linearly with form count × per-query latency, which is enough to exceed the gateway's timeout under normal (not even elevated) load — matching the ticket's symptom exactly (504 on this endpoint, this tenant, this specific startup profile).

Also found two stray `console.log('submission', ...)` / `console.log('field', ...)` debug statements left in the hot path, and a dead `allFields` map that was written to but never read anywhere in the function.

## Fix
`sc-saas-backend/src/modules/form-management/form-management.service.ts`, `getCustomFormProfileData()`: replaced the sequential `for` loop with `Promise.all(profileForms.map(async (formData) => {...}))`, so all forms' lookups run concurrently instead of one after another. Each iteration is independent (results keyed by the iteration's own `formData`/`submission`, no cross-iteration state), so parallelizing changes no behavior — only removes the artificial serialization. `Promise.all` with `.map` preserves original array order regardless of resolution order, so response ordering is unchanged. Dropped the two debug `console.log`s and the dead `allFields` map.

## Blast radius
Single function, single file. Response shape and per-form filtering logic (`submission?.data` presence check) unchanged — only removed one `await` per DB call from becoming a full round-trip wait before the next form starts.

## Verification
`npx tsc --noEmit -p tsconfig.json` clean. No test suite exists for this module.

## Rollout
Re-scope this ticket's repo label from "Repo: Frontend" to "Repo: Backend" in Linear to match where the actual fix landed (the ticket's own description already flagged this need). Not resolving the Sentry issue outright — recommend watching for recurrence for a few days post-deploy given no load-test was possible in this session.

## Open questions
None.
