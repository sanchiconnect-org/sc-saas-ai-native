# Linear breakdown — Notifications and an Action-Driven Dashboard

**Status: CREATED IN LINEAR on 2026-10-01.**

| Item | Linear issues |
|---|---|
| Parents T0–T8 | SAN-1381 – SAN-1389 |
| Phase 1 sub-issues (79) | SAN-1390 – SAN-1468, in the order listed below |
| Phase 2/3 placeholders (19, Backlog, no milestone) | SAN-1469 – SAN-1487 |

All issues are assigned to Vishali. Parent dependency chain: T0 → T1 → T2 → {T3 → T4, T5} → T6 → T7 → T8.

## Where this lives in Linear

| Field | Value |
|---|---|
| Project | **Enhancement** (P-SAN-48, team Sanchiconnect / SAN) |
| Milestone | **Notifications and an Action-Driven Dashboard** — new; to be created |
| Source BRD | *Notifications and an Action-Driven Dashboard for SanchiAPP* v1.1, 1 Oct 2026 |
| Governing spec | `specs/features/SAN-1381-notifications-action-driven-dashboard.spec.md` — renamed to the anchoring SAN-xxx on creation |
| Assignee | **To be confirmed** — one developer for the whole milestone, per the workspace assignee convention |

## Conventions

- **Repo labels:** every issue and sub-issue carries exactly one `Repo:` label. Workspace-only items have no repo label.
- **Priority:** uses Linear's native Priority field.
- **Workflow:** issues move Todo → In Progress → In Review → Done as the work actually happens.
- **References:** `FR-` / `EX-` / `NFR-` / `D` = BRD ids. `W-` = BRD wireframes. `OQ-` = open questions in the governing spec.
- **Blocked:** a sub-issue marked ⛔ is blocked until the named OQ is answered. The BRD does not settle those points against the current code.
- **Scope:** this milestone delivers **BRD Phase 1** (BRD §14). Phase 2 and 3 items appear in §P2/P3 only as backlog placeholders, so every BRD requirement is traceable. They are not built here.

## How the 10-step process maps to the issues

| Step | Where it happens |
|---|---|
| 1. Orient · 2. `/from-linear` · 3. spec · 4. resolve open design questions | **T0** |
| 5. Contract checks (`/trace-flag`, `/audit-contract`, `/check-isolation`) | **T6** |
| 6. Tests first | The first sub-issue of each dev issue (`.0`), plus **T7** |
| 7. Work directly on the branch | Every dev issue — see the branch note in T8.4 |
| 8. `/spec-implement` | **T1–T5** |
| 9. Verify; update module specs, Gap Register, Linear | **T7**, **T8.3** |
| 10. Commit and push, close | **T8.4** |

---

## T0 — Spec sign-off and design decisions

- **Repo label:** none (workspace)
- **Priority:** Urgent
- **Covers:** steps 1–4
- **Blocks:** everything below

| ID | Sub-issue | BRD ref | Done when | Depends |
|---|---|---|---|---|
| T0.1 | Get BRD v1.1 signed off. Rename the spec to its SAN id and link it to the milestone | §18 | Sign-off recorded; spec `linear:` field filled | — |
| T0.2 | Decide the community-wall scope. "Joined communities" (D2) has no backing model in the code | FR-U2, D2 | OQ-1 answered in the spec | T0.1 |
| T0.3 | Decide which outreach queue(s) count. Decide whether Submitted, Under review and Returned need new states | FR-A1 | OQ-2 answered | T0.1 |
| T0.4 | Decide the persona list (Academia? Incubators vs Partners) and how a tenant's auto-approval is detected | FR-A2, D4 | OQ-3 answered | T0.1 |
| T0.5 | Decide the feedback/grievance split, the "awaiting user" status, and an acknowledge action for the SLA | FR-A5, D6, D8 | OQ-4 answered | T0.1 |
| T0.6 | Define the task team queue and the meaning of "In progress" | FR-A4, D5 | OQ-5 answered | T0.1 |
| T0.7 | Define eligibility for challenges, programs and events, and which program table(s) feed the counts | FR-U3 | OQ-6 and OQ-7 answered (dev lead) | T0.1 |
| T0.8 | Choose the target dashboard(s) for the catch-up card, and where the admin menu badges go | EX-01, EX-08, W-08 | OQ-8 and OQ-10 answered | T0.1 |
| T0.9 | Decide whether socket-gateway auth is fixed here or before Phase 2 | NFR-05 | OQ-9 answered (dev lead) | T0.1 |
| T0.10 | Move the spec to `approved` | — | Open-questions list is empty | T0.2–T0.9 |

