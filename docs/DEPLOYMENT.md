# Branch model and deployment

Decided 2026-10-13 by Nirmal Singh. This is the branch-model record for L0 Foundations (SAN-1564) and the decision for SAN-1570, in the CI Pipeline and Gates project (P-SAN-75).

## The release path

Every repo follows the same four long-lived branches:

```
ai_native_setup → development → stagingdemo → main / master
    (dev 1)        (dev 2)     (production    (production,
                                    demo)          clients)
```

| Branch | Purpose | Deployed by | How code gets in |
|---|---|---|---|
| `ai_native_setup` | Daily developer work and fixes | Jenkins, dev server 1 | Direct push (for now) |
| `development` | Second dev server, integration check | Jenkins, dev server 2 | PR from `ai_native_setup` |
| `stagingdemo` | The demo site, running on production (sc-saas-e2e also runs here) | Jenkins, production demo | PR from `development` |
| `main` / `master` | Client production | Production Jenkins | PR from `stagingdemo`, or a hotfix PR |
| `sanchiconnect` (sc-saas-frontend only) | SanchiConnect incubation, on production | Production Jenkins | PR (protected like `main`); outside this path today, see Other branches below. Never delete. |

`main` / `master`, `stagingdemo` and the frontend's `sanchiconnect` are fixed names: production Jenkins jobs depend on them (all three deploy to production: clients, the demo, and SanchiConnect incubation; corrected 2026-10-14). `sanchiconnect-saas-tenants` and `sc-saas-3rdparty-webservices` use `master` for production; every other repo uses `main`.

## Retired branches

`initial_development` and `pre_development` were retired on 2026-10-13. They held no code of their own, only merge commits, and added two PR hops to every release. Before deletion each tip was tagged `archive/<branch>` (backend, frontend and admin had both; tenants had `pre_development`; the analyzer had `initial_development`), and no Jenkins job built from either branch. To restore one: `git push origin archive/<branch>:refs/heads/<branch>`.

"Automatically delete head branches" is **off** in every repo. It was briefly on (13 Oct) and deleted the long-lived `ai_native_setup_<name>` branches as soon as their PRs merged; those were restored at their exact commits. Turn it on only once the team works on short-lived per-issue branches.

Each developer keeps one long-lived personal branch, `ai_native_setup_<name>` (confirmed 2026-10-19, replacing the 2026-10-13 plan to move to short-lived topic branches). Work starts on it, and it reaches the release path through `ai_native_setup`:

```
ai_native_setup_<name> → ai_native_setup → development → stagingdemo → main / master
```

The personal branches are not deployed and are never deleted ("Automatically delete head branches" stays off). Only `ai_native_setup` and the branches after it deploy.

## Production hotfixes

1. Branch from `main` / `master`: `hotfix/san-123-slug`.
2. PR into `main` / `master`. It goes through the same checks and review as any other PR into production (branch protection belongs to the target branch, not the source).
3. The same day, PR the fix into `ai_native_setup` so it reaches every lower branch on the next release.
4. Delete the hotfix branch.

A fix that reaches production without step 3 gets silently dropped by the next release. That already happened once: SAN-1044 was fixed on `pre_development` and never reached `ai_native_setup`.

## Gates

Every deploying branch has a gate; nothing deploys unverified.

- **Checks:** install, lint, test, build and secret scan, from the CI workflow in each repo.
- **Review:** one approval from someone other than the author.

| Branch | Gate | Turned on at |
|---|---|---|
| `ai_native_setup` | Checks on every push; the dev 1 deploy is triggered only when the checks are green | Checks report since 13 Oct 2026 (L1); L2 makes the deploy wait for green |
| `development` | Checks + review on the PR | Review required since 13 Oct 2026; checks required from L2 |
| `stagingdemo` | Checks + review on the PR | Review required since 13 Oct 2026; checks required from L2 |
| `main` / `master` | Checks + review on the PR (hotfixes included) | Review required since 13 Oct 2026; checks required from L2 |

