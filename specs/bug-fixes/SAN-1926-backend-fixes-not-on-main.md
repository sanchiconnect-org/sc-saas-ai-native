---
id: SAN-1926
title: "Backend fixes SAN-1872/1895/1874/1873 are not on main — prod (deployed 2026-10-11) still throws them (SC-SAAS-BACKEND-3M, 5Q, 9, X)"
type: bug-fix
status: in-progress
linear: https://linear.app/sanchiconnect/issue/SAN-1926
sentry: [SC-SAAS-BACKEND-3M, SC-SAAS-BACKEND-5Q, SC-SAAS-BACKEND-9, SC-SAAS-BACKEND-X]
repos: [backend]
related: [SAN-1872, SAN-1895, SAN-1874, SAN-1873, SAN-1754]
commit: none — deploy/release action, no code change
created: 2026-10-15
updated: 2026-10-16
---

# SAN-1926: backend deploy lag

## Investigation
Prod backend containers started 2026-10-11 (Sentry `app_start_time`). That matches `origin/main` HEAD `6e7ca5c8` (merge of PR #2027 from stagingdemo, 2026-10-11 20:47 IST).

These fixes are on `ai_native_setup_vishali` but are **not** ancestors of `origin/main`:

| Sentry | Events (14d) | Fix | Commit |
|---|---|---|---|
| 3M `Unknown column 'NaN'` on `profile_views` INSERT | 96 | SAN-1872 | `acfeb44a` (2026-10-12) |
| 5Q `meeting.user.id` of null in `MeetingsRepository.getMeetings` | 2 | SAN-1895 | `60a20f65` (PR #2038, 2026-10-13) |
| 9 S3 `SignatureDoesNotMatch` (diagnostic tagging) | 11 | SAN-1874 | `1ad29b33` (2026-10-12) |
| X AxiosError 500 unhandled (ConvertAPI) | 4 | SAN-1873 | `aaad005e` (2026-10-13) |

The 5Q stack frame (`if (userIds.includes(meeting.user.id))`, `meetings.repository.js:363`) is the pre-fix code, which confirms the deployed build lacks the fix.

For 3M, the earlier fix SAN-1754 (`6b3f8945`) is on main but covers a different write site.

## Branch state (re-checked 2026-10-16, after `git fetch`)
* All four commits are on `origin/ai_native_setup` (and `ai_native_setup_vishali`).
* None of them is on `origin/development`, `origin/stagingdemo` or `origin/main`.
* `development`, `stagingdemo` and `main` point at the same commit (`906f7fb6`). Nothing is waiting between them.
* `development..ai_native_setup` holds **58 non-merge commits**. A whole-branch promotion would ship all of them.
  * Besides the four fixes, that includes unreviewed feature work:
    * socket gateway auth (SAN-1490);
    * the consent ledger and backfill (`38fac74a`);
    * push/WhatsApp notifications (`5b9d60ae`);
    * tentative rounds (`7ccf6c6f`);
    * forms `public_share_token` column (SAN-35);
    * the CFA closed-program apply refusal (SAN-1886);
    * the CI/contract-gate stack (P-SAN-75).
  * Several of these carry schema or behaviour changes that need their own QA on `development`.

## Fix — two options (no new code either way)
**A. Hotfix backport (recommended for prod).**
* Cherry-pick only the four fix commits onto `development`, then promote `development` → `stagingdemo` → `main` and redeploy.
* Order: `acfeb44a`, `1ad29b33`, `aaad005e`, `60a20f65`.
* Use `cherry-pick -x` so the provenance is recorded.
* Prod then gets exactly these fixes and nothing else.
* When `ai_native_setup` is promoted later, git sees the same patches and the merge stays clean.

**B. Full promotion** (the original plan).
* Promote `ai_native_setup` → `development` → `stagingdemo` → `main`.
* This ships the four fixes **plus** the other 54 commits.
* Use it only if that whole batch has already been QA'd for release.

Note: `ai_native_setup_vishali` has 2 more commits (SAN-1931 `4843fd2c`, SAN-1923 `688f5870`) that are not on `ai_native_setup` yet. They are out of scope here; they go with their own issues.

## Backport dry run (option A)
* Ran in a throwaway detached worktree on `origin/development`, then deleted it. No branch was changed, committed or pushed.
* All 4 commits cherry-pick **cleanly** (no conflicts).
* Touched files:
  * `instrument.ts`;
  * `user.repository.ts`;
  * `meetings.repository.ts` and a new `meetings.repository.spec.ts`;
  * `form-management.service.ts`, `resources.service.ts`, `pitch-deck.service.ts`;
  * `meetings/module.spec.md`.
* The diffs don't depend on any of the other 54 commits:
  * no new imports, entities, migrations, DTOs or flags;
  * only null guards, `.catch()` loggers, a userId sanitiser and Sentry tags.
* `npx tsc --noEmit -p tsconfig.json`: exit 0.
* `npx jest` over meetings, user, form-management, resources, pitch-deck: **6 suites / 25 tests pass**, including the SAN-1895 regression spec.
* `eslint` on the touched files: 0 new findings.
  * The only error is `form-management.service.ts:630` `prefer-const`, which is already on `development`. It is cleared by `c5a17d5d`, which is on `ai_native_setup` only.
  * CRLF `prettier` noise comes from the Windows checkout and is not a code problem.
* `npm run gates` doesn't exist on `development` yet (`scripts/gates.sh` arrives with SAN-1590 in the 58). The checks above are the equivalent available there.

## Contract checks
* **API contract:** no controller or DTO change.
  * 5Q: a meeting whose creator was soft-deleted is dropped from the list instead of 500ing, and the single-meeting fetch returns 404.
  * The response shape is unchanged.
* **Flags:** no flag touched.
* **Tenant scoping:** no new queries. The 5Q filter runs in memory on an already-scoped result.
* Automated test coverage: the existing SAN-1895 spec travels with the backport. No new tests were added for this issue, because it is a release action.

## Verification
After the deploy, the four groups should stop. For BACKEND-9, the SAN-1874 tags (region/host/status) will then show the real misconfiguration; follow up on that separately.
