---
id: SAN-1474
title: "Notifications Phase 2 — EX-10 full: command centre SLA colouring and trends"
type: feature
status: done                    # approved 2026-10-08 (OQs resolved by Mahima); implemented 2026-10-08; browser check pending
linear: https://linear.app/sanchiconnect/issue/SAN-1474/notifications-p2-ex-10-full-command-centre-sla-colouring-and-trends
owner: Mahima Sharma
source: "BRD v1.1, EX-10 (W-08), Phase 2 — extends SAN-1450 (basic command centre)"
repos: [admin]
contracts:
  api: ["None"]
  flags: [notification_centre_enabled]   # EXISTING — the page is already gated
  events: ["spa_settings — new SLA keys per OQ-2 (seeded by notifCentreSettingDefaults)"]
tenant_scoped: true             # per-tenant $database; main-DB program_promotions filtered by domain (as today)
depends_on: [SAN-1381, SAN-1450]
created: 2026-10-08
---

# EX-10 full — command centre SLA colouring and trends

## Current state (checked 2026-10-08)
- `modules/command_centre.php` + `themes/default/html/command_centre/index.php` [EV] show an SLA-breach strip, then one card per permitted queue with its count, oldest-item age and overdue count. Everything comes from `getAdminNotificationCounters()` [EV `includes/notification_centre_functions.php:307`]. **There is no colour by SLA state and no trend.**
- **SLA settings exist only for outreach and support:**
  - `sla_outreach_decision_hours` 48
  - `sla_grievance_ack_hours` 24
  - `sla_grievance_resolve_days` 7

  Tasks are judged by their own `due_date` (overdue = due before today). Ecosystem and engagements have no SLA (`overdue` is always 0).
- **No history of counts is stored.** Trends must either come from the source tables or from a new snapshot table, which would need a scheduler that admin doesn't have.

## Proposed design
- **P-1 SLA colour per card [DDP OQ-1]:**
  - 🔴 red: overdue > 0.
  - 🟠 amber: oldest-item age ≥ 80 % of the queue's SLA (tasks: any task due today or tomorrow).
  - 🟢 green: otherwise.
  - Shown as a left border plus a text label ("Past SLA", "Near SLA", "On track"), so it isn't colour-only (NFR-08).
- **P-2 SLA for ecosystem and engagements [DDP OQ-2]:** add `sla_ecosystem_review_hours` (72) and `sla_engagement_decision_hours` (48). They are editable in Settings, and also feed `overdue` for these two queues, so the strip, bell and command centre agree.
- **P-3 Trend per card [DDP OQ-3]:** "+N / −N vs last week", with an arrow and a text label. It counts **items that entered the queue** in the last 7 days against the 7 days before, using each queue's own conditions and the admin's own scope (tasks and tickets are scoped per admin, as in the counters). It is computed only on the command centre page, through an opt-in argument to `getAdminNotificationCounters`, so other pages get no extra queries.
- **P-4 No snapshot table:** inflow is derived from `created_at`.

## Acceptance criteria
- [ ] A queue with an overdue item → red card, labelled "Past SLA".
- [ ] Oldest at 80 % or more of its SLA with nothing overdue → amber "Near SLA".
- [ ] Otherwise → green "On track".
- [ ] A queue with 5 new items this week and 2 last week shows "▲ +3 vs last week". Equal counts show "= same as last week".
- [ ] The trend respects permissions: a non-super admin's tickets and tasks trend counts only their own scope.
- [ ] Setting a new SLA key changes the colouring with no deploy.
- [ ] Flag off → page is unreachable (unchanged). Bell and other pages run no extra queries.

## Open questions

None. All three were resolved by Mahima on 2026-10-08, by accepting the recommended defaults: red/amber/green with a label; new 72 h / 48 h SLAs; new-this-week vs last-week trends.

## Implementation notes (2026-10-08)

Admin only, uncommitted on `ai_native_setup_mahima`.

- **`getAdminNotificationCounters()`:**
  - Ecosystem `overdue` now counts pending applicants older than `sla_ecosystem_review_hours`.
  - Engagements `overdue` now counts meetings awaiting moderation longer than `sla_engagement_decision_hours`.
  - Both were always 0 before. The SLA strip, bell and the SAN-1476 digest "at risk" section now include them.
- **New settings,** seeded by `notifCentreSettingDefaults`: `sla_ecosystem_review_hours` (72) and `sla_engagement_decision_hours` (48).
- **New `notifCentreCommandCentreEnrich()`,** called only by `modules/command_centre.php`. It returns `sla_state` (past / near / ok) and `trend` (this_week / last_week inflow) per queue. Tasks and support are scoped per admin, as in the counters. Outreach includes `program_promotions` (main DB, domain-filtered) when promotions are on.
- **Template:**
  - Each card has a 4 px left border (#b91c1c / #b45309 / #15803d) and a text label: "Past SLA", "Near SLA" or "On track". The colours are 6.47 / 5.02 / 5.02:1 against white, so they aren't the only signal.
  - A trend line under each card: "N new this week · ▲ +X vs last week".
- **Verification:**
  - `php -l` is clean on all three files.
  - A real-MySQL harness ran the real `notification_centre_functions.php` with the real Medoo on the local test DB. 9/9 checks pass:
    - outreach past and its trend (3 / 1)
    - ecosystem near at 60 h of a 72 h SLA, with overdue 0
    - engagements overdue 1 at 49 h of 48 h, so past
    - tasks near (due tomorrow), with the trend in last week
  - Not run: a browser check.