---

## T1 — Tenants: feature flag and per-tenant settings

- **Repo label:** `Repo: Tenants`
- **Priority:** High
- **Depends on:** T0.10

| ID | Sub-issue | BRD ref | Acceptance | Edge cases |
|---|---|---|---|---|
| T1.0 | Tests first: migration up/down; flag present in `verify_tenant` | — | Tests fail before T1.1–T1.3 and pass after | — |
| T1.1 | Add the boolean column `notification_centre_enabled` to `TenantUsersEntity`, default false, with a migration | §5 (per-tenant config) | Column exists; existing tenants read `false` | Existing rows backfill to false, not NULL |
| T1.2 | Expose the flag in the `verify_tenant` / `tenant-settings` features payload | §5 | Payload carries the key; the shape change is additive only | Old frontends ignore the unknown key |
| T1.3 | Seed `spa_settings` defaults | D1, D7, D8 | New tenants get the defaults below; existing tenants backfilled once | Never overwrite a value the tenant has already changed |

Defaults for T1.3:
- `notif_opportunity_counter_mode` = B
- `sla_outreach_decision_hours` = 48
- `sla_grievance_ack_hours` = 24
- `sla_grievance_resolve_days` = 7
- `notif_engagement_types` = meeting,mentor_session

---

## T2 — Backend: data model

- **Repo label:** `Repo: Backend`
- **Priority:** High
- **Depends on:** T0.10, T1.1

| ID | Sub-issue | BRD ref | Acceptance | Edge cases |
|---|---|---|---|---|
| T2.0 | Tests first: entity and migration tests for T2.1–T2.7 | — | Run red, then green | — |
| T2.1 | Add `Feature.NOTIFICATION_CENTRE_ENABLED` to the `Feature` enum | §5 | Enum value matches the tenants column name exactly | — |
| T2.2 | Add a `notification_section_last_seen` table (user, section, last_seen_at; unique user+section) | §7.1, §13 | Upsert keeps one row per user per section | Concurrent upserts from two devices: keep the latest time |
| T2.3 | Add an `admin_section_last_seen` table (admin_user_id, section, last_seen_at) | FR-A2, FR-A3, §13 | Same as T2.2, per admin | — |
| T2.4 | Add a `notification_item_views` table (user, item_type, item_id, first_viewed_at; unique) | FR-U3 mode B, §13 | First view is recorded; later views don't change it | Item deleted after viewing: the row is harmless |
| T2.5 | Extend `notifications`: add `read_at`, `actioned_at`, `category`, `source_type`, `source_id`. Add `notification_reads` for per-user read state on `send_to=all` rows. Fix the unbracketed `orWhere` | FR-U5, §13 | Existing rows still list; one user reading a broadcast no longer marks it read for others | Keep `has_read` written for back-compat |
| T2.6 | Add `job_applications.viewed_at` and `viewed_by_user_id` | FR-U4, §13 | Nullable; existing applications start as unviewed | Decide whether historic applications count as New — see T3.4 |
| T2.7 | Add `users.previous_logged_in`; at login, copy `last_logged_in` into it before overwriting | EX-01 | After a 2nd login, `previous_logged_in` = the 1st login time | First-ever login: NULL, so fall back to `created_at` |
| T2.8 ⛔ OQ-4 | Ticket schema for the feedback/grievance split, "awaiting user" and `acknowledged_at` — only if OQ-4 chooses new columns | FR-A5, D6, D8 | Per the OQ-4 decision | Existing open tickets need a default category |
| T2.9 ⛔ OQ-2/OQ-5 | Outreach and task status additions — only if OQ-2 or OQ-5 requires them | FR-A1, FR-A4 | Per the decision | — |

