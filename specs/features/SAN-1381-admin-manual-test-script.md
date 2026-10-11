# SAN-1381 — Admin manual test script (T5.0 / SAN-1441)

`sc-saas-admin` has no automated test suite, so the admin side of the Notifications BRD v1.1 (FR-A1 to FR-A5, EX-10 basic) is verified by hand with this script. Every touched PHP file must also pass `php -l`.

Run it on a tenant whose backend already has the T2 schema (`admin_section_last_seen`, the ticket columns `ticket_category` / `acknowledged_at` / `acknowledged_by_id`, and `awaiting_user` in the `ticket_status` enum). Without that schema the admin treats the feature as off; see case 0.2.

## Sample data (W-08)

Seed the tenant DB so that the expected admin bell is **27**:

| Queue | Rows | Notes |
|---|---|---|
| Outreach | 5 | 3 `partner_broadcast_requests` with `status='pending'`, `target_scope='hub'`; 2 `program_promotions` with `approval_status='pending'` for this tenant's domain (main DB). Make 1 broadcast older than 48 h. |
| Ecosystem | 9 | 6 startups, 2 mentors, 1 investor with `approval_status='pending'`. |
| Engagements | 6 | 4 `meetings` + 2 mentor sessions created after the admin's last visit. |
| Tasks | 3 | 2 assigned to admin A (one with `due_date` yesterday) + 1 with an empty `assigned_to_ids` (team queue). All `task_status IN ('open','assigned')`, `status=1`. |
| Support | 4 | 3 `open` tickets (2 feedback, 1 grievance) + 1 more grievance `open`. Add 1 extra `awaiting_user` ticket — it must **not** count. |

Admins:

- **A** — super-admin (sees everything).
- **B** — role with the Tasks and Tickets menus only, no `can_broadcast_messages`, no `can_accept_reject_profiles`.
- **C** — role with none of these permissions or menus.
- **P** — a partner session (`$_SESSION["partner_id"]` set).

## 0. Gating

| # | Step | Expected |
|---|---|---|
| 0.1 | Flag `notification_centre_enabled` = 0 for the tenant. Log in as A. | No bell, no new sidebar badges, no Command centre menu. Every page looks exactly as before. |
| 0.2 | Flag = 1, but the tenant DB lacks `admin_section_last_seen`. | No PHP warning or error. Engagements shows no count. The other counters still work. |
| 0.3 | Flag = 1. Log in as P (partner). | No admin bell and no admin counters (partners have their own menus). |
| 0.4 | Flag = 1. Log in as C. | No bell badge, no sidebar badges. The Command centre shows its empty state ("No queues to show"). |

## 1. Bell and sidebar badges (T5.1, T5.3)

| # | Step | Expected |
|---|---|---|
| 1.1 | Log in as A. | The bell next to Quick Links shows **27**. Its dropdown lists Outreach 5, Ecosystem 9, Engagements 6, Tasks 3, Support 4. |
| 1.2 | Look at the sidebar. | Badges on the matching menus: outreach/broadcast red, Ecosystem red **9**, Engagements orange **6**, Tasks red **3**, Support red **4**. |
| 1.3 | Log in as B. | The bell shows **7** (tasks 3 + support 4). There are no outreach, ecosystem or engagement badges. |
| 1.4 | Set any counter above 99. | The badge shows "99+". Every badge has an `aria-label`. |
| 1.5 | Make every counter 0. | No badge is shown anywhere, and the bell has no number. |

## 2. Outreach (T5.4, FR-A1)

| # | Step | Expected |
|---|---|---|
| 2.1 | Open the outreach / broadcast approvals list. | Pending rows are sorted oldest first, with a "Waiting" column. The row older than 48 h shows **Overdue**. |
| 2.2 | Change `spa_settings.sla_outreach_decision_hours` to 1. | More rows show Overdue, with no deploy. |
| 2.3 | Approve one request. | The outreach count drops by 1 (bell 26). |
| 2.4 | Reject one request without a reason. | It is blocked: a reason is required. |
| 2.5 | Reject with a reason. | The count drops by 1. The requester gets the reason (SAN-392 `rejection_message`). An audit row is written (5.x). |
| 2.6 | Add a `program_promotions` row for a **different** domain. | The count does not change. |

