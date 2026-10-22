---
id: SAN-1984
title: "IsWorkEmail constraint throws on a missing/non-string value → 500 instead of 400 (SC-SAAS-BACKEND-5T)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1984
sentry: [SC-SAAS-BACKEND-5T]
repos: [backend]
commit: backend@4703763b (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1984: IsWorkEmail throws

## Investigation
* **Events:** 3 events on 2026-10-16 06:53 UTC, `environment: local`, same dev Docker backend (`468e2fa18dd4`) as SAN-1976. No production events.
* **Stack:** `ValidationPipe` → `IsWorkEmailConstraints.validate` (`src/core/validator/work-email.validator.ts:13`) → `company-email-validator/index.js:8` `email = email.toLowerCase()`.
* **Version mismatch:** the locally installed copy (1.0.7) checks `validator.validate(email)` first and does not throw. The image's copy, a newer `^1.0.7` release, lower-cases first, so `undefined` throws.
* **Where it is used:** `@IsWorkEmail()` is active on `partner/dto/add-startup.dto.ts` and `startup-kit/dto/service-submission.dto.ts`. Neither field is `@IsOptional()`, so an omitted email reaches the constraint.

## Root cause
The custom constraint passes its input straight to a library that assumes a string. A throwing constraint escapes `ValidationPipe` as a 500 instead of a 400. The same code is on `origin/main`.

## Fix
`src/core/validator/work-email.validator.ts`: a non-string or blank value returns `false`, and the library call is wrapped in try/catch that also returns `false`. The message and constraint name (`isWorkDomain`) are unchanged.

## Blast radius / existing-flow impact
* A valid work email still passes, and a free-provider email still fails with "Only work email address allowed!".
* Only the error path changes: a missing or non-string email now gets a 400 validation error (sibling `@IsEmail()` already rejected it) instead of a 500.
* DTO declarations are untouched, so there is no contract change.

## Verification
* New `src/core/validator/work-email.validator.spec.ts`, 10/10 pass. It covers:
  * a company email passes and a gmail address fails;
  * a simulated library `TypeError` becomes a validation failure;
  * `undefined`, `null`, `''`, `'   '`, `42`, `{}` and an array all fail without throwing.
* `npm run gates`: lint 0, test 0, test-floors 0, openapi-floors 0, build 1, unguarded-routes 0. The build failure is pre-existing and unrelated (`deploy-migrate.ts:139`, typeorm 0.3.6 vs 0.3.17 in `node_modules`; see SAN-1976).

## Ops follow-ups
* `npm ci` locally would bring `node_modules` in line with the lockfile (typeorm 0.3.17, current `company-email-validator`).

## Related
SAN-1976 (same dev session).
