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

The per-developer `ai_native_setup_<name>` branches are replaced by short-lived topic branches (`<name>/san-123-slug`, the branch name Linear generates), deleted after merge.

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

### Branch protection settings (SAN-1569)

GitHub repository rulesets, identical in all seven repos (the `sanchiconnect` account is on GitHub Pro, which private-repo protection requires):

| Ruleset | Branches | Rules |
|---|---|---|
| release branches | `main`, `master`, `stagingdemo`, `development`; in sc-saas-frontend also `sanchiconnect` (added 2026-10-14) | Pull request required (no direct pushes); 1 approving review, never the author's own; stale approvals dismissed on new commits; the last push must be approved by someone else; no force-push; no deletion; no bypass actors |
| dev branch | `ai_native_setup` | No force-push; no deletion; direct pushes allowed |

Not yet enabled, at L2: required status checks (SAN-1583) and required CODEOWNERS review (SAN-1584). The contract checks (`flags`, `scoring-contract`, `tenant-contract`, `api-contract`) can be made required: they run on every PR and push and decide in their first step whether the files they protect changed (SAN-1596), so an unrelated PR gets a passing check in seconds instead of a check that never reports. Never add an `on.paths` filter to a workflow that is, or will be, a required check. In an emergency the account owner can disable a ruleset in the repo's Settings → Rules; that change is logged and should be reversed the same day.

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
- Analyzer `ai_analyizing_new_updates_aman`: SAN-1015 DB pool fix (14 Oct), not yet merged; needs a PR into `ai_native_setup`.

## Retirement checklist (2026-10-13)

1. **SAN-1044: nothing to recover.** Backend `971836f3` (on `pre_development`) has an identical twin, `49d6e84c` (same patch ID), merged into `ai_native_setup` through PR #1975. No repo had production code missing from `ai_native_setup`. Done.
2. **Jenkins.** Confirmed that no Jenkins job builds from `initial_development` or `pre_development`. Done.
3. **Archive, then delete.** Done: 8 `archive/<branch>` tags pushed, 8 branches deleted. (Auto-delete of merged PR branches stays off; see Retired branches.)
4. **Fill the gaps. Done:** by 2026-10-14 every repo has `development` and `stagingdemo` (tenants, 3rdparty and tenants-admin gained them 8-11 Oct). Whether each has a staging Jenkins job is part of the Jenkins table below.

## CI secrets

| Secret | Repos | What it is | Used by |
|---|---|---|---|
| `CONTRACT_CHECK_TOKEN` | sanchiconnect-saas-tenants, sc-saas-backend, sc-saas-frontend, sc-saas-admin, ai-startups-analyzer | Fine-grained personal access token of the `sanchiconnect` account. Repository access: those five repos **plus sanchiconnect-saas-tenants-admin** (tenants' `tenant-contract.yml` reads both PHP panels' copy of the ai_credit_* schema, SAN-1595), nothing else. Permissions: **Contents: Read-only** (nothing else). Expiry: 1 year; renew before it lapses. | The L3 contract checks, which check out the other repos of a contract to compare them: `flags.yml` (SAN-1592), `scoring-contract.yml` (SAN-1594) and `tenant-contract.yml` (SAN-1591). GitHub's built-in token can only read the repo it runs in. |

To create it: github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token, with the settings above. Then add it as a secret to the five repos that run the checks (tenants-admin only needs to be readable, it runs none) without pasting it anywhere else:

```bash
for r in sanchiconnect-saas-tenants sc-saas-backend sc-saas-frontend sc-saas-admin ai-startups-analyzer; do
  gh secret set CONTRACT_CHECK_TOKEN -R sanchiconnect/$r   # paste the token when prompted
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
  gh secret set SLACK_CI_WEBHOOK_URL -R sanchiconnect/$r   # paste the URL when prompted
done
gh workflow run ci-alerts.yml -R sanchiconnect/sc-saas-backend   # test message; works once ci-alerts.yml is on main
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

**Not recorded yet:** the dev Jenkins job names, each job's server/URL, and whether any job starts by itself on a push (webhook/poll) or only from "Build now".