---

## T3 — Backend: counters and notification API

- **Repo label:** `Repo: Backend`
- **Priority:** High
- **Depends on:** T2

| ID | Sub-issue | BRD ref | Acceptance | Edge cases |
|---|---|---|---|---|
| T3.0 | Tests first: one Jest suite per counter, using the BRD's acceptance numbers | FR-U1–U4 | Suites written before the counters | — |
| T3.1 | Connections counter: pending incoming requests | FR-U1, D3 | 3 pending → 3; after accepting one → 2; sent requests never count | Withdrawn (soft-deleted) excluded; deactivated sender excluded; `pending_moderation` not counted; no expiry |
| T3.2 ⛔ OQ-1 | Community wall counter: visible posts newer than the user's last visit | FR-U2, D2 | 5 new posts → 5; own posts excluded | Hidden or deleted after posting drops out; first login uses the registration time; posts limited to other user types are excluded |
| T3.3 ⛔ OQ-6/7 | Opportunities counter in mode A and B, per category, plus `closing_soon[]` within 72 h | FR-U3, D1 | Mode B: 4 live − 1 opened − 1 applied = 2; category counts sum to the tab | Drops out at close time in tenant timezone (IST); mode A is not in the bell; ineligible items never count |
| T3.4 | Jobs counter: unopened applications on any team member's jobs, broken down per job | FR-U4 | Jobs with 3 and 2 unopened → total 5, per-job 3 and 2 | Closed job still counts; `in-moderation` excluded; shared across the team |
| T3.5 | `GET notifications/counters`: one batched response with every section, the bell total and the catch-up summary | FR-U5, §7.2, EX-01, EX-08, NFR-12 | Bell = red + orange counts, live counts excluded; catch-up is null when everything is 0 | Flag off → 403 (guard applied per method, not per class) |
| T3.6 | `POST notifications/sections/{section}/visit` | §7.1 | `last_seen_at` set to the `left_at` the client sends | Reject unknown sections; reject a `left_at` in the future |
| T3.7 | `POST notifications/item-views` | FR-U3 mode B | Item counts as opened; a repeat call is harmless | Unknown item → 404 |
| T3.8 | `PATCH notifications/{uuid}/read`; narrow `mark-all-read` to "new" items; list response returns `read_at`, `category` and a Today/Earlier group | FR-U5 | Mark-all leaves action-required items untouched | Another user's notification uuid → 404 |
| T3.9 | `PATCH jobs/applications/{uuid}/viewed`; also set it automatically when the poster opens the application | FR-U4 | Any team member opening it clears it once for the whole team | Non-team user → 403; status changes to shortlisted or rejected also clear it |
| T3.10 | Emit `fetch-count` on every change that moves a counter (job applications; admin actions that hit user counters) | NFR-02, §7.2 | Counts update within 60 s; the actor's own view updates immediately | No per-user fan-out for wall posts (the poll covers them) |
| T3.11 | `notifications_purge` cron: remove notifications older than 90 days. Seed the job as inactive | FR-U5 (90-day history) | Runs via `cron_jobs`; off by default | Respects `cron_enabled` |
| T3.12 | Performance: indexes on the counter columns; measure p95 on the largest tenant | NFR-01, NFR-04 | p95 ≤ 300 ms; dashboard load +≤10 % | If over budget, add a short per-user cache cleared on `fetch-count` |

---

## T4 — Frontend: user notifications and dashboard

- **Repo label:** `Repo: Frontend`
- **Priority:** High
- **Depends on:** T3, and T1.2 for the flag

