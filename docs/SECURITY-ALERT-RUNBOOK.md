# Security-alert runbook

What to do when a security tool raises something. Covers the seven product repos. Part of the CI Pipeline and Gates project (P-SAN-75, SAN-1601). Facts below were checked against GitHub on 2026-10-14; update this page when a tool goes live.

**Status: draft.** Items marked `[DECISION PENDING]` need an answer from the dev lead before this page is final. Do not invent the answer.

## What is live, and what is not

| Source | State | Where you see it |
|---|---|---|
| Secret scan (gitleaks) | **Live** on every push and PR (`secret-scan.yml`, rules in `.gitleaks.toml`). Scans only new commits. Reports only; it blocks a merge once SAN-1583 makes it a required check. | A red `secret-scan` run; Slack alert (`ci-alerts.yml`) when it fails on `main`/`master`, `stagingdemo` or `development`. |
| GitHub secret scanning and push protection | **Not available.** The `sanchiconnect-org` organization is on the free plan and has no GitHub Secret Protection (the API returns 404). The gitleaks workflow is the substitute, and it cannot stop a push: a secret is detected after it is already on GitHub. | n/a |
| Dependabot alerts | **Live** in all seven repos. | Repo → Security → Dependabot, or `gh api repos/sanchiconnect-org/<repo>/dependabot/alerts?state=open`. Nothing notifies the team yet. |
| Dependabot version updates, dependency review on PRs | **Not live** (SAN-1599). | n/a |
| Code scanning | **CodeQL is not available:** it needs GitHub Code Security, a paid add-on that the `sanchiconnect-org` free plan does not include. **Semgrep** (open-source rules) runs instead, as `code-scan.yml` (SAN-1598). Advisory: it reports and never fails a build. | The `code-scan` run: a findings summary on the run page and a `semgrep-findings` artifact. |
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
4. Run the repo's `gates` entry point (`npm run gates`, `composer gates`, `make gates`) before pushing.
5. If an alert cannot be fixed, dismiss it on GitHub with a reason and link the issue, so it does not come back as noise.

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
| ai-startups-analyzer, sc-saas-3rdparty-webservices | none reported | | | |

That is about 107 critical alerts today, so the same-day rule for criticals cannot be met for the existing backlog. `[DECISION PENDING]` Agree a burn-down plan (for example: triage every critical for reachability first, then upgrade the reachable ones repo by repo, starting with the backend and tenants) and treat only **new** criticals as same-day until the backlog is cleared.

## Open items before this page is final

- The three `[DECISION PENDING]` answers above.
- SAN-1598: triage the first week of Semgrep findings into Production Defects with the Security prefix, then decide when `code-scan` becomes a required check.
- SAN-1599: when Dependabot version updates and dependency review go live, update the table at the top.
- Mirror this page to Linear (a document in the CI Pipeline and Gates project).
- Done-when: handle one real alert by following this page, and fix the gaps it shows.
