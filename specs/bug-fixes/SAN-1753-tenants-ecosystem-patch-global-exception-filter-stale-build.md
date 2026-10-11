# SAN-1753 — tenants `PATCH /ecosystem/startups` 500s via GlobalExceptionFilter (already fixed in code)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1753 (Sentry SC-SAAS-TENANTS-2; sibling -1) · **Repo:** sanchiconnect-saas-tenants · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR, already fixed (stale build)

## Evidence
- 1,145 events on SC-SAAS-TENANTS-2, all `GlobalExceptionFilter.catch` on ecosystem POST/PATCH/DELETE (observed in Sentry).
- Events come from a container started 2026-10-04, before the fix landed on 2026-10-05 (inferred from the `app_start_time` tag; there is no release tag, so this is not proven).

## Root cause
Observed in the code and in `git show 1ef4df9`: the async `RequestHeader` decorator ran `validateOrReject(plainToInstance(<data>, headers))` with no class, and class-validator 0.14.2+ rejects that with `unknownValue` as a raw non-HTTP error (500). `validateCustomDecorators: true` also made the global pipe re-validate the returned Promise against `ClientDomainHeaderDto` (400 even on 0.14.0; reproduced in that commit). A production image installing a newer 0.14.x than the lockfile is the likely trigger (unverified).

## Fix
No new code. `1ef4df9` (SAN-1014, 2026-10-05) is already in the repo: `src/core/validator/request-header.validator.ts` is synchronous, checks `x-client-domain` and throws a 400 `Client domain is required`; `validateCustomDecorators` is removed from `src/main.ts`. Both files read on 2026-10-07 to confirm. `src/core/module.spec.md` corrected (it still claimed `validateCustomDecorators: true`).

## Not fixed
Nothing known. Not confirmed: that the running production container has the fix.

## Contract impact
None new. A missing `x-client-domain` is now a clean 400 instead of a 500.

## Verification
Code and diff read only. No tests added; nothing run against a deployed build.

## Commit
`1ef4df9` (earlier). The spec correction is uncommitted in the working tree.

## Sentry
Resolved under the 2026-10-07 policy (fix in code). Reopen if it recurs from a container started after 2026-10-05 15:17 +0530; then look at class-validator version drift or another call site.