| ID | Sub-issue | BRD ref / W | Acceptance | Edge cases |
|---|---|---|---|---|
| T4.0 | Tests first: Karma specs for T4.3 and T4.4 | — | Written before the code | — |
| T4.1 | Add the flag to `IFeatures`; add new `notifications.service` methods; add an NgRx `counters` slice | §5 | Flag off → app behaves as today | — |
| T4.2 | Polling that pauses while the tab is hidden and refreshes when it becomes visible; socket `fetch-count` triggers a refresh | §7.2, NFR-02 | ≤60 s freshness; no requests while hidden | Logout clears the interval |
| T4.3 | `QualifyingVisitService`: 3 continuous seconds in the foreground; pauses on tab switch or app background; sends `left_at` on route leave, with a `sendBeacon` fallback | §7.1, NFR-09 | 2 s → no visit; 3 s → visit; a tab switch resets the continuous count | Tab closed mid-visit (beacon); multiple tabs open |
| T4.4 | Generic nav badge: red / orange / outlined; hidden at 0; "99+" cap; `aria-label`; opens the list pre-filtered | §7.2, NFR-08, W-01 | Same badge component used on all four menus | Replaces the hard-coded badges keyed by menu id; `featureKey` gating still applies |
| T4.5 | Header bell and panel: All / Needs action tabs; Today / Earlier groups; each item deep-links to its record | FR-U5, W-02 | Bell = sum from T3.5; reaches 0 | Hidden for account types the header already hides badges for |
| T4.6 | Accept / Decline a connection request inside the panel | FR-U5, W-02 ① | Red counts update without a page refresh | Request already withdrawn → friendly error |
| T4.7 | Mark all as read, plus the footer note "items that need action stay"; `/notifications` stops auto-marking everything read when the flag is on | FR-U5, W-02 ③④ | Only orange items clear | — |
| T4.8 | Connections → Received tab: pending-only landing; "Waiting N days" label | FR-U1, D3, W-03 | Opening the tab doesn't change the count | — |
| T4.9 | Community wall: "New since your last visit" divider above the oldest unseen post; visit timer hook | FR-U2, W-04 | Badge clears after 3 s; divider placed correctly | No unseen posts → no divider |
| T4.10 | Challenges, programs and events: per-category counts; orange unseen dot; red "Closes in N days" chip; "Applied" tag; 3 s detail-page view recorded | FR-U3, W-05 | Categories sum to the menu badge; opened card loses its dot | Mode A shows the outlined badge, not in the bell |
| T4.11 | Jobs → My job posts: red count per job; New / Viewed status; opening an application marks it viewed | FR-U4, W-06 | Per-job counts sum to the Jobs badge | Closed jobs still show their unopened count |
| T4.12 ⛔ OQ-8 | Dashboard catch-up card: "Since {day}: …", each phrase links to its filtered list, dismissible | EX-01, W-01 ③ | Shown only when something changed | Dismissal lasts until the next login |
| T4.13 ⛔ OQ-8 | Empty state when every counter is 0: "You're all caught up" plus one suggested action | EX-08, W-01 ⑤ | Appears only at all-zero | — |

---

## T5 — Admin: counters, bell, command centre

- **Repo label:** `Repo: Admin`
- **Priority:** High
- **Depends on:** T2 (tables must exist first), T1.3

