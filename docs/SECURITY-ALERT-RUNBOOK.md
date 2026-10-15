# Security-alert runbook

What to do when a security tool raises something. Covers the seven product repos. Part of the CI Pipeline and Gates project (P-SAN-75, SAN-1601). Facts below were checked against GitHub on 2026-10-14; update this page when a tool goes live.

**Status: draft.** Items marked `[DECISION PENDING]` need an answer from the dev lead before this page is final. Do not invent the answer.

## What is live, and what is not

| Source | State | Where you see it |
|---|---|---|
| Secret scan (gitleaks) | **Live** on every push and PR (`secret-scan.yml`, rules in `.gitleaks.toml`). Scans only new commits. Reports only; it blocks a merge once SAN-1583 makes it a required check. | A red `secret-scan` run; Slack alert (`ci-alerts.yml`) when it fails on `main`/`master`, `stagingdemo` or `development`. |
| GitHub secret scanning and push protection | **Not available.** The `sanchiconnect-org` organization is on the Team plan (since 2026-10-14), which does not include GitHub Secret Protection (a separate paid add-on; the API returns 404). The gitleaks workflow is the substitute, and it cannot stop a push: a secret is detected after it is already on GitHub. | n/a |
| Dependabot alerts | **Live in five repos, but reporting nothing in `sc-saas-3rdparty-webservices` and `ai-startups-analyzer`**, where an OSV scan of the lockfile finds 213 and 50 advisories (see the baseline). Alerts are most likely not enabled there. | Repo → Security → Dependabot, or `gh api repos/sanchiconnect-org/<repo>/dependabot/alerts?state=open`. Nothing notifies the team yet. |
| Dependabot version updates | **Merged in all seven repos** (`.github/dependabot.yml`, SAN-1599): one grouped weekly PR per ecosystem, minor and patch only. Dependabot reads the file only from the default branch, so the first PRs appear once it reaches `main`/`master`. | The weekly Dependabot PR in each repo. |
| Dependency review on PRs | GitHub's own check is **not available** (the dependency-graph compare API answers 403; it needs the paid Code Security add-on). `dependency-check.yml` (OSV-Scanner, SAN-1599) runs instead: it flags the vulnerabilities a PR adds to a lockfile. Advisory. | The `dependency-check` run: warnings on the PR and a summary on the run page. |
| Code scanning | **CodeQL is not available:** it needs GitHub Code Security, a separate paid add-on that the `sanchiconnect-org` Team plan does not include (the code-scanning API answers 403). **Semgrep** (open-source rules) runs instead, as `code-scan.yml` (SAN-1598). Advisory: it reports and never fails a build. | The `code-scan` run: a findings summary on the run page and a `semgrep-findings` artifact. |
| Secrets already in git history | Not re-reported on every push. Tracked in SAN-1562 (rotation). | SAN-1562 |

## Severity and response

Linear priority names match the Production Defects project, so an alert becomes an ordinary issue there. That project's own table maps Sentry levels, not security severity, so the mapping below is a proposal. `[DECISION PENDING]`

| Alert | Linear priority | Response time |
|---|---|---|
| A real secret in a commit, in any repo | Urgent | **Same day.** Start the leaked-secret steps below at once. |
| Dependabot **critical**, in code that production runs and that is reachable | Urgent | **Same day:** upgrade, or switch off the affected feature, or record why it is not reachable. |
| Dependabot critical, in dev-only or unreachable code | High | Within the week, with the reason written on the issue. |
| Dependabot **high** | High | Within the week. |
| Dependabot **medium** | Medium | In the weekly batch, or the next planned work on that repo. |
| Dependabot **low** | Low | Monthly batch. |
| CodeQL finding (once live) | Same table, by its severity | Same table |

## Who is paged

`[DECISION PENDING]` Name, per the dev lead:

- the person who answers a same-day alert, and a second person for when they are away (the CODEOWNERS pair `@nirmal8126` and `@Amank-sc` is the obvious starting point, as on the high-risk paths);
- the Slack channel the alert goes to (the CI failure alerts already use the channel behind `SLACK_CI_WEBHOOK_URL`, see `docs/DEPLOYMENT.md`);
- the org admin who can change rulesets and repo security settings (Nirmal, per the project's working rules).

## A secret was pushed (gitleaks red, or someone noticed)

A secret that has been pushed is compromised, even if the commit is later removed. Rotate first, investigate second.

1. **Stop.** Do not merge. Tell the person on call.
2. **Rotate it with its provider.** Make the old value stop working before anything else. Where our secrets live:
   - tenant settings in the tenants DB (SMTP passwords, per-tenant API keys, `ai_credits_internal_api_key`);
   - GitHub Actions secrets (`CONTRACT_CHECK_TOKEN`, `SLACK_CI_WEBHOOK_URL`);
   - provider accounts (S3, SendGrid, CometChat, VideoSDK, Easebuzz, WATI, Zoho, LLM keys).
3. **Remove it from the code** and load it from the deployment's own `.env` or secret store. Never put the new value in a commit, a Linear issue or chat.
4. **Purge it from history** if it is on a shared branch. The rulesets forbid force-pushes and have no bypass actors, so an org admin has to lift the ruleset for the repo briefly (Settings → Rules), rewrite history (`git filter-repo` or BFG), force-push, restore the ruleset the same day and ask everyone to re-clone. GitHub can still serve the old commit by hash and from PR refs and forks: if the secret was real, ask GitHub Support to purge the cached views. Rotation, not purging, is what makes the leak safe.
5. **Verify.** Check the provider's usage log for use of the old value between the push and the rotation; run `gitleaks detect` over the full history of the repo locally; confirm the app works with the new value.
6. **Record it.** File an Urgent issue in Production Defects with the repo, commit, what was rotated and when, and what the provider log showed. Link SAN-1562 if the secret is one of the known exposures.

Exceptions that are not leaks: the CloudFront key files in `sc-saas-backend` (`cloudfront-*.pem`) are committed on purpose and allow-listed in `.gitleaks.toml`; do not rotate them for being flagged.

## A Dependabot alert

1. Open the alert; read the affected package, the range that fixes it and whether the vulnerable code path is used (production dependency or dev-only, reachable or not).
2. Create or update an issue in Production Defects with the priority from the table above. Put the repo label on it.
3. Fix by upgrading the package. Production runs Node 16 (backend) and Node 18 (tenants), and PHP 8.1 for the panels: a fix that needs a newer runtime is a bigger change, so say so on the issue rather than forcing the upgrade (the SAN-76/78 outages came from dependency drift).
   - **Do not stop at the first fixed version the alert names.** Check the version you pick with OSV-Scanner first (put it in a scratch `package.json`, run `npm install --package-lock-only`, then `osv-scanner scan source --lockfile package-lock.json`). The first run of this runbook, mysql2 (SAN-1916), showed that the "fixed" 3.9.7 and 3.9.9 still carried other advisories while 3.24.6 and its whole tree carried none, and it was still inside the declared `^3` range.
   - Change only the package: `npm install <pkg>@<range> --ignore-scripts --no-audit --no-fund`, then look at the lockfile diff (packages added, removed, changed) and at the new packages' `engines.node` against production's Node.
   - Measure it: OSV-Scanner on the lockfile before and after, and put both numbers on the issue and the PR.
4. Run the repo's `gates` entry point (`npm run gates`, `composer gates`, `make gates`) before pushing. On a **Windows** checkout with `core.autocrlf=true`, the "generated file is up to date" contract tests (tenants, backend) fail only because committed LF files become CRLF locally; convert those files to LF for the run (and restore them with `git checkout --` afterwards), or run the gates in WSL or CI, and say so in the PR.
5. A runtime driver or framework (database driver, HTTP stack, auth) needs a **real smoke test** that the unit tests cannot give: start the service against a dev database after the merge to `ai_native_setup` and exercise one request. Say in the PR that this is still to do if you could not do it.
6. If an alert cannot be fixed, dismiss it on GitHub with a reason and link the issue, so it does not come back as noise.
7. **The alert does not close until the fix reaches the default branch** (`main`/`master`): Dependabot evaluates that branch only, and fixes land on `ai_native_setup` first. Leave the issue open until the release PR has gone through `development` and `stagingdemo`, then confirm the alert closed.
8. In Linear text, do not write "alert #5": Linear turns `#5` into a link to an unrelated pull request. Write "alert number 5" or paste the alert URL.

## Cadence

- **Same day:** a pushed secret; a reachable critical.
- **Weekly:** one person reviews all open alerts across the seven repos and triages new ones into issues. `[DECISION PENDING]` who, and which weekday.
- **Monthly:** low-severity batch; check that the Actions secrets and the fine-grained token have not neared their expiry (`CONTRACT_CHECK_TOKEN` lasts one year).

## Baseline on 2026-10-14

Open Dependabot alerts when this page was written:

| Repo | Critical | High | Medium | Low |
|---|---|---|---|---|
| sanchiconnect-saas-tenants | 7 | 72 | 56 | 20 |
| sc-saas-backend | 14 | 111 | 108 | 22 |
| sc-saas-frontend | 12 | 137 | 95 | 22 |
| sc-saas-admin | 37 | 130 | 125 | 23 |
| sanchiconnect-saas-tenants-admin | 37 | 133 | 121 | 20 |
| ai-startups-analyzer, sc-saas-3rdparty-webservices | none reported (see below) | | | |

**Those last two are not clean.** Dependabot reports nothing for them, but an OSV-Scanner scan of their lockfiles on 2026-10-15 finds 213 advisories in 56 packages in `sc-saas-3rdparty-webservices/package-lock.json` and 50 advisories in 6 packages in `ai-startups-analyzer/api/requirements.txt`. The numbers above are therefore a floor. `[DECISION PENDING]` An org owner (Settings → Code security) should confirm that the dependency graph and Dependabot alerts are on for both repos; until then the weekly review for them has to use `osv-scanner scan source --lockfile <file>`.

That is about 107 critical alerts in the five repos that report them, so the same-day rule for criticals cannot be met for the existing backlog. `[DECISION PENDING]` Agree a burn-down plan (for example: triage every critical for reachability first, then upgrade the reachable ones repo by repo, starting with the backend and tenants) and treat only **new** criticals as same-day until the backlog is cleared.

## Open items before this page is final

- The three `[DECISION PENDING]` answers above.
- SAN-1598: triage the first week of Semgrep findings into Production Defects with the Security prefix, then decide when `code-scan` becomes a required check.
- SAN-1599: the first weekly Dependabot PRs appear once the files reach `main`/`master`; then confirm one is merged or declined within the week.
- Mirror this page to Linear (a document in the CI Pipeline and Gates project).
- Done-when: handle one real alert by following this page, and fix the gaps it shows.
