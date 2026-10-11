# SAN-1152 — QueryFailedError: Column 'profile_type' cannot be null (SC-SAAS-BACKEND-4F)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1152
- **Repo:** sc-saas-backend · **Type:** Bug · **Priority:** High · **Assignee:** Sandeep
- **Classification:** CODE_ERROR (root cause class known from precedent) — investigation inconclusive

## Problem
Sentry `SC-SAAS-BACKEND-4F` — 1 event, production, unhandled. Same error text as the
already-fixed `SC-SAAS-BACKEND-B` group (SAN-1012/1021, SAN-892/1050 pattern), but a distinct
Sentry group, firing after those fixes landed — suspected third write path.

## Investigation
Checked every backend entity with a `profile_type` column:
- `connections-user-matrix.entity.ts` — `default: UserTypes.STARTUP`
- `profile-views.entity.ts` — `nullable: true`, `default: null`
- `connections-matrix.entity.ts` (`profile_type_1`/`_2`) — `default: UserTypes.STARTUP`
- `community-wall-posts.entity.ts` — `nullable: true`
- `memberships.entity.ts` / `membership-upgrade-requests.entity.ts` — `default: 'startup'`
- `event_booths.entity.ts` — `default: UserTypes.STARTUP` (already fixed under SAN-1021)

Every one is nullable or has a DB-level default — none can currently throw a NOT NULL violation
through TypeORM's normal `.save()`/`.insert()` path. Also checked files using raw
`createQueryBuilder()`/`.query()` that touch `profile_type` (`payment.repository.ts`,
`membership.repository.ts`, `admin-actions.service.ts`, membership cron service) — nothing
conclusive.

## Fix
None. The event's stacktrace has no first-party frame (bottoms out in `mysql2`/`typeorm`
internals only), there's no request/SQL breadcrumb, and only 1 occurrence exists. Guessing at a
write path and patching it without evidence would risk masking the real cause or fixing the wrong
thing.

## Verification
N/A — no code change made.

## Next step
Revisit if `SC-SAAS-BACKEND-4F` recurs, ideally with a symbolicated frame or request context to
identify the actual write path.

## Commit
None — no code changed, nothing to commit.
