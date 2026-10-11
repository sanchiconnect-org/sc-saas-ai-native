# SAN-1381 — BRD §4 baseline queries (for T8.1 / SAN-1465)

These are read-only queries for the 30-day baseline that BRD §4 asks for *before* client tenants get `notification_centre_enabled`. Run them on each tenant DB (one backend deployment = one tenant DB). Paste the results into the SAN-1381 spec under "Baselines".

- **Window:** the last 30 days before enablement. Every query uses `@from` / `@to`.
- **Time zone:** all timestamps are stored in UTC. Shift by `+ INTERVAL 330 MINUTE` if you need IST day boundaries.
- **Read-only:** every query is a SELECT. Run them on a replica if you have one.

```sql
SET @to   = UTC_TIMESTAMP();
SET @from = @to - INTERVAL 30 DAY;
```

## 1. Weekly active share; median days between logins

`users.last_logged_in` is overwritten on every login, and `users_login_session` is only filled when `single_session_login_enabled` is on. **There is no login history to query backwards.** Take a daily snapshot of the query below for the 30 days instead, for example with a scheduled job or by hand. The weekly active share is the average of the 30 snapshots.

```sql
-- Daily snapshot: share of active accounts that logged in during the last 7 days.
SELECT DATE(@to) AS snapshot_day,
       SUM(last_logged_in >= @to - INTERVAL 7 DAY) AS weekly_active,
       COUNT(*)                                     AS accounts,
       ROUND(100 * SUM(last_logged_in >= @to - INTERVAL 7 DAY) / COUNT(*), 1) AS weekly_active_pct
  FROM users
 WHERE deleted_at IS NULL AND status = 1;

-- Median gap between a user's last two logins, in days (users with both values).
SELECT ROUND(AVG(gap), 1) AS median_gap_days FROM (
  SELECT gap, ROW_NUMBER() OVER (ORDER BY gap) AS rn, COUNT(*) OVER () AS n FROM (
    SELECT TIMESTAMPDIFF(HOUR, previous_logged_in, last_logged_in) / 24 AS gap
      FROM users
     WHERE deleted_at IS NULL AND previous_logged_in IS NOT NULL AND last_logged_in >= @from
  ) g
) r WHERE rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2));
```

## 2. Median time to accept or decline a connection (target: under 3 days)

```sql
-- accepted_at is set on accept. modified_at is the best available signal for a reject.
SELECT ROUND(AVG(days), 2) AS median_days_to_decide, MAX(n) AS decided FROM (
  SELECT days, ROW_NUMBER() OVER (ORDER BY days) AS rn, COUNT(*) OVER () AS n FROM (
    SELECT TIMESTAMPDIFF(MINUTE, created_at, COALESCE(accepted_at, modified_at)) / 1440 AS days
      FROM connections
     WHERE parent_id IS NULL AND deleted_at IS NULL
       AND connection_status IN ('accepted', 'rejected')
       AND COALESCE(accepted_at, modified_at) BETWEEN @from AND @to
  ) d
) r WHERE rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2));
```

## 3. Applications per live challenge or program (target: +20 %)

```sql
-- Programs (Calls for Applications): submissions in the window ÷ programs open in the window.
SELECT COUNT(DISTINCT fs.id) / NULLIF(COUNT(DISTINCT p.id), 0) AS applications_per_live_program
  FROM application_programs p
  LEFT JOIN forms_submissions fs
         ON fs.form_id = p.form_id AND fs.deleted_at IS NULL AND fs.created_at BETWEEN @from AND @to
 WHERE p.deleted_at IS NULL AND p.status = 1 AND p.test_mode_enabled = 0
   AND (p.application_closed_date IS NULL OR p.application_closed_date >= @from);

-- Challenges: participants in the window ÷ challenges live in the window.
SELECT COUNT(DISTINCT cp.id) / NULLIF(COUNT(DISTINCT c.id), 0) AS applications_per_live_challenge
  FROM challenges c
  LEFT JOIN challenge_participants cp
         ON cp.challenge_id = c.id AND cp.deleted_at IS NULL AND cp.created_at BETWEEN @from AND @to
 WHERE c.deleted_at IS NULL AND c.status = 1 AND c.approval_status = 'approved'
   AND (c.dead_line IS NULL OR c.dead_line >= DATE(@from));
```

## 4. Wall opens; posts and comments per active user (target: +30 % wall opens)

**Wall opens are not tracked before release.** `notification_section_last_seen` only exists with the flag on, and it keeps the latest visit per user, not a count. For the baseline, use web analytics (Mixpanel / GA page views of the wall route) for the 30 days. Posts and comments come from the DB:

```sql
SELECT (SELECT COUNT(*) FROM comm_wall_posts
         WHERE deleted_at IS NULL AND created_at BETWEEN @from AND @to) AS posts,
       (SELECT COUNT(*) FROM comm_wall_post_comments
         WHERE deleted_at IS NULL AND created_at BETWEEN @from AND @to) AS comments,
       (SELECT COUNT(*) FROM users
         WHERE deleted_at IS NULL AND last_logged_in BETWEEN @from AND @to) AS active_users;
-- per active user = (posts + comments) / active_users
```

## 5. Outreach decided within 48 h; grievances within SLA (target: 90 %)

```sql
-- Median hours from a hub broadcast request to its decision.
SELECT ROUND(AVG(h), 1) AS median_hours_to_decision FROM (
  SELECT h, ROW_NUMBER() OVER (ORDER BY h) AS rn, COUNT(*) OVER () AS n FROM (
    SELECT TIMESTAMPDIFF(MINUTE, created_at, reviewed_on) / 60 AS h
      FROM partner_broadcast_requests
     WHERE target_scope = 'hub' AND reviewed_on BETWEEN @from AND @to AND deleted_at IS NULL
  ) d
) r WHERE rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2));

-- Grievances closed in the window, and how many were closed within the resolve SLA (7 d default).
SELECT COUNT(*) AS grievances_closed,
       SUM(closed_at <= created_at + INTERVAL 7 DAY) AS within_resolve_sla,
       ROUND(100 * SUM(closed_at <= created_at + INTERVAL 7 DAY) / COUNT(*), 1) AS pct_within_sla
  FROM tickets
 WHERE ticket_category = 'grievance' AND closed_at BETWEEN @from AND @to AND deleted_at IS NULL;
```

Program promotions (`program_promotions`) live in the tenants (main) DB. Run the same median query there, on `approval_status` changes per domain, if they should count toward outreach.

## 6. Badge-to-list mismatches (target: zero)

There is no production baseline, because the badges don't exist before release. Evidence comes from `sc-saas-backend/src/modules/notifications/badge-equals-list.integration.spec.ts` (12/12 on 2026-10-08). After release, re-check per tenant by comparing `GET notifications/counters` with the list endpoints.
