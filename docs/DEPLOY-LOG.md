# Production deploy log (SAN-1626)

One row per production deploy, added the same day by the person who pressed "Build now". Production means any job that builds `main`/`master`, `stagingdemo` (the demo on the production servers) or the frontend's `sanchiconnect` branch; see `docs/DEPLOYMENT.md` for the jobs. Until a deploy workflow exists (Phase 3), this file is the record. The Friday review counts deploys per week from it.

## How to log a deploy

1. **Tag** what you are deploying, on the production branch after the merge: `scripts/tag-release.sh <repo> [<repo> ...]`. This creates `release-YYYY-MM-DD` (then `-2`, `-3` the same day) on the head of each repo's production branch and pushes it.
2. **Set the Sentry release** to that tag on the server before restarting: `SENTRY_RELEASE=<tag>` in the app's `.env` (the Jenkins step in `docs/DEPLOYMENT.md` does this). The frontend reports `sc-saas-frontend@<commit>` from its build instead; log that commit.
3. **Build now** on every affected job.
4. **Smoke check** (the release plan's checks, or at least: the app starts, one tenant loads, and the changed feature works).
5. **Add the row below**: newest first. "Verified by" is a person other than the deployer when possible.

## Merged, waiting for a build

Merged to a production branch but not built yet: a merge alone changes nothing on the servers. On 27 Oct the production backend was still running code from 14 Oct (SC-SAAS-BACKEND-3M, fixed on `main` by SAN-1872, still fired at 14:31 IST). Builds are planned for 31 Oct – 1 Nov (SAN-1939). When a job is built, move its row into the deploy table below and fill in who deployed, who verified it and the smoke result.

| Merged (IST) | Merge commit | Repo → branch | What |
|---|---|---|---|
| 2026-10-27 16:30 | #1972 `ae1608db` | sc-saas-frontend → `stagingdemo` | SAN-1939 stage 2: 89 commits incl. SAN-1959/2000 applicant token, SAN-1490 socket auth, SAN-2018 |
| 2026-10-27 11:39 | #49 `628b8263` | sanchiconnect-saas-tenants-admin → `main` | SAN-1939 release `stagingdemo → main` |
| 2026-10-27 11:37 | #2054 `cc8fb88d` | sc-saas-backend → `main` | SAN-1939 release `stagingdemo → main`: applicant-token route and `forms.public_share_token` (needed by the production admin since 26 Oct), SAN-1872. Needs `FACTACY_API_KEY` and the `log`-mode keys first |
| 2026-10-27 11:34 | #210 `5ba82490` | sanchiconnect-saas-tenants → `master` | SAN-1939 release `stagingdemo → master` (`TENANT_SETTINGS_KEY_MODE=log`) |
| 2026-10-27 10:55 | #2053 `c0356b69` | sc-saas-backend → `stagingdemo` | SAN-1939 stage 2 |
| 2026-10-27 10:23 | #209 `7c0a9dbe` | sanchiconnect-saas-tenants → `stagingdemo` | SAN-1939 stage 2 |
| 2026-10-27 10:22 | #48 `658ea81c` | sanchiconnect-saas-tenants-admin → `stagingdemo` | SAN-1939 stage 2 |
| 2026-10-27 10:09 | #2643 `0763339a` | sc-saas-admin → `main` | SAN-2048 hotfix: Learning Management → Reports "Subquery returns more than 1 row" |
| 2026-10-27 10:09 | #40 `af1c90e7` | sc-saas-3rdparty-webservices → `master` | SAN-1939 release (`GATEWAY_KEY_MODE=log`); SAN-2049 SMTP 465 is not in it (still on `ai_native_setup`) |
| 2026-10-26 | #93 `277ceb34` | ai-startups-analyzer → `main` | Already in the table below as "not live yet"; still needs "Build now" |

| Date (IST) | Tag / commit | Repo → branch | Jobs / tenants | What (PRs, issues) | Deployed by | Verified by | Smoke result | Sentry release |
|---|---|---|---|---|---|---|---|---|
| 2026-10-26 | #2642 (merge `039df75a`, untagged) | sc-saas-admin → `main` | SaaS - Backoffice (Admin) | SAN-2043: analysis worker defines `imagekit_url` ("Couldn't prepare analysis" on forms with image/video answers) | _to fill_ | _to fill_ | _to fill_ | not set |
| 2026-10-26 | #93 (merge `277ceb34`, untagged) | ai-startups-analyzer → `main` | analyzer API (production) | Release `stagingdemo → main`: CORS fails closed (SAN-2017), thesis drafting, `/health` with DB check (SAN-1574), Sentry prover (SAN-1572), CI spine | _to fill_ | _to fill_ | ⚠️ not live yet: at 21:3x IST `api.analyzer.sanchiapp.com/api/v1/health` still returned `{"status":"ok"}` without `checks.db`, i.e. the old code | not set |
| 2026-10-26 | #2639 (merge `bfe5e116`, untagged) | sc-saas-admin → `main` | SaaS - Backoffice (Admin) | Release `stagingdemo → main` (SAN-1939): security fortnight, CI spine, notification centre, fixes. **Ahead of the backend**: public submission links (SAN-35) and Backdoor Access (SAN-1959) need the backend release | _to fill_ | _to fill_ | _to fill_ | not set |
| 2026-10-26 | #2636 (merge `c365aa0b`, untagged) | sc-saas-admin → `main` | SaaS - Backoffice (Admin), Firstwings | SAN-2036: "Show in Download Ratings?" switch adds form answers to the ratings export | Nirmal | Nirmal ("working on production") | ✅ | not set |
| 2026-10-22 | #203 (merge `14608db3`, untagged) | sanchiconnect-saas-tenants → `master` | tenants API (production) | SAN-1659: read-only, HMAC-signed tenant list endpoint for the Command Centre | _to fill_ | _to fill_ | _to fill_ | not set |
| 2026-10-22 | #204 (merge `366e9661`, untagged) | sanchiconnect-saas-tenants → `master` | tenants API (production) | SAN-44 hotfix: `tenant-settings/%25` leaked a tenant's secrets; exact hostname match | _to fill_ (PR merged by Aman) | _to fill_ | _to fill_ | not set |
| 2026-10-15 | #84 (merge `1ab9186`), #85, #86 (untagged) | ai-startups-analyzer → `main` | analyzer API (production) | SAN-1920: thesis prose mode (#84); SQLAlchemy `[asyncio]` <2.1 so the app boots (#85); API-key check off the event loop (#86) | Nirmal | Nirmal (iiitdic: thesis and Prepare Analysis work) | ✅ after #86; #84's build alone failed to start (greenlet), fixed by #85 | not set |
| 2026-10-15 | #2628 (untagged) | sc-saas-admin → `main` | SaaS - Backoffice (Admin) | SAN-1921: analysis worker shows its failure reason | Nirmal | Nirmal (iiitdic) | ✅ | not set |
| 2026-10-14 | #2616 (untagged) | sc-saas-admin → `main` | SaaS - Backoffice (Admin) | SAN-1908: apostrophes in master data broke the Applications Kanban | not recorded (PR merged by Aman) | Nirmal (production bug report closed) | ✅ | not set |

## Before this log (merges only)

Production-branch merges from 1 to 13 Oct 2026, taken from GitHub. Who deployed and verified them was not recorded.

| Merged | Repo → branch | PR |
|---|---|---|
| 2026-10-12 | sc-saas-admin → `main` | #2607 (from `stagingdemo`) |
| 2026-10-11 | sc-saas-backend → `main` | #2027 (from `stagingdemo`) |
| 2026-10-11 | sc-saas-frontend → `main` | #1938 (from `sanchiconnect`) |
| 2026-10-11 | sc-saas-admin → `main` | #2602 (from `stagingdemo`) |
| 2026-10-11 | sc-saas-3rdparty-webservices → `master` | #27 (from `development`) |
| 2026-10-08 | sanchiconnect-saas-tenants → `master` | #197 (from `development`) |
| 2026-10-08 | sanchiconnect-saas-tenants-admin → `main` | #36 (from `development`) |
| 2026-10-05 | sc-saas-frontend → `main` | #1908 (from `sanchiconnect`) |
| 2026-10-03 | sc-saas-admin → `main` | #2566 (from `stagingdemo`) |
| 2026-10-02 | sc-saas-backend → `main` | #1994 (from `stagingdemo`) |
| 2026-10-02 | sc-saas-frontend → `main` | #1902 (from `sanchiconnect`) |
| 2026-10-01 | sc-saas-admin → `main` | #2558 (from `stagingdemo`) |