| ID | Sub-issue | BRD ref / W | Acceptance | Edge cases |
|---|---|---|---|---|
| T5.0 | Tests first: a manual test script for W-08 to W-12; `php -l` on every touched file | — | Script written up front | — |
| T5.1 | Flag constant plus `getAdminNotificationCounters()`, each counter gated on the admin's permission | NFR-06, D5 | Admin without the right sees neither the badge nor the card | Super-admin and dev roles see everything; partner sessions excluded |
| T5.2 | Admin visit endpoint (session + CSRF) plus a 3 s JS timer writing `admin_section_last_seen` | §7.1, FR-A3 | Per-admin "new" counts clear after 3 s | Two admins: independent counts |
| T5.3 | Admin bell next to Quick Links; sidebar badges on the matching menus | FR-A1–A5, W-08 | Bell = sum of the admin counters | Menus differ per tenant (OQ-10) |
| T5.4 ⛔ OQ-2 | Outreach queue: oldest first, waiting time, Overdue past the SLA; reject requires a reason that is sent to the requester | FR-A1, D8, W-09 | Approve, reject or return each reduce the count by 1 | Main-DB `program_promotions` must be filtered to this tenant's domain |
| T5.5 ⛔ OQ-3 | Ecosystem persona tabs with counts; badge lands on the "Pending review" filter | FR-A2, D4, W-10 | 6 + 2 + 1 = 9; approving one → 8 | Disabled personas hidden; auto-approve tenants use orange "new since last visit" |
| T5.6 | Engagements: orange count per admin of meetings and mentor sessions created since the last visit | FR-A3, D7, W-11 | Only types in `notif_engagement_types` count | — |
| T5.7 ⛔ OQ-5 | Tasks: overdue first; team-queue "Assign to me" | FR-A4, D5, W-11 | Complete or cancel → count −1 | Task with no due date never shows Overdue |
| T5.8 ⛔ OQ-4 | Support: Feedback / Grievance tabs; grey "awaiting user" sub-count; Acknowledge-by and Resolve-by columns, flagged when near or past SLA | FR-A5, D6, D8, W-12 | Menu = feedback + grievance; grey count excluded from red | Reopened ticket counts again |
| T5.9 | Command centre page: SLA-breach strip, then queue cards with count + oldest age; registered via a `cli/` menu script | EX-10 basic, W-08 ①② | Each card opens its filtered queue | Admin with zero permitted queues sees an empty state |
| T5.10 | Audit log for every approve / reject / resolve that clears a counter: who, when, reason | NFR-11 | Log row per decision | Reuse existing logging where it already exists — check first |

---

## T6 — Integration and contract gates

- **Covers:** step 5
- **Repo label:** per sub-issue — each gate is labelled with the repo that owns the contract
- **Depends on:** T1–T5 code complete

| ID | Sub-issue | Label | Acceptance |
|---|---|---|---|
| T6.1 | Run `/trace-flag notification_centre_enabled` | Repo: Tenants | Present in tenants, backend, frontend and admin. Confirms whether tenants-admin needs anything. No orphans |
| T6.2 | Run `/audit-contract` on the new and changed notification and job routes against frontend services and admin cURL calls | Repo: Backend | No drift; `GET notifications/count` unchanged |
| T6.3 | Run `/check-isolation` on the backend counter queries | Repo: Backend | No cross-tenant reads (NFR-05) |
| T6.4 | Run `/check-isolation` on the admin counter SQL, including the main-DB `program_promotions` domain filter | Repo: Admin | Every main-DB query is domain-filtered |
| T6.5 | Cross-repo smoke test: flag off → no change anywhere; flag on for one tenant → live badge updates; a second tenant stays independent | Repo: Frontend | All three scenarios pass |
| T6.6 | Run `/cross-repo-review` before pushing | Repo: Backend | No invariant violations |

---

## T7 — QA

- **Covers:** steps 6 and 9
- **Repo label:** per sub-issue
- **Depends on:** T6

| ID | Sub-issue | BRD ref | Label |
|---|---|---|---|
| T7.1 | Test cases from every user-side acceptance criterion (FR-U1–U5, EX-01, EX-08), using the W-01 sample data where the bell = 21 | §8, App. A | Repo: Frontend |
| T7.2 | Test cases from every admin acceptance criterion (FR-A1–A5, EX-10), using the W-08 sample data where the admin bell = 27 | §9, App. A | Repo: Admin |
| T7.3 | Automated test that each badge equals the number of rows in the list it opens | NFR-03, §15 | Repo: Backend |
| T7.4 | Accessibility check: screen-reader labels, WCAG 2.1 AA contrast, colour never the only signal | NFR-08 | Repo: Frontend |
| T7.5 | Devices: desktop, mobile web and PWA; 3-second rule when the app is backgrounded | NFR-09 | Repo: Frontend |
| T7.6 | Time zone: items close at IST close time; data stored in UTC | NFR-07 | Repo: Backend |
| T7.7 | Performance: p95 counter latency and dashboard-load overhead | NFR-01 | Repo: Backend |

