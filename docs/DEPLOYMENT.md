# Branch model and deployment

Decided 2026-10-13 by Nirmal Singh. This is the branch-model record for L0 Foundations (SAN-1564) and the decision for SAN-1570, in the CI Pipeline and Gates project (P-SAN-75).

## The release path

Every repo follows the same four long-lived branches:

```
ai_native_setup → development → stagingdemo → main / master
    (dev 1)        (dev 2)       (staging)      (production)
```

| Branch | Purpose | Deployed by | How code gets in |
|---|---|---|---|
| `ai_native_setup` | Daily developer work and fixes | Jenkins, dev server 1 | Direct push (for now) |
| `development` | Second dev server, integration check | Jenkins, dev server 2 | PR from `ai_native_setup` |
| `stagingdemo` | Staging and QA (sc-saas-e2e runs here) | Staging Jenkins | PR from `development` |
| `main` / `master` | Production | Production Jenkins | PR from `stagingdemo`, or a hotfix PR |

`main` / `master` and `stagingdemo` are fixed names: the production and staging Jenkins jobs depend on them. `sanchiconnect-saas-tenants` and `sc-saas-3rdparty-webservices` use `master` for production; every other repo uses `main`.

## Retired branches

`initial_development` and `pre_development` are retired. They held no code of their own, only merge commits, and added two PR hops to every release.

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
| release branches | `main`, `master`, `stagingdemo`, `development` | Pull request required (no direct pushes); 1 approving review, never the author's own; stale approvals dismissed on new commits; the last push must be approved by someone else; no force-push; no deletion; no bypass actors |
| dev branch | `ai_native_setup` | No force-push; no deletion; direct pushes allowed |

Not yet enabled, at L2: required status checks (SAN-1583) and required CODEOWNERS review (SAN-1584). In an emergency the account owner can disable a ruleset in the repo's Settings → Rules; that change is logged and should be reversed the same day.

## Current state per repo

Branches as found on each remote on 2026-10-13. "Missing" means the branch does not exist yet in that repo.

| Repo | Production | `stagingdemo` | `development` | `ai_native_setup` | To retire |
|---|---|---|---|---|---|
| sc-saas-backend | `main` | yes | yes | yes | `initial_development`, `pre_development` |
| sc-saas-frontend | `main` | yes | yes | yes | `initial_development`, `pre_development` |
| sc-saas-admin | `main` | yes | yes | yes | `initial_development`, `pre_development` |
| sanchiconnect-saas-tenants | `master` | missing | yes | yes | `pre_development` |
| sc-saas-3rdparty-webservices | `master` | missing | yes | yes | — |
| sanchiconnect-saas-tenants-admin | `main` | missing | yes | yes | — |
| ai-startups-analyzer | `main` | missing | missing | yes | `initial_development` |

## Before retiring anything

These are preconditions, in order. Nothing is deleted until each one is done.

1. **Recover SAN-1044.** Backend commit `971836f3` (1:1 event emails CC fix) is on `pre_development` and in production, but not in `ai_native_setup`. Merge it back first.
2. **Repoint Jenkins.** Any Jenkins job that builds from `initial_development` or `pre_development` (a dev server is believed to deploy from `pre_development`) is moved to `ai_native_setup` or `development` before the branch goes.
3. **Fill the gaps.** Decide, per repo, whether tenants, 3rdparty, tenants-admin and the analyzer get a `stagingdemo` branch (and a staging Jenkins job), and whether the analyzer gets a `development` branch.
4. **Archive, then delete.** Tag each retired branch as `archive/<branch>` so nothing is lost, then delete it. Turn on "Automatically delete head branches" in every repo.

## Jenkins jobs

To be filled in from the Jenkins dashboard. None of the seven repos has a Jenkinsfile, so the branch-to-server mapping lives only in Jenkins.

| Jenkins job | Repo | Branch | Server / URL | Trigger (webhook / poll / manual) |
|---|---|---|---|---|
| | | | | |
