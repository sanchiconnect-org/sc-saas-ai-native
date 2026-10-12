---
id: SAN-1872
title: "profile-views/increment INSERT fails with Unknown column 'NaN' (SC-SAAS-BACKEND-3M)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1872
sentry: [SC-SAAS-BACKEND-3M]
repos: [backend]
commit: sc-saas-backend@acfeb44a (branch ai_native_setup_vishali, pushed)
created: 2026-10-12
updated: 2026-10-12
---

# SAN-1872: profile_views INSERT with a NaN user_id

**Classification:** CODE_ERROR. Supersedes SAN-1754, which was closed without a verified root cause or a code change.

## Evidence
* 232 events; the latest is 2026-10-10 (production).
* The build with the SAN-1152 `attachFailedQuery` instrumentation tags the failure as `failed_table=profile_views`, query `INSERT INTO profile_views(... user_id, profile_type, profile_id) VALUES (..., ?, ?, ?)`.

## Root cause
`POST user/profile-views/increment` stores `profileViewDto.userId ?? null`. The DTO field has only `@IsOptional()`, and the global ValidationPipe doesn't transform the body, so whatever the client sends reaches the INSERT.

All 7 frontend public-profile pages send `userId: loggedInUserDetails?.id || ''`. mysql2 inlines a JS NaN number unquoted, which gives "Unknown column 'NaN'". An offline TypeORM 0.3.6 reproduction showed that `''` and `'abc'` bind as quoted strings. So the exact upstream source of the NaN number is not pinned down; the fix below covers every non-integer input regardless.

## Fix
`sc-saas-backend/src/modules/user/repositories/user.repository.ts`, `trackProfileView()`: `userId` and `profileId` go through `toPositiveIntOrNull()`. A positive integer (or numeric string) is kept; anything else is stored as an anonymous view (NULL).

* The DTO and route are unchanged, so there is no API contract change.
* `@IsInt()` was rejected: it would 400 every anonymous view and show visitors an error toast.

## Blast radius
This method only. Logged-in views behave as before. No flag, auth or tenancy change.

## Verification
* `tsc --noEmit`: the touched file compiles clean. The only error is pre-existing and unrelated: `@aws-sdk/client-sesv2` is not installed locally.
* The existing `user.repository*.spec.ts` suites pass (5/5).
* Full Jest suite compared against the original code (stashed): no regression (16 vs 17 failing suites, all pre-existing). Details are in `sentry-sweep-2026-10-12.md`.
* All 3 `profile_views` readers were checked. Today's anonymous rows are `user_id = 0` (MySQL is non-strict); after the fix they are NULL, and every reader treats the two identically. Details are in `sentry-sweep-2026-10-12.md` §3.
* The coercion was checked against 15 input shapes.
* No automated regression test added yet (proposed: `user.repository.spec.ts` asserting `''`/NaN/`'abc'`/0 → null and `5`/`'5'` → 5).

## Follow-up
* Optional frontend cleanup: send `?? null` instead of `|| ''`.
* After deploy, any untagged 3M events that remain come from a different call site and need a new ticket.