**Unguarded routes (SAN-1937, 2026-10-19).** `npm run gates` in sc-saas-backend, sanchiconnect-saas-tenants and sc-saas-3rdparty-webservices includes a required `unguarded-routes` gate (`scripts/unguarded-routes.js`, same file in all three).
- It fails on any controller route without an auth guard that is neither allow-listed (kind, reason, owner) nor among the recorded known gaps (`unreviewed`, which may only shrink).
- Baseline:

| Repo | Routes | Guarded | Allow-listed | Known gaps |
|---|---|---|---|---|
| backend | 853 | 447 | 2 | 404 |
| tenants | 72 | 13 | 4 | 55 |
| 3rd-party | 36 | 0 | 1 | 35 |

### Branch protection settings (SAN-1569)

GitHub repository rulesets, identical in all seven repos. **In effect** (re-checked 2026-10-14): the rulesets moved with the repos to `sanchiconnect-org` under the same IDs, were unenforceable for a few hours while the organization was on the free plan (the API answered "Upgrade to GitHub Pro"), and are enforced again since the organization moved to **GitHub Team** the same day. Both rulesets are `active` with no bypass actors in all seven repos, and GitHub reports `deletion, non_fast_forward, pull_request` on every release branch and `deletion, non_fast_forward` on `ai_native_setup`. Keep the organization on a paid plan: on the free plan, private repositories get no rulesets, branch protection, secret scanning or CodeQL.

| Ruleset | Branches | Rules |
|---|---|---|
| release branches | `main`, `master`, `stagingdemo`, `development`; in sc-saas-frontend also `sanchiconnect` (added 2026-10-14) | Pull request required (no direct pushes); 1 approving review, never the author's own; stale approvals dismissed on new commits; the last push must be approved by someone else; no force-push; no deletion; no bypass actors |
| dev branch | `ai_native_setup` | No force-push; no deletion; direct pushes allowed |

Not yet enabled, at L2: required status checks (SAN-1583) and required CODEOWNERS review (SAN-1584). **SAN-1583's rulesets exist but are disabled** (2026-10-19). Each repo has a `required checks (L2, SAN-1583)` ruleset on `main`/`master` (plus `sanchiconnect` in the frontend), with branches required to be up to date. The required checks are:
- the CI job: `node`, `php`, `python`, or the frontend's `build` + `unit-tests`;
- `gitleaks`;
- the repo's contract checks, plus `migrations` in backend and tenants.

