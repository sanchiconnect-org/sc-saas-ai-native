# SAN-1154 — Broadcast details: real send status, missing-SES-stats notice, auto-fetch for recent broadcasts

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1154
- **Repo:** sc-saas-admin · **Type:** Improvement (+ one display bug) · **Priority:** Medium · **Assignee:** Nirmal Singh · **Related:** SAN-1153

## Problem
On the sanchiconnect tenant, broadcast 223 (Jul 21 2026, 3,983 recipients) showed every recipient as
"In Progress". Yet every `ses_email_queue` row was `email_sent_status = sent`, with an SES `250 Ok <messageId>`.
- Row status was derived only from SES timestamps, which Request Stats fills in (one SES
  `getMessageInsights` call per row, sequentially). It never read `email_sent_status`.
- An SES "not found" answer (insights no longer held for a two-month-old message) was written as
  "Not found", then immediately overwritten by `setRowStatus()` back to "In Progress".
- Evidence that lookups had failed: after 392 processed rows, the rows' `modified_at` still equalled the
  send time. The success path always rewrites it; the error path doesn't.

## Change
- `modules/broadcast_messages/details.php`: selects `last_sent_at`; adds per-row `sentAt` and
  `checkedAt` epochs. `checkedAt` is 0 until a stats fetch has succeeded.
- `themes/default/html/broadcast_messages/details.php`:
  - Rows carry `data-db-status` / `data-sent-at` / `data-checked-at`.
  - Status falls back to the DB state: pending → "In Progress", sent → "Sent", failed → "Failed".
    SES detail (Delivered/Opened/Bounced) still wins.
  - Counters: "In Progress" now counts only queued rows. There's a new "Sent" box, and a "Failed" box
    that appears only when there are failures.
  - SES "not found" → "Sent · stats unavailable in SES" (no longer overwritten).
  - Automatic fetch on load, only for rows that are `sent`, 15 minutes to 30 days old, not opened or bounced,
    and not successfully checked in the last 6 h. It still runs one lookup at a time. Request Stats refreshes every row.
  - A run-in-progress guard: the button is an `<a>`, so `disabled` didn't stop overlapping runs.

## Verification
- `php -l` clean on both files; `node --check` clean on the extracted page script; no `//` comments.
- jsdom simulation of the real page script (jQuery, stubbed `$.ajax`) on 7 rows covering sent, old,
  pending, failed, recently checked, SES not found and opened. Auto-fetch hit only the 2 eligible rows.
  Labels and counters were correct, and a double-click on Request Stats started one run.
- Not yet tested against live SES. sc-saas-admin has no automated test framework.

## Known limits
- The 30-day window is an assumption about how long SES Virtual Deliverability Manager keeps message
  insights. Adjust `AUTO_FETCH_MAX_AGE_SEC` if the tooltip shows otherwise.
- On the first visit to a large, recent broadcast, the automatic fetch still makes one lookup per
  eligible row, but the 6-hour recheck rule prevents repeats. A backend cron would remove the need
  to keep the page open; that would be separate sc-saas-backend work.
- The "stats unavailable" state isn't persisted, so an old broadcast shows "Sent" until Request Stats is clicked.

## Commit
sc-saas-admin `caf66553` (pushed to `ai_native_setup` 2026-09-30)
