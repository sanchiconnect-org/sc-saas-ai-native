---
id: SAN-1981
title: "PATCH /api/v1/ecosystem/startups fails with Duplicate entry on ecosystem_startups.user_id one-to-one key (SC-SAAS-TENANTS-7)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1981
sentry: [SC-SAAS-TENANTS-7]
repos: [tenants]
related: [SAN-143, SAN-410, SAN-460, SAN-1924, SAN-1753]
commit: tenants@52ce2c4 (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1981: a startup owner already linked to another ecosystem startup row breaks the PATCH push

## Root cause
* **Sentry:** `QueryFailedError: Duplicate entry '237' for key 'ecosystem_startups.REL_74505afb55a0a7b3daa526f5a8'`.
  * Culprit `PATCH /api/v1/ecosystem/startups`, caller axios 0.27.2 (sc-saas-backend's ecosystem push), production.
  * 5 events, all between 2026-10-18 23:45:01 and 23:45:42 UTC, from one container (`app_start_time` 2026-10-11). Unhandled, so a 500 to the caller.
* **The index:** `REL_74505afb55a0a7b3daa526f5a8` is `UNIQUE INDEX (user_id)` on `ecosystem_startups` (`src/core/database/migrations/1792394003573-Baseline.ts:65`), from the `@OneToOne` + `@JoinColumn({ name: 'user_id' })` in `src/modules/ecosystem/entities/startups.entity.ts`. `237` is an `ecosystem_users.id`.
* **The flow** (`src/modules/ecosystem/ecosystem.service.ts`, `updateStartup()`, ~467-490; `addStartups()` ~46-64 is the same):
  1. `addOrUpdateStartup()` finds the startup row by `(domain, uuid)` and saves it (insert if new).
  2. `addOrUpdateUser()` finds the owner by `(domain, user uuid)` and sets `ecosystem_users.startup_id` to this startup.
  3. `updateStartupEntity(startup.id, { userId: user.id })` sets `ecosystem_startups.user_id`.
* **Step 3 fails** when another `ecosystem_startups` row of the same domain still holds `user_id = 237`. Nothing in the flow releases the owner from that older row, so the one-to-one is violated. Steps 1 and 2 have already been written by then, so the DB is left half-updated: the owner's `startup_id` points at the new startup, the new startup's `user_id` is NULL, the old startup still points at the owner.
* **How a second row gets the same owner:** the backend's `getStartupByUUIDForEcosystem()` pushes the startup's primary owner (`user.parentId IS null`). The tenants rows are keyed by startup uuid, so the owner is already linked elsewhere when the backend owner now belongs to a different startup uuid than before. Likely causes: the old startup was deleted in the backend and its `DELETE /ecosystem/startups/:uuid` was lost (the backend swallows errors there), or the owner was moved to / re-registered another startup. [UNVERIFIED — no production DB access from here; the diagnostic query below confirms which.]
* **Why 5 events in 41 s:** the backend pushes after each profile-section save (`editProduct`, `editFinancials`, `editIndustryAndTechnology` … in `sc-saas-backend/src/modules/startup/startup.service.ts`). One user saving several sections → one failing PATCH each. Deterministic, not a race.
* **Not a stale build:** the tenants ecosystem repositories/service have not changed since the individuals work (`f87d1cb`); the code on `origin/master` behaves the same.

## Fix (tenants only, uncommitted)
* `src/modules/ecosystem/repositories/startups.repository.ts`: new `detachUserFromOtherStartups(domain, userId, keepStartupId)` — `UPDATE ecosystem_startups SET user_id = NULL WHERE domain = :domain AND user_id = :userId AND id != :keepStartupId`. Scoped to the caller's `domain` (invariant #5).
* `src/modules/ecosystem/ecosystem.service.ts`: `updateStartup()` and `addStartups()` call it right before `updateStartupEntity()`. The latest push wins, which matches what `addOrUpdateUser()` already does with `ecosystem_users.startup_id`.
* Same file, `searchStartups()`: `startup.user.name` → `startup.user?.name`. A startup row with no owner (the detached one, or one left half-written by this bug today) would otherwise throw a TypeError and 500 every other tenant's startup search.
* The stale row is **kept**, not deleted. Whether to delete it is a product call (below).

## Blast radius / existing-flow impact
* **No API contract change.** No controller or DTO touched; request and response shapes are identical. `/audit-contract` not required.
* **Happy path unchanged:** when no other row holds the owner, the new UPDATE matches 0 rows and the flow is exactly as before.
* **Only startups.** The other seven profile types (investors, mentors, corporates, partners, individuals, service providers, program-office members) have the same pattern and the same latent bug; left alone deliberately (no events for them).
* **Search:** a detached stale startup still appears in other tenants' search results, now with `user.name` undefined instead of crashing. Before this bug it appeared with the owner's name.
* `sanchiconnect-saas-tenants-admin` reads the tenants DB directly; a NULL `user_id` was already possible there (the column is nullable), so no new state.
* No schema change, no migration.

## Verification
* New `src/modules/ecosystem/ecosystem.service.startup-relink.spec.ts` (3 tests): detach runs before the link with `(domain, userId, startupId)` in both `updateStartup()` and `addStartups()`, and the repository query sets `user_id = NULL` filtered by domain, user id and `id !=` the kept row. `npx jest src/modules/ecosystem` → 3 passed.
* `npm run gates` (tenants): lint 0, test 1, test-floors 0, build 0, unguarded-routes 0.
  * test: 3 failed, 134 passed, 137 total. The 3 failures are the generated-contract freshness checks (`ai-credits.contract.spec.ts` ×2, `tenant-verification.contract.spec.ts` ×1) failing on local CRLF line endings (`core.autocrlf=true`), the same pre-existing local-only failure noted in SAN-1924. Unrelated to this change.
* Not verified against a real MySQL (no local DB); the query is exercised through a mocked query builder only.

## Open
* **[DESIGN DECISION PENDING]** (product owner): what to do with the stale startup row whose owner moved — keep it searchable without an owner (this fix), hide rows with no owner from search, or delete it. Today the fix keeps it, the least destructive option.
* **Ops check** (production tenants DB, read-only): `SELECT id, uuid, domain, user_id FROM ecosystem_startups WHERE user_id = 237 OR id = (SELECT startup_id FROM ecosystem_users WHERE id = 237);` confirms the two rows, and `SELECT COUNT(*) FROM ecosystem_startups WHERE user_id IS NULL;` shows how many half-written rows exist now.
* Optional backend follow-up: check why that startup's `DELETE /ecosystem/startups/:uuid` did not reach tenants (errors are swallowed in `sc-saas-backend` `ecosystem.service.ts` `deleteStartup()`).
* Same latent bug in the other seven profile types; separate ticket if wanted.

## Related
SAN-143 (startup push without a user), SAN-410 / SAN-460 (ecosystem push on approve), SAN-1753 / SAN-1924 (ecosystem PATCH stale build).
