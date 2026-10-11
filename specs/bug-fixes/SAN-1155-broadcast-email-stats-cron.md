# SAN-1155 — Backend cron: collect SES broadcast email stats automatically

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1155
- **Repo:** sc-saas-backend · **Type:** Improvement · **Priority:** High · **Assignee:** Nirmal Singh · **Related:** SAN-1154, SAN-1153

## Problem
Broadcast delivery/open/bounce stats were only saved when an admin clicked Request Stats on
`broadcast_messages/details` while SES still held the message insights. Once SES dropped them, the stats
were lost for good. Observed: a fetch at 12 days worked (sanchiconnect broadcast 233); fetches at ~71 days
(broadcast 223) and ~14 months (SINE broadcast 24) failed.

## Change
- `src/modules/cron/sync-broadcast-email-stats.service.ts` (new), `SYNC_BROADCAST_EMAIL_STATS` = `syncBroadcastEmailStats`:
  - **Rows:** `email_sent_status = sent`, type broadcast/partner_broadcast, `broadcast_message_id` set,
    sent 15 minutes to 30 days ago, not opened or bounced. They qualify if never checked (`modified_at` within
    60 s of `last_sent_at`) or last checked more than 20 h ago. Ordered by `modified_at` ASC, 300 per run,
    200 ms between calls.
  - **Lookup:** SES v2 `GetMessageInsights`, region `ses_region`, then `SES_STATS_REGION`, then `AMAZON_REGION`.
    Writes the earliest SEND/DELIVERY/OPEN/BOUNCE timestamps and the bounce diagnostic, and only overwrites
    fields with non-null values. Every check touches `modified_at`.
  - **On bounce:** `users.promotional_emails_enabled = 0` (same as admin). The admin also sets
    `all_emails_enabled = 1`; that isn't mirrored because it looks unintended.
  - **Errors:** NotFound only marks the row as checked. Throttling or credential errors stop the run.
    Other errors are logged per row. An end-of-run summary logs `candidates/updated/notFound/noMessageId/errors/stoppedBy`.
- Registered in `CronJobName`, the default seed (hourly at :20, seeded **active**, the only default job
  besides the queue sender that is, so stats are never lost waiting for a manual switch-on), `cron.module.ts` providers, and the `cron.service.ts` scheduler switch.
- Config: optional `SES_STATS_ACCESS_KEY_ID` / `SES_STATS_SECRET_ACCESS_KEY` / `SES_STATS_REGION`
  (Joi optional), with getters falling back to `AMAZON_*`.
- Dependency: `@aws-sdk/client-sesv2` **exactly 3.600.0**. Versions ≥ 3.723 require Node 18, and production runs Node 16.
  Lockfile compared package by package against HEAD: 0 changed, 0 removed, 144 added (all in the new SDK's tree).
  The existing `@aws-sdk/*` 3.131 packages stay at top level. The large text diff is npm rewriting the v2
  lockfile's legacy `dependencies` section. No new Node 18 requirement (`pdfmake` 0.2.20 was already there).

## Verification
- `tsc --noEmit` clean; eslint 0 errors on touched files (Prettier applied to the new file and the config service).
- Smoke run of the real service with mocked SES + DB: found → timestamps saved (earliest per type);
  not found → marked checked only; no message ID → no SES call; bounce → timestamp, message and
  promotional opt-out saved; throttled → run stopped before later rows; no credentials → skipped.
- TypeORM-generated SQL checked (property → column mapping, `DATE_ADD` "never checked" rule, soft-delete filter).
- Not run against live SES/MySQL. No committed Jest test yet (proposed, waiting for go-ahead).

## Rollout
1. Deploy the backend. On boot, the job row is auto-inserted into `cron_jobs` as **active** and starts running,
   with no manual step. To turn it off for a tenant: `UPDATE cron_jobs SET active = 0 WHERE name = 'syncBroadcastEmailStats';`,
   then restart the backend.
2. Check the logs after the next :20 run. `updated > 0` means it works. A `stopped early -- AccessDeniedException`
   log, or everything coming back `notFound` for rows only a few hours old, means the keys belong to another
   account or region. In that case set `SES_STATS_*` to the same platform keys the admin uses (`spa_amazon_*`).

## Known limits
- The 30-day window is an assumption about how long SES keeps insights (see SAN-1154).
- There's no index on `last_sent_at`/`modified_at`, so the hourly select may scan `ses_email_queue`. Watch it on
  the largest tenants; add a composite index if needed.

## Commit
sc-saas-backend `76b0a4e5` + `d506fa98` (seeded active) (pushed to `ai_native_setup` 2026-09-30)