They stay disabled until the SAN-1939 release puts the CI workflows on each production branch. Until then a required check could never run, which would block every hotfix PR (such as #204). To turn one on, first confirm on any PR into the branch that every listed check reports. Then set the ruleset's Enforcement to Active. The ruleset IDs are on SAN-1583. The contract checks (`flags`, `scoring-contract`, `tenant-contract`, `api-contract`) can be made required: they run on every PR and push and decide in their first step whether the files they protect changed (SAN-1596), so an unrelated PR gets a passing check in seconds instead of a check that never reports. Never add an `on.paths` filter to a workflow that is, or will be, a required check. The Playwright smoke check `smoke / e2e` (`smoke.yml` in sc-saas-frontend and sc-saas-admin, calling `sc-saas-e2e`'s `e2e.yml` against staging on every PR to `main`) reports only until SAN-1585 adds it to the `main` ruleset of both repos, after two green weeks with no quarantined test older than a week; it needs a `staging` Environment holding the QA secrets in each of the two repos. In an emergency the account owner can disable a ruleset in the repo's Settings → Rules; that change is logged and should be reversed the same day.

## Current state per repo

Long-lived branches on each remote, checked 2026-10-14: every repo has all four.

| Repo | Production | `stagingdemo` | `development` | `ai_native_setup` |
|---|---|---|---|---|
| sc-saas-backend | `main` | yes | yes | yes |
| sc-saas-frontend | `main` | yes | yes | yes |
| sc-saas-admin | `main` | yes | yes | yes |
| sanchiconnect-saas-tenants | `master` | yes | yes | yes |
| sc-saas-3rdparty-webservices | `master` | yes | yes | yes |
| sanchiconnect-saas-tenants-admin | `main` | yes | yes | yes |
| ai-startups-analyzer | `main` | yes | yes | yes |

**Production vs `ai_native_setup` (checked 2026-10-14).** GitHub shows production ahead of `ai_native_setup` in every repo (for example backend 53, admin 61 commits), but those are merge commits from release PRs: compared by content (`git cherry`), production has no change that `ai_native_setup` lacks. No catch-up merge is needed; merging `main`/`master` back into `ai_native_setup` at the next release just clears the counter.

**Other branches (checked 2026-10-14).** Besides the four above:

- Per-developer `ai_native_setup_<name>` (aman, mahima, sandeep, vishali) in every repo: still used for PRs (e.g. admin PR #2619). Kept until the team moves to short-lived per-issue branches.
- **Frontend `sanchiconnect` is a production branch: it deploys the SanchiConnect incubation production site. Never delete it.** It has no work that `ai_native_setup` lacks. Since 2026-10-14 it is in the frontend's release-branch ruleset (PR with one non-author approval, no force-push, no deletion), but it is still outside the release path above; its Jenkins job belongs in the table below.
- Archived and deleted 2026-10-14 (no work missing from `ai_native_setup`): backend `ai_native_updates_aman`, `api_integration_aman`, `backend_new_branch_aman`, `corporate_logo_fix`. Each tip is kept as tag `archive/<branch>`; restore with `git push origin archive/<branch>:refs/heads/<branch>`.
- Archived and deleted 2026-10-14 by decision, although never merged (the work now exists only in the tags): backend `update-the-api` (2 commits, a TypeORM 0.3.31 upgrade) and `language_updates` (1 commit); frontend `language_updates` (61 translation commits, Apr 2026). Tags `archive/<branch>`.
- Analyzer `ai_analyizing_new_updates_aman` renamed 2026-10-14 to `ai_native_setup_aman` (same tip `7746fee`, also kept as tag `archive/ai_analyizing_new_updates_aman`), matching the `<base>_aman` naming in the other repos. Its SAN-1015 DB pool fix (`pool_pre_ping` / `pool_recycle`) is already in `ai_native_setup` (`e26b527`) and `main`, so no PR is needed.

## Retirement checklist (2026-10-13)

1. **SAN-1044: nothing to recover.** Backend `971836f3` (on `pre_development`) has an identical twin, `49d6e84c` (same patch ID), merged into `ai_native_setup` through PR #1975. No repo had production code missing from `ai_native_setup`. Done.
2. **Jenkins.** Confirmed that no Jenkins job builds from `initial_development` or `pre_development`. Done.
3. **Archive, then delete.** Done: 8 `archive/<branch>` tags pushed, 8 branches deleted. (Auto-delete of merged PR branches stays off; see Retired branches.)
4. **Fill the gaps. Done:** by 2026-10-14 every repo has `development` and `stagingdemo` (tenants, 3rdparty and tenants-admin gained them 8-11 Oct). Whether each has a staging Jenkins job is part of the Jenkins table below.

## GitHub organization

On 2026-10-14 the repos moved from the `sanchiconnect` personal account to the **`sanchiconnect-org`** organization. `github.com/sanchiconnect/<repo>` still redirects, but only until someone creates a repo of the same name under the `sanchiconnect` account, which still exists. Use `sanchiconnect-org` everywhere: in git remotes (`git remote set-url origin https://github.com/sanchiconnect-org/<repo>.git`), Jenkins job and server clone URLs, and `gh -R`. The contract workflows check out sibling repos with `${{ github.repository_owner }}/<repo>`, so they follow the org automatically.

## CI secrets

| Secret | Repos | What it is | Used by |
|---|---|---|---|
| `CONTRACT_CHECK_TOKEN` | sanchiconnect-saas-tenants, sc-saas-backend, sc-saas-frontend, sc-saas-admin, ai-startups-analyzer | Fine-grained personal access token created from the `sanchiconnect` account with **Resource owner: `sanchiconnect-org`** (a token owned by the personal account cannot read the org's repos). Repository access: those five repos **plus sanchiconnect-saas-tenants-admin** (tenants' `tenant-contract.yml` reads both PHP panels' copy of the ai_credit_* schema, SAN-1595), nothing else. Permissions: **Contents: Read-only** (nothing else). Expiry: 1 year (current token expires 2027-10-15); renew before it lapses. | The L3 contract checks, which check out the other repos of a contract to compare them: `flags.yml` (SAN-1592), `scoring-contract.yml` (SAN-1594) and `tenant-contract.yml` (SAN-1591). GitHub's built-in token can only read the repo it runs in. |

To create it: github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token (fine-grained tokens are always created from a personal account's settings, never the org's), set Resource owner to `sanchiconnect-org`, then the settings above. Check the token's page afterwards: it must list the six repos and Contents: Read-only. A token saved with repositories but no permission keeps no repositories at all, and the checks then fail at checkout with `403 Write access to repository not granted`. Test it with `curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $T" https://api.github.com/repos/sanchiconnect-org/sc-saas-backend/contents/README.md` (200 = good, 404 = no access). Then add it as a secret to the five repos that run the checks (tenants-admin only needs to be readable, it runs none) without pasting it anywhere else:

```bash
for r in sanchiconnect-saas-tenants sc-saas-backend sc-saas-frontend sc-saas-admin ai-startups-analyzer; do
  gh secret set CONTRACT_CHECK_TOKEN -R sanchiconnect-org/$r   # paste the token when prompted
done
```

### Slack alerts for CI (SAN-1600)

`ci-alerts.yml` in each of the seven repos posts to Slack when `ci`, `secret-scan` or a contract check fails on `main`/`master`, `stagingdemo` or `development` (a merge, or a release PR from one of them), and once more when that workflow is green again. `ai_native_setup` is left out on purpose. Without the secret the workflow only logs a warning.

| Secret | Repos | What it is |
|---|---|---|
| `SLACK_CI_WEBHOOK_URL` | all seven product repos | A Slack incoming-webhook URL for the channel the team watches (one URL can serve every repo). Treat it as a secret: anyone holding it can post to that channel. |

To create it: api.slack.com/apps → Create New App → From scratch (name it e.g. "SanchiSaaS CI", pick the workspace) → Incoming Webhooks → On → Add New Webhook to Workspace → choose the channel (e.g. `#ci-alerts`) → copy the URL. Then add it without pasting it anywhere else:

```bash
for r in sanchiconnect-saas-tenants sc-saas-backend sc-saas-frontend sc-saas-admin ai-startups-analyzer sc-saas-3rdparty-webservices sanchiconnect-saas-tenants-admin; do
  gh secret set SLACK_CI_WEBHOOK_URL -R sanchiconnect-org/$r   # paste the URL when prompted
done
gh workflow run ci-alerts.yml -R sanchiconnect-org/sc-saas-backend   # test message; works once ci-alerts.yml is on main
```

GitHub only runs `workflow_run` triggers, and only allows manual runs, from the default branch's copy of a workflow, so `ci-alerts.yml` does nothing until it reaches each repo's `main`/`master` through the normal release path. To check the webhook before then, post to it directly from your own machine: `curl -X POST -H 'Content-Type: application/json' -d '{"text":"test"}' "$SLACK_CI_WEBHOOK_URL"` (read the URL into the variable with `read -s SLACK_CI_WEBHOOK_URL` so it stays out of your shell history).

## Jenkins jobs

None of the seven repos has a Jenkinsfile, so the branch-to-server mapping lives only in Jenkins. Recorded from the **production Jenkins** dashboard on 2026-10-14 (branches confirmed by Nirmal). Status: enabled jobs had a successful build about 2 days 17 hours earlier (a bulk deploy); ⊘ marks a disabled job.

**Demo and SanchiConnect stack (production servers)**

| Jenkins job | Repo | Branch |
|---|---|---|
| Demo - SaaS API, Demo - SaaS API - 2, Demo - SaaS API - 3 | sc-saas-backend | `stagingdemo` |
| SanchiConnect - Live - SaaS API | sc-saas-backend | `stagingdemo` |
| Demo - API Builder | sc-saas-backend (build step) | `stagingdemo` |
| Demo - Frontend | sc-saas-frontend | `stagingdemo` |
| Demo - Frontend Sanchi Connect | sc-saas-frontend | `sanchiconnect` |
| Demo - Backoffice | sc-saas-admin | `stagingdemo` |

**Client production**

| Jenkins job | Repo | Branch |
|---|---|---|
| SaaS - Frontend | sc-saas-frontend | `main` |
| SaaS - Backoffice (Admin) | sc-saas-admin | `main` |
| SaaS - 3rd Party Services | sc-saas-3rdparty-webservices | `master` |
| SaaS API - Builder | sc-saas-backend (build step) | `main` |
| SaaS API - Client NN - <client> (one backend per client) | sc-saas-backend | `main` |
| (job not on this dashboard) | sanchiconnect-saas-tenants (cockpit API, shared by every client) | `master` |
| (job not on this dashboard) | sanchiconnect-saas-tenants-admin | `main` |
| (job not on this dashboard) | ai-startups-analyzer | `main` |

Client backend jobs, enabled: 01 Sine Mumbai, 07 IIIT Dic, 11 CII, 14 VGU, 17 ISBA, 19 SIIC Program, 21 Ginserv, 22 CDIIC, 23 SINGAM, 24 First Wings, 26 AMSIM, 27 iHUB, 30 Tally Startup Collective, 31 Runway, 34 Ieema, 35 Bharat Innovates, 36 IIML EIC, 37 Tally MSME Honours, 38 Nagpur Entrepreneurship Mission, 39 PSG Step Incubation, 40 ISGBB Bharat Cares, 41 T-Rise Tripura, 42 Supernova Gdai, 43 Healthx Elevate, 44 AIC Techno, 45 AKTU.

Disabled (⊘): 02 Preseed Accelerator, 03 Leap Unicorn, 04 T-Hub, 04 T-Hub Math, 05 Nass Com, 06 SIIC Kanpur, 08 Startup Themezha, 09 SPJIMR, 10 N.COE, 12 1Trepreneur, 13 Innovher, 15 8x Ventures, 16 IIT Tirupati, 18 Boss Ladies, 20 Jubiliant, 25 Pitch To VC, 28 SanchiAccel, 29 Startup Chattisgarh, 33 Truleum. (No Client 32.)

The tenants API, tenants-admin and the AI analyzer deploy to production from `master`/`main` only (Nirmal, 2026-10-14); their job names are not on this dashboard.

**Development (dev Jenkins, confirmed by Nirmal 2026-10-14):** `ai_native_setup` deploys dev server 1 (thub.sanchidev.in: frontend thub.sanchidev.in, backend api.thub.sanchidev.in, admin adm.thub.sanchidev.in, tenants API api.tenants.sanchidev.in); `development` deploys dev server 2.

**How a deploy starts (Nirmal, 2026-10-14):** every deploy, on dev and production Jenkins alike, is started **by hand with "Build now"** on the job. No job runs by itself on a push (no webhook or poll trigger), and this stays manual for now. Merging to a branch therefore does not deploy it: the change goes live only when someone builds that branch's job, which is how a branch and its server drift apart (SAN-589).

**Not recorded yet:** the dev Jenkins job names, and each dev job's server/URL.

## Deploy workflow (SAN-1602; all seven repos since 2026-10-19)

**All seven repos now carry the same three files** (2026-10-19):
- `.github/workflows/deploy.yml`;
- `.github/scripts/deploy-rollout.sh`;
- `.github/scripts/jenkins-build.sh`.

Change them in every repo together. They grew out of the sc-saas-3rdparty-webservices pilot described below, and keep its settings, so a pilot setup keeps working.

**Jobs per Environment:** either the secret `JENKINS_JOB` (one job) or the variable `JENKINS_JOB_PATTERN` (a regex over Jenkins' enabled jobs; the backend's per-tenant case is below).

**Branches and Environments:**

| Push to | Tag | Environment |
|---|---|---|
| `stagingdemo` | `staging-YYYY.MM.DD-<sha7>` | `staging` |
| `main`/`master` | `YYYY.MM.DD-<sha7>` | `production` |
| `sanchiconnect` (frontend only) | `sanchiconnect-YYYY.MM.DD-<sha7>` | `sanchiconnect` |

The `sanchiconnect` Environment holds the `Demo - Frontend Sanchi Connect` job and needs its own reviewer. Every repo's deploy stays inert until its Environments and secrets exist (SAN-1597).

The rest of this section describes the original pilot:

Decided by Aman on 2026-10-15: Jenkins and the servers stay; a GitHub Actions workflow (`.github/workflows/deploy.yml`) **tags every release and triggers the Jenkins job through its API**. Staging follows `stagingdemo`, production follows `main`/`master`, the same as the release path above. The workflow never touches a server.

| Push to | Tag | GitHub Release | Then |
|---|---|---|---|
| `stagingdemo` | `staging-YYYY.MM.DD-<sha7>` | pre-release | triggers the staging Jenkins job |
| `master` / `main` | `YYYY.MM.DD-<sha7>` (date in IST) | release | waits for the reviewer on the `production` Environment, then triggers the production Jenkins job |

The tag is what the rollback redeploys (SAN-1604) and what Sentry's release should carry. A re-run never creates a tag twice.

**It is safe to merge before any setup.** The `release` job needs nothing but the repo, so tags and Releases start at once. The `deploy` job ends green with a warning until its Environment has the secrets below.

**Setup, for the org owner. Order matters:**
1. Create the Environments `staging` and `production` (Settings → Environments). On `production`, add a **required reviewer who is not the person who merged**. A GitHub Environment is created on first use with *no* rules, so if the secrets exist before the reviewer does, a production deploy runs unreviewed.
2. Only then add, to each Environment, the secrets `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN` (a Jenkins API token of a user that may only build that job) and `JENKINS_JOB` (the job name, for example `SaaS - 3rd Party Services`; URL-encode spaces as `%20`).
3. Optional variables: `SERVICE_URL` (after the build the workflow checks that `GET <SERVICE_URL>/` answers 200) and `JENKINS_TAG_PARAMETER` (the name of a job parameter, for example `RELEASE_TAG`, that receives the tag so the job can set `SENTRY_RELEASE` to it; the job must be parameterised).

**Open questions for Nirmal** (they cannot be answered from the repos): is the production Jenkins reachable from GitHub's runners (if it sits behind an IP allow-list, a self-hosted runner is needed); which job is the **staging** job for this service (the dashboard above lists none for `sc-saas-3rdparty-webservices`); is the production job parameterised.

**Not in the pilot yet:** the smoke suite (sc-saas-e2e covers the PWA and the admin panel, not this service; the `SERVICE_URL` check is the substitute), a Sentry release created by the workflow, and the other repos except the backend (below).

### Backend: one rollout over every tenant job (SAN-1603)

`sc-saas-backend/.github/workflows/deploy.yml` follows the pilot, but deploys one Jenkins job per tenant. Pushes to `stagingdemo` go to the staging Environment, pushes to `main` to production.
- **The tenant list comes from Jenkins at run time:** every enabled job whose name matches the Environment variable `JENKINS_JOB_PATTERN`, in name order. The tenants DB has no tenant-to-job mapping, so a client job added, disabled or removed in Jenkins changes the rollout with no workflow edit.
- **One job, one approval.** GitHub asks a reviewer for every job that uses the `production` Environment, so the rollout is one job that deploys the tenants one after another, not 26 jobs.
- **The first failure stops the rollout.** The tenants after it keep the previous version and the run fails. GitHub's failed-run notification is the page.
- **The step summary** has a row per tenant: its result (SUCCESS, FAILURE, TIMEOUT or not started) and its Jenkins build link.

Each Environment needs:
- the secrets `JENKINS_URL`, `JENKINS_USER` and `JENKINS_TOKEN`;
- the variable `JENKINS_JOB_PATTERN`, for example production `^SaaS API - Client [0-9]+ - ` and staging `^(Demo - SaaS API|SanchiConnect - Live - SaaS API)`.

Optional variables:
- `JENKINS_BUILDER_JOB`: `SaaS API - Builder` or `Demo - API Builder`, built once before the tenants, if the client jobs depend on it;
- `JENKINS_TAG_PARAMETER`;
- `JENKINS_WAIT_MINUTES` (default 30 per job).

Same setup order as above: the Environment and its reviewer first, then the secrets.

Open questions, the same as the pilot's, plus one: do the client jobs build their own `dist/` or copy it from the Builder job?

## Deploy log, release tags and the Sentry release (SAN-1626)

Every production deploy gets a row in `docs/DEPLOY-LOG.md` (what, where, who deployed, who verified, smoke result). Before pressing "Build now", tag the production branch with `scripts/tag-release.sh <repo> ...` (creates and pushes `release-YYYY-MM-DD`, `-2` for a second release the same day).

So that Sentry shows which release is live, each production Jenkins job sets `SENTRY_RELEASE` to that tag before restarting the app. Add this to the job's shell step after the checkout (the analyzer's `.env` is in `api/`; the frontend needs nothing, it reports its build commit):

```bash
git fetch --quiet --tags origin
TAG="$(git describe --tags --exact-match --match 'release-*' HEAD 2>/dev/null || git rev-parse --short HEAD)"
if grep -q '^SENTRY_RELEASE=' .env; then
  sed -i "s/^SENTRY_RELEASE=.*/SENTRY_RELEASE=${TAG}/" .env
else
  echo "SENTRY_RELEASE=${TAG}" >> .env
fi
```

An untagged build falls back to the short commit, which still identifies what's live.

## Database migrations step (SAN-1605)

`sc-saas-backend` and `sanchiconnect-saas-tenants` change their schema through TypeORM migrations (SAN-1630). Each Jenkins job for either service runs the migrations against its own database **after the build and before the app restarts**, and stops if they fail. For the backend that means every client job, each against the database in its own `.env`.

Add this to the job's shell step, between `npm run build` and the pm2 restart:

```bash
set -e
npm run migration:deploy   # exit 1: a migration failed, so the app is not restarted
```

`set -e` is what stops the job: Jenkins marks the build failed and the old version keeps running. Make sure the job's failure notification reaches a person (email or Slack), since that is the only page.

What the step does (`src/core/database/deploy-migrate.ts` in each repo):

| Database | Result |
|---|---|
| Nothing pending | "is up to date", exit 0 |
| Has recorded migrations, some pending | runs them, one transaction each, exit 0. On failure: exit 1, the failed one isn't recorded. |
| Never recorded a migration, empty | runs every migration (builds the schema), exit 0 |
| Never recorded a migration, matches the entities | **adopts** it: records every migration as applied without running it (`--fake`), exit 0 |
| Never recorded a migration, differs from the entities | prints the differences. While `synchronize` is still on (until SAN-1630 phase 4) it exits 0 and leaves them to `synchronize`. With `MIGRATIONS_STRICT=true` it exits 1. |
| Can't connect | exit 2 |

It holds a MySQL lock (`GET_LOCK('sc_deploy_migrate')`) while it works, so two jobs on one database (the three Demo API jobs) take turns.

MySQL can't roll back DDL (`CREATE`, `ALTER`, `DROP`), so a migration that fails halfway can leave part of its change behind. Write one schema change per migration. If one fails, read the log, fix the database or the migration, and rebuild.

**Rollout**
1. Add the step to the dev server 1 jobs (backend and tenants) and build. The log should say "adopted". If it says "left to synchronize", that database has drift: build once more after the app has started (synchronize applies the drift at boot), and the next run adopts it.
2. Then dev server 2, the Demo jobs, SanchiConnect, one client job, every other client job, and the cockpit job, in that order. Record each one in `docs/DEPLOY-LOG.md`.
3. Turning `synchronize` off (SAN-1630 phase 4) is per job, in that job's `.env`. Once its log says "adopted" or "up to date", add:
   - `DB_SYNCHRONIZE=false`;
   - `MIGRATIONS_STRICT=true`, so a drifted database stops the deploy instead of being left to synchronize.

   Then rebuild. With synchronize off, the app checks the schema at boot:
   - `SCHEMA_CHECK_MODE=log` (default) logs any difference as an error and keeps running;
   - `enforce` refuses to start.

   Go back by removing `DB_SYNCHRONIZE`.

**Open questions:**
- Does each `SaaS API - Client NN` job run its own `npm ci && npm run build`, or does it copy `dist/` from `SaaS API - Builder`? The step needs `dist/`, `node_modules` and the client's `.env` in the job's folder.
- Which notification does a failed production build send today?

## Rollback

**Redeploy a previous tag (SAN-1604, built 2026-10-19).** Actions → deploy → Run workflow, and set `rollback_tag` to an earlier release tag, e.g. `2026.10.18-abc1234`.
- **No new tag is made.** The tag's prefix picks the Environment, and that Environment's reviewer approves as usual.
- **Every job is rebuilt with that tag**, in order, stopping at the first failure.
- **The tag is checked first:** a name that is not a tag this workflow makes, or a tag that does not exist, is refused before anything runs.
- **It needs `JENKINS_TAG_PARAMETER` and Jenkins jobs that check out the tag they are given.** A job that builds its branch tip would "roll back" to the current code. So without the parameter the rollback refuses to run, and the git revert below is the way back.
- **Not drilled yet:** a drill needs a parameterised job. Until then, the method below is the one that has been used.

Chosen method (Nirmal, 2026-10-14): **revert in git, then rebuild.** None of the repos has a Jenkinsfile or a rollback script, and Jenkins jobs build the tip of their branch, so the branch itself is what gets rolled back.

1. Find the bad commit on the deploy branch (`main`/`master`, `stagingdemo`, or frontend `sanchiconnect`) and revert it on a hotfix branch: `git revert <sha>` (for a merged PR, `git revert -m 1 <merge-sha>`). Never force-push or reset; the protected branches block it anyway.
2. Open a hotfix PR into the deploy branch. It needs one approval from someone other than the author, so line up a second person as soon as a rollback is likely.
3. After the merge, press **"Build now"** on every Jenkins job that received the bad deploy. For sc-saas-backend that is each affected client job (`SaaS API - Client NN - ...`, up to 26), not one job.
4. Bring the revert back to `ai_native_setup` (cherry-pick, as with any hotfix) so the next release does not redeploy the bad code.

**Two things a code rollback does not undo:**

- **Database schema (sc-saas-backend and sanchiconnect-saas-tenants).** Both run TypeORM `synchronize: true` with no migrations, so the app alters its tables at startup. Reverting the code does not remove a column the bad deploy added, and if it dropped or renamed a column, that column's data is already gone. Before deploying any change to an entity, take an RDS snapshot; it is the only undo for the database. The PHP panels and the 3rd-party gateway have no schema step, so for them the revert is a full rollback.
- **Cached frontend (sc-saas-frontend is a PWA).** Browsers keep the cached build, so after a rollback some users still run the bad version until they reload or the service worker updates.

## Health endpoints (SAN-1574)

Every service answers an unauthenticated `GET` for the Observability Command Centre probes. It runs one trivial read and returns booleans and a timestamp only: no secrets, no tenant data, `Cache-Control: no-store`.

| Service | URL |
|---|---|
| sc-saas-backend | `https://<tenant api host>/api/health` |
| sanchiconnect-saas-tenants | `https://<cockpit api host>/api/health` |
| sc-saas-3rdparty-webservices | `https://<gateway host>/api/health` |
| ai-startups-analyzer | `https://<analyzer host>/api/v1/health` |
| sc-saas-admin | `https://<tenant admin host>/health.php` |
| sanchiconnect-saas-tenants-admin | `https://<tenants-admin host>/health.php` |

Response (HTTP 200 when every check passes, 503 otherwise):

```json
{ "status": "ok", "service": "sc-saas-backend", "checks": { "db": true }, "timestamp": "2026-10-21T09:48:24.000Z" }
```

- `status` is `ok` or `degraded`.
- `checks.db` is the result of `SELECT 1` (MySQL; the PHP panels and the analyzer use the main database, with a 3 s cap).
- The 3rd-party gateway has no database, so its `checks` is `{}` and it reports `ok` while the process answers.
- Not yet included: the tenants ecosystem-push counter (items that arrived in the last day and week). The `ecosystem_*` tables have no `created_at`, so it needs a migration first.