## 3. Ecosystem (T5.5, FR-A2)

| # | Step | Expected |
|---|---|---|
| 3.1 | Click the Ecosystem badge. | The persona list opens with the "Pending review" filter applied. |
| 3.2 | Look at the persona tabs. | Startups 6, Mentors 2, Investors 1 (6 + 2 + 1 = 9). |
| 3.3 | Approve a startup. | The Startups tab shows 5 and the Ecosystem total shows 8. |
| 3.4 | Turn a persona's tenant flag off. | That persona's tab and count disappear. |
| 3.5 | Program office (auto-approved). | Shown in orange as "new since your last visit", not red. |

## 4. Engagements (T5.6, FR-A3, per admin)

| # | Step | Expected |
|---|---|---|
| 4.1 | As A, open the Engagements view for 2 s and leave. | The count is still 6. |
| 4.2 | Open it for 3 continuous seconds and leave. | The count shows 0 after the next page load. |
| 4.3 | Open it, switch to another browser tab after 2 s, come back for 2 s, then leave. | No visit is recorded, because the time wasn't continuous. The count is still 6. |
| 4.4 | As another super-admin, check Engagements. | Still 6. Counts are per admin. |
| 4.5 | Set `notif_engagement_types` = `meeting`. | Only the 4 meetings count. |
| 4.6 | POST to `notifications/visit` with an unknown section. | HTTP 400, no row written. |
| 4.7 | POST to `notifications/visit` with an expired session. | HTTP 401 JSON, no PHP warning. |
| 4.8 | POST without, or with a wrong, CSRF token. | HTTP 403, no row written. |

## 5. Tasks (T5.7, FR-A4)

| # | Step | Expected |
|---|---|---|
| 5.1 | Open the task list as A. | The overdue task is first and marked **Overdue**. A task with no due date never shows Overdue. |
| 5.2 | Look at the "Team queue" section. | The unassigned task appears with an "Assign to me" button. |
| 5.3 | Click "Assign to me". | The task moves to A's list. The count is unchanged (it is still open). |
| 5.4 | Complete a task. Then cancel another. | The count drops by 1 each time. |

## 6. Support (T5.8, FR-A5)

| # | Step | Expected |
|---|---|---|
| 6.1 | Open the tickets list. | Feedback and Grievance tabs, each with its own red count (2 and 2). A grey "Awaiting user" sub-count (1) is not added to red. The Support menu total is 4. |
| 6.2 | Look at the columns. | "Acknowledge by" (created + 24 h) and "Resolve by" (created + 7 d), flagged when near or past the SLA. |
| 6.3 | Acknowledge a grievance. | `acknowledged_at` / `acknowledged_by_id` are set. The Acknowledge-by flag clears. |
| 6.4 | Resolve a ticket. | The count drops by 1. |
| 6.5 | Reopen a resolved ticket. | It counts again. |

## 7. Command centre (T5.9, EX-10 basic)

| # | Step | Expected |
|---|---|---|
| 7.1 | Open the Command centre as A. | An SLA strip at the top ("N items past SLA") with a View link. One card per queue with count, oldest-item age and overdue count. |
| 7.2 | Click a card. | Its filtered queue opens. |
| 7.3 | Open it as B. | Only the Tasks and Support cards. |
| 7.4 | Open it as C. | The empty state. |

## 8. Audit log (T5.10, NFR-11)

| # | Step | Expected |
|---|---|---|
| 8.1 | After 2.3, 2.5, 3.3, 5.4 and 6.4, check the admin log. | One row per decision, with admin id, time, action, record and reason (where there is one). Actions that already logged before this change are not double-logged. |

## 9. Settings (T5.11)

| # | Step | Expected |
|---|---|---|
| 9.1 | On a tenant with none of the keys, load any admin page with the flag on. | Rows are created once: `notif_opportunity_counter_mode`=B, `sla_outreach_decision_hours`=48, `sla_grievance_ack_hours`=24, `sla_grievance_resolve_days`=7, `notif_engagement_types`=`meeting,mentor_session`. |
| 9.2 | Change one value in Settings, then reload. | The changed value is kept and never overwritten. |

## 10. Lint

`php -l` passes on every PHP file touched by T5.
