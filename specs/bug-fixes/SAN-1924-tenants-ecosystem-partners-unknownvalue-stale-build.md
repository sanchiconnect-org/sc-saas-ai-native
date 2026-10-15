---
id: SAN-1924
title: "PATCH /api/v1/ecosystem/partners fails validation \"unknownValue\" into GlobalExceptionFilter (SC-SAAS-TENANTS-2)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1924
sentry: [SC-SAAS-TENANTS-2]
repos: [tenants]
related: [SAN-1753, SAN-1014, SAN-143]
commit: none — no code defect, already fixed by SAN-1014 (1ef4df9); see Investigation
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1924: ecosystem/partners "unknownValue" is the same pre-SAN-1014 stale build as SAN-1753

## Investigation
* **Sentry:** `An instance of Object has failed the validation: - property undefined has failed the following constraints: unknownValue`.
  * Culprit `PATCH /api/v1/ecosystem/partners`, caller axios 0.27.2 (sc-saas-backend's ecosystem push).
  * 1,152 events all-time, 33 in the last 14 days. Last seen 2026-10-08 14:30 UTC, from a container with `app_start_time` 2026-10-04.
* **Source:** the old async `RequestHeader` param decorator (`src/core/validator/request-header.validator.ts`). It ran `validateOrReject(plainToInstance(value, headers))` on raw headers that had no class.
  * The rejection is a `ValidationError[]`, not an HttpException, so it fell through to `GlobalExceptionFilter` as a 500.
  * `validateCustomDecorators: true` in `main.ts` added a second validation.
* **The body is not the cause.** `ProfileData` (`src/modules/ecosystem/dtos/add-profiles.dto.ts:22`) is a decorated class. A bad body (empty, array, missing `userData`) gets a clean 400 from `ValidationPipe`, never this message.
* **Already fixed** by `1ef4df9` (SAN-1014, 2026-10-05):
  * the decorator is now synchronous and throws `BadRequestException('Client domain is required')`;
  * `validateCustomDecorators` was dropped.
* **`/partners` is covered.** `ecosystem-partner.controller.ts` uses the same shared decorator on every route, so `/partners` was fixed at the same moment as `/startups`.
* SAN-1753 had no code commit; its doc already classifies the `/startups` case as a stale build.
* The fix reached `origin/master` via merge `d535d4f` (PR #197) at 2026-10-08 22:06 IST, after the container that raised the last event had started. No events since.

## Fix
None in tenants.

## Blast radius
None, no code changed.

## Verification
* A temporary controller test against the real `EcosystemPartnersController` (mocked service, `ValidationPipe({whitelist:true})` as in main.ts), deleted afterwards:
  * valid push → 200;
  * no `userData`, `{}` body, array body → 400;
  * missing header → 400 "Client domain is required".
* The existing `request-header.validator.spec.ts` passes (6 cases).
* `npm run gates` (tenants): exit 1.
  * lint 0, build 0.
  * test: 3/93 failed. All 3 are generated-contract freshness checks failing on local CRLF line endings (`core.autocrlf=true`), unrelated to this ticket.
  * test-floors fails as a knock-on of those same 3 tests.

## Open
* **Optional backend hygiene:** `sc-saas-backend` `ecosystem.service.ts` `updatePartner()` (~1437-1465) should skip the push when `partner?.user?.[0]` is missing, as the SAN-143 guard already does in `updateStartup()`.
* Pin class-validator / use `npm ci` in the tenants build so prod can't drift from the 0.14.0 lockfile.
* Reopen only if an event comes from a container started after 2026-10-08.