---

## T8 — Release and close

- **Covers:** steps 9 and 10
- **Repo label:** none (workspace)
- **Depends on:** T7

| ID | Sub-issue | BRD ref | Acceptance |
|---|---|---|---|
| T8.1 | Capture 30-day baselines for the BRD §4 metrics **before** enabling the flag for client tenants | §4 | Baseline numbers recorded in the spec |
| T8.2 | Deploy in order: tenants → backend → frontend → admin; run the admin menu script; enable the flag on one internal tenant | Spec §Rollout | Smoke test passes on the internal tenant |
| T8.3 | Update module specs (notifications, job, connections, admin), the Gap Register and Linear states | Step 9 | Docs match the shipped code |
| T8.4 | Commit and push once the user confirms; enable the purge cron; close the milestone | Step 10 | All issues Done |

Branch note for T8.4: commit to `ai_native_setup` per CLAUDE.md. Backend and frontend use `ai_native_setup_vishali` per your branch override. Confirm which applies.

---

## P2 / P3 — remaining BRD items (backlog placeholders, not in this milestone)

Each item becomes **one** backlog issue that needs its own spec before work starts. They are listed only so every BRD requirement traces to an issue.

**Phase 2**
- EX-02 Your next actions
- EX-03 Personal activity
- EX-04 Application status updates
- EX-05 Event reminders
- EX-06 Profile completeness with a reason
- EX-10 full (SLA colouring and trends)
- EX-11 Escalation rules
- EX-12 Daily admin digest
- EX-17 "What you missed" email digest
- EX-19 Notification preferences
- EX-20 Consent and compliance (DPDP Act)
- EX-21 Quiet hours and batching

**Phase 3**
- EX-07 Recommended for you
- EX-09 Profile views
- EX-13 Ecosystem pulse and dormant members
- EX-14 Program health alerts
- EX-15 Bulk actions
- EX-16 Notification analytics
- EX-18 Mobile push and WhatsApp

---

## Coverage check — every BRD item → issue

| BRD | Issue(s) |
|---|---|
| §7.1 qualifying visit | T2.2, T3.6, T4.3, T5.2 |
| §7.2 display rules | T3.5, T4.2, T4.4 |
| FR-U1 | T3.1, T4.8, T4.6 |
| FR-U2 | T3.2, T4.9 |
| FR-U3 | T2.4, T3.3, T3.7, T4.10 |
| FR-U4 | T2.6, T3.4, T3.9, T4.11 |
| FR-U5 | T2.5, T3.5, T3.8, T3.11, T4.5–T4.7 |
| FR-A1 | T5.4 (+T2.9) |
| FR-A2 | T5.5 |
| FR-A3 | T2.3, T5.6 |
| FR-A4 | T5.7 (+T2.9) |
| FR-A5 | T5.8 (+T2.8) |
| EX-01 | T2.7, T3.5, T4.12 |
| EX-08 | T3.5, T4.13 |
| EX-10 basic | T5.9 |
| D1–D9 | D1 → T1.3, T3.3 · D2 → T0.2 · D3 → T3.1 · D4 → T0.4, T5.5 · D5 → T5.1, T5.7 · D6 → T5.8 · D7 → T1.3, T5.6 · D8 → T1.3, T5.4, T5.8 · D9 → P2/P3 |
| NFR-01 | T3.12, T7.7 |
| NFR-02 | T3.10, T4.2 |
| NFR-03 | T7.3 |
| NFR-04 | T3.12 |
| NFR-05 | T6.3, T6.4 |
| NFR-06 | T5.1 |
| NFR-07 | T3.3, T7.6 |
| NFR-08 | T4.4, T7.4 |
| NFR-09 | T4.3, T7.5 |
| NFR-10 | No Phase 1 work — no new off-platform channel |
| NFR-11 | T5.10 |
| NFR-12 | T3.5 (single service) |
| §4 baselines | T8.1 |
| §18 sign-off | T0.1 |
