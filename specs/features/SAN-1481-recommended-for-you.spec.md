---
id: SAN-1481
title: "Notifications Phase 3 — EX-07 Recommended for you (challenges, mentors, investors matched to the startup)"
type: feature
status: done                    # approved 2026-10-08 (+D-0); implemented 2026-10-08; SAN-1831/1832 + SAN-1481 Done; tab name "Challenges", 72 h chip, legacy-dashboard ordering accepted by Mahima; manual dev-tenant run + EXPLAIN pending
linear: https://linear.app/sanchiconnect/issue/SAN-1481/notifications-p3-ex-07-recommended-for-you   # parent issue (project "Enhancement"); sub-issues SAN-1831 (backend), SAN-1832 (frontend)
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1, EX-07, Phase 3 (not wireframed). BRD text itself is NOT in the workspace; only the Linear SAN-1481 placeholder text is available."
repos: [backend, frontend]      # dependency order, under the recommended defaults. tenants/admin only if OQ-10 picks a new flag; none of the other repos are touched.
contracts:
  api:
    - "GET api/v1/startups/recommended/challenges   (backend, NEW — JwtAuthGuard + RolesGuard(Role.STARTUP) + class FeatureGuard; @Features(STARTUP, BUSINESS_CHALLENGES, NOTIFICATION_CENTRE_ENABLED) on the method)"
    - "GET api/v1/startups/recommended/investors    (backend, EXISTING startup.controller.ts:480 — ADDITIVE `matchReasons[]` per item; ranking fix only when notification_centre_enabled is on (OQ-7))"
    - "GET api/v1/startups/recommended/mentors      (backend, EXISTING startup.controller.ts:507 — same additive `matchReasons[]` + ranking fix + cap (OQ-7, OQ-12))"
    - "GET api/v1/startups/recommended/corporates   (backend, EXISTING startup.controller.ts:533 — UNCHANGED under the default; only if OQ-5 extends reasons to it)"
    - "investors|mentors|corporates /recommended/startups (EXISTING — UNCHANGED under the default; OQ-5)"
  flags:
    - notification_centre_enabled   # EXISTING (SAN-1401) — recommended gate for every NEW behaviour (OQ-10)
    - business_challenges           # EXISTING (Feature.BUSINESS_CHALLENGES) — gates the challenges tab/route
    - startups                      # EXISTING (Feature.STARTUP) — already on the startup recommended routes
    - new_dashboard_layout          # EXISTING — consumed by frontend placement (dashboard-v2 only, OQ-15)
  events:
    - "None under the recommended default: no notifications row type, no InAppCategory, no cron job, no socket emit (OQ-1)"
tenant_scoped: true
depends_on: [SAN-1381]          # flag + dashboard-v2 Phase 1 code present. Not dependent on SAN-1471/1472/1478 code under the default (no new notification type).
created: 2026-10-08
---

# Notifications Phase 3 — EX-07 Recommended for you

## Reference and evidence tags

- **Source:** Linear SAN-1481 (no comments), verbatim:
  > Placeholder (BRD Phase 3). Needs its own spec. Not wireframed.
  > BRD ref: EX-07. Matches based on sector, stage, persona and activity: challenges to apply to, mentors to request, investors aligned with the startup's thesis.
- **The BRD text is not in the workspace.** Searched `specs/`, repo docs and `*.md` for `EX-07`, "Recommended for you", "recommendation" — only the SAN-1381 backlog lists mention EX-07 (`specs/features/SAN-1381-notifications-action-driven-dashboard.spec.md:533`, `specs/features/SAN-1381-linear-breakdown.md:253`). NFR-10 wording is also not in the workspace; SAN-1381's trace only says "NFR-10: No Phase 1 work — no new off-platform channel" (`SAN-1381-linear-breakdown.md:292`).
- **Builds on:** SAN-1381 (flag, counters, dashboard-v2 catch-up card), SAN-1478 (in-app categories), SAN-1471 / SAN-1472 (writer + cron patterns, only relevant if OQ-1 picks bell rows).
- **`ai-startups-analyzer` is not checked out in this workspace** (no `ai-startups-analyzer/` directory). Its capabilities are taken from `specs/features/FAI-001-*.spec.md` / `FAI-002-enrichment-thesis.spec.md`.
- **Tags** (per `specs/spec-authoring-practices.md`): **[EV]** evidenced with `file:line`; **[INFERRED]** drawn from code, not stated; **[NOT SPECIFIED]** nothing in source says either way; **[DDP]** = `[DESIGN DECISION PENDING]`, see Open questions.
- Paths without a repo prefix are in `sc-saas-backend/src/`.

## Problem

A startup has no single place that says "here is what fits you": which open challenges match its sector, which mentors to request, and which investors invest in its space. EX-07 asks for a "Recommended for you" surface driven by sector, stage, persona and activity.

**The most important finding is that most of this already exists** (§1). A rule-based recommender for startup → investors / mentors / corporates and investor / mentor / corporate → startups is live, and dashboard-v2 already renders it as a "Recommendations" card. What is missing is: (a) challenges, (b) stage and activity signals, (c) any "why recommended" shown to the user, and (d) correct ranking. The recommended MVP therefore **extends the existing feature** instead of building a new engine.

## Current state (checked against code, 2026-10-08)

### 1. Existing recommendation feature (prior art — reuse, don't reinvent)

**Backend routes** (all `version: '1'`, class-level `@UseGuards(FeatureGuard)`):

| Route | Guard / roles | Service | Evidence |
|---|---|---|---|
| `GET startups/recommended/investors` | `JwtAuthGuard, RolesGuard`, `@Roles(STARTUP)`, `@Features(STARTUP)` | `StartupService.getRecommendedInvestors` | [EV `modules/startup/startup.controller.ts:472–492`; `startup.service.ts:153–337`] |
| `GET startups/recommended/mentors` | same | `StartupService.getRecommendedMentors` | [EV `startup.controller.ts:499–518`; `startup.service.ts:344–482`] |
| `GET startups/recommended/corporates` | same | `StartupService.getRecommendedCorporates` | [EV `startup.controller.ts:525–545`; `startup.service.ts:1961–2075`] |
| `GET startups/recommended/hide-investor/:uuid`, `hide-corporate/:uuid` | same | writes the startup **user id** into `investors.hide_recommended_startup` / `corporates.hide_recommended_startup` JSON | [EV `startup.controller.ts:552–599`; `startup.service.ts:1675–1733`; `investor.repository.ts:2224–2250`] |
| `GET investors/recommended/startups` (+ `hide-startup/:uuid`) | investor | `InvestorService.getRecommendedStartups` | [EV `investor.controller.ts:437–485`; `investor.service.ts:829–997`] |
| `GET mentors/recommended/startups` | mentor | `MentorService.getRecommendedStartups` | [EV `mentor.controller.ts:242–263`; `mentor.service.ts:623–785`] |
| `GET corporates/recommended/startups` (+ `hide-startup/:uuid`) | corporate | `CorporateService.getRecommendedStartups` | [EV `corporate.controller.ts:286–338`; `corporate.service.ts:652–781`] |

**How matching works today (startup side):**
- **Investors** — candidate SQL: `investors.is_approved = 1`, `is_search_results = 1`, not hidden for this startup user, AND (any startup sector ∈ `investment_details.sectoral_interest_ids`) **AND** (any startup business model ∈ `investment_details.business_models`), ordered `approved_on DESC`, page size 100 [EV `modules/investor/repositories/investor.repository.ts:2115–2216`]. Then per row, in JS: count common sectors and business models into `totalPoints`, drop rows with an existing connection (rejected ones reappear after 180 days), slice to 12 [EV `startup.service.ts:189–336`].
- **Mentors** — SQL: `is_approved = 1`, `is_search_results = 1`, AND sector overlap **AND** technology overlap **AND** mentorship-area overlap, no limit, no hide list [EV `modules/mentors/repositories/mentor.repository.ts:1172–1242`]; same JS scoring/connection exclusion [EV `startup.service.ts:360–481`].
- **Weekly investor email** — cron `STARTUP_RECOMMENDATIONS_FOR_INVESTOR` emails every approved investor the startups that joined recently, by email + WhatsApp (no in-app row) [EV `modules/cron/startup-recommendation-to-investor.service.ts:35–123`; seed `cron/repository/cron-job.repository.ts:90`; manual trigger `global/admin-actions/admin-actions.controller.ts:310`].

**Defects found in the existing feature** (each is in scope only as far as the MVP touches it — see P-4):
1. **Ranking is effectively "newest approved first", not "best match first".** The list is sorted by `totalPoints`, then *re-sorted* by `approvedTimestamp` with a comparator that ignores points, so points only break exact-timestamp ties [EV `startup.service.ts:327–333` (investors), `:472–478` (mentors)]. [INFERRED from JS sort semantics]
2. **Match reasons are computed but never shown.** `industriesCount`, `businessModelsCount`, `technologiesCount`, `mentorshipAreaCount`, `totalPoints` are set server-side [EV `startup.service.ts:223–238, 392–405`] but no frontend file reads them [EV grep `sc-saas-frontend/src`: no match]. Also `investmentDetails` is overwritten with an array of sector names [EV `startup.service.ts:312–314`], so the response shape is irregular.
3. **Over-strict AND across categories.** A startup with no business models gets an empty-OR bracket for that category [EV `investor.repository.ts:2184–2194`; `if (businessModels)` is true for `[]`]. Whether TypeORM renders an empty `Brackets` as match-all, match-none or invalid SQL is not verified [INFERRED — dev lead to confirm]. Either way a mentor must overlap on all three of sector, technology and mentorship area to appear [EV `mentor.repository.ts:1202–1236`].
4. **N+1 queries.** `getAllMembersIds()` and `getConnectionDetails()` run once per candidate inside the loop (up to 100 investors) [EV `startup.service.ts:243–252, 408–417`].
5. **Holes in the response.** `delete investors.items[i]` / `delete mentors[i]` leaves `undefined` slots [EV `startup.service.ts:266, 270, 431, 435`, comment at :275–277]; mentors are returned unsliced, so a hole serialises as `null` and the frontend maps `e.user[0]` [EV `sc-saas-frontend/src/app/shared/common-components/recommended-mentors/recommended-mentors.component.ts:61–66`]. [INFERRED crash risk]
6. **Mentor "hide" calls the wrong endpoint.** `RecommendedMentorsComponent.hideStartup()` calls `hideRecommendedStartups(id, accountType)` [EV `recommended-mentors.component.ts:72–91`], which hits `investors/recommended/hide-startup/` (or the corporate one) [EV `core/service/recommended.service.ts:119–123`]. A startup user hiding a mentor would hit an investor-only route with a mentor uuid. No hide-mentor route exists. [INFERRED: 403/404]
7. **Not partner-scoped.** None of the recommendation queries apply hub/spoke `partner_id` scoping, while the directory search does [EV `modules/search/module.spec.md:58, 64`; `search.service.ts:166–204`].
8. **Unused notification types.** `NotificationType.STARTUP_SUGGESTION` / `INVESTOR_SUGGESTION` [EV `core/constants/enum.ts:351–352`] have writers `addStartupSuggestionNotification` / `addInvestorSuggestionNotification` [EV `modules/notifications/repositories/notifications.repository.ts:303–351`] with **no callers** in backend, admin or frontend code [EV grep]. They are `send_to = all` broadcasts, not personal recommendations.

**Frontend surfaces:**
- **dashboard-v2** renders `<app-dashboard-recommendations-v2>` titled "Recommendations", only when `profileCompleteness?.isApproved` [EV `sc-saas-frontend/src/app/modules/dashboard-v2/dashboard-v2.component.html:204–206`; card `components/dashboard-recommendations-v2/dashboard-recommendations-v2.component.html:1–47`]. Tabs by persona [EV `dashboard-recommendations-v2.component.ts:58–141`]: startup → Investors / Mentors / Corporates (each gated on `brandDetails.users.*`); investor, mentor, corporate → Startups. **No challenges tab.** No `notification_centre_enabled` gate.
- **Legacy dashboards** show `<app-recommended-investors>` / `<app-recommended-mentors>` on the startup dashboard, gated by the startup's own `services_looking_for` (fundraising / mentorship) [EV `modules/startups/pages/dashboard/dashboard.component.html:50–65`], and `<app-recommended-startups>` on investor, mentor and program-office dashboards [EV grep `app-recommended-startups`]. dashboard-v2 does **not** use `services_looking_for`.
- Shared components + service: `shared/common-components/recommended-{investors,mentors,corporates,startups}/`, `core/service/recommended.service.ts`, endpoints in `core/service/api-endpoint.service.ts:181–182, 262–269`.
- No admin caller [EV grep `recommended/` in `sc-saas-admin`: no match].

### 2. Matching data available (how each field is stored)

All sector/technology/area fields are **JSON arrays of master-table ids** (not FKs, not free text), matched today with `JSON_CONTAINS(col, 'id') OR JSON_CONTAINS(col, '"id"')` because ids are stored both as numbers and strings [EV e.g. `investor.repository.ts:2177`].

| Signal | Startup | Investor | Mentor | Corporate | Challenge | Program (CFA) |
|---|---|---|---|---|---|---|
| **Sector** (`industry_domains` master) | `startups.startup_industries` JSON ids [EV `startup.entity.ts:413–418`]; `startup_industry_primary_id` int [:434–435]; sub-categories JSON [:427–432]; free-text `startup_other_industries` [:420–425] | `investor_investment_details.sectoral_interest_ids` JSON [EV `investor-investment-details.entity.ts:38–39`]; sub-categories [:44–49]; free-text others [:41–42] | `mentors.sectoral_interest_ids` JSON [EV `mentor.entity.ts:106–111`] | `corporates.sectoral_interest_ids` JSON [EV `corporate.entity.ts:81–86`] | `challenges.sectoral_interest_ids` JSON [EV `challenges.entity.ts:82–87`], resolved against `IndustryDomainsEntity` [EV `challenges.repository.ts:85–92`] | **none** — no sector column on `application_programs` [EV grep `application-programs.entity.ts`] |
| **Technology** (`technology_domains`) | `startup_technologies` JSON [EV `startup.entity.ts:399–404`] | — | `mentors.technologies` JSON [EV `mentor.entity.ts:99–104`] | — | — | — |
| **Mentorship need / expertise** (`domain_areas`) | `startups.mentorship_areas` JSON [EV `startup.entity.ts:437–442`] | — | `mentors.domain_areas` JSON [EV `mentor.entity.ts:85–90`] | — | — | — |
| **Business model** (`business_models`) | `startup_business_models` JSON [EV `startup.entity.ts:450–455`] | `investment_details.business_models` JSON [EV `investor-investment-details.entity.ts:54–55`] | — | — | — | — |
| **Stage** | Four unrelated stage fields: `startups.incubation_stage` → `incubation_stages` [EV `startup.entity.ts:444–448, 631–634`]; `startup_financials.funding_stage_id` → `funding_stages` [EV `startup-financials.entity.ts:16–20, 84–88`]; `startup_financials.revenue_stage` enum `pre_revenue/post_revenue` [EV :35–40; `enum.ts:668–671`]; `startup_product.product_stage_id` → `product_stages` [EV `startup-product.entity.ts:22–23, 65–68`]; `startups.trl_level` 1–9 [EV `startup.entity.ts:155–170`] | `investment_details.investment_stage_ids` JSON → **`investment_stages`** master (`id, name, is_active`) [EV `investor-investment-details.entity.ts:35–36`; `global/investment_stages/investment_stages.entity.ts:3–13`]. Import sample value "Pre Revenue" [EV `modules/import/dto/import-investor.dto.ts:184`] | none | none | none (participants record `maturity_stage_id` at apply time [EV `challenge-participants.entity.ts:42–43`]) | none |
| **Ticket size** | `startup_financials.target_fundraise` **varchar free text** [EV `startup-financials.entity.ts:22–23`] | `ticket_size_min/max` int [EV `investor-investment-details.entity.ts:10–24`] | — | — | — | — |
| **Instruments** | `startup_financials.instrument_ids` JSON [EV :32–33] | `investment_mechanism_ids` JSON [EV :29–30] (matching commented out [EV `startup.service.ts:176–180`]) | — | — | — | — |
| **Persona / intent** | `users.account_type`; `startups.services_looking_for` SET (`fundraising, tech_hiring, customer_access, business_services, mentorship`) [EV `startup.entity.ts:457–468`; `enum.ts:236–242`] | — | — | — | startups only (SAN-1381 OQ-6) | `membership_stakeholder_type` [EV `notification-counters.repository.ts:288`] |
| **Discoverability / approval** | `is_approved`, `is_search_results` | `is_approved` [EV `investor.entity.ts:138`], `is_search_results` (default false) [:110–115], `approved_on` [:144] | `is_approved` [EV `mentor.entity.ts:137`], `is_search_results` (default **true**) [:144–149] | `is_approved`, `is_search_results` (default true) [EV `corporate.entity.ts:129, 150–156`] | `approval_status`, `privacy_type` | `status`, `test_mode_enabled`, … |

**Conclusions on matching quality:**
- **Sector is matchable across every pair** that EX-07 names (startup ↔ challenge, mentor, investor), on one shared master (`industry_domains`). [EV, and INFERRED that `startup_industries` and challenge/investor/mentor sector ids reference the same master — same `IndustryDomainsEntity` resolver is used for all: `startup.service.ts:309, 463`; `challenges.repository.ts:86`]
- **Stage is NOT matchable today without a decision.** The investor's stage preference uses the `investment_stages` master; the startup has no column pointing at that master. A mapping (or a new startup field) is needed. Challenges, mentors and programs have no stage preference at all. → OQ-3.
- **Ticket size is NOT matchable**: the startup side is free text. → Out of scope.
- **Programs have no sector**, so "recommended programs" could only be "eligible + open", which the SAN-1381 opportunities counter already covers. → Out of scope (EX-07 names challenges, not programs).

### 3. Activity signals available

| Signal | Where | Notes |
|---|---|---|
| Profile views | `profile_views` (`user_id` = viewer, `profile_type`, `profile_id`, `created_at`) [EV `modules/user/entities/profile-views.entity.ts:6–28`]; written by `trackProfileView()` [EV `user/repositories/user.repository.ts:1268–1283`]; 30-day viewer list [EV :1291–1319] | Usable as "you looked at X" or "people like you viewed Y"; EX-09 (Profile views, Phase 3) also builds on it |
| Connections | `connections` (status, `other_user_id`) | Already used as an **exclusion** (no rec for existing connections) |
| Challenge applications | `challenge_participants` (`startup_id`) | Already used by `getLiveChallenges` as `applied` [EV `notification-counters.repository.ts:210–212`] |
| Mentorship requests | `mentorship` (`mentor_id`, `startup_id`, `approval_status`) [EV `modules/mentorship/entities/mentorship.entity.ts:12–62`] | **Not** used today; existing mentor recs exclude connected mentors only |
| Opportunity views | `notification_item_views` (challenge/program/event) [EV `notification-counters.repository.ts:208–209`] | Written by SAN-1381 mode-B |
| Hides | `investors/corporates.hide_recommended_startup`, `startups.hide_recommended_investor/corporate` JSON user-id lists | Dismiss mechanism exists for investor/corporate only |

### 4. "Opportunities" eligibility to reuse for "challenges to apply to"

`NotificationCountersRepository.getLiveChallenges(userId, startupId, startupApproved)` [EV `modules/notifications/repositories/notification-counters.repository.ts:199–238`]:
- startups only (called only when `isStartup && moduleOn(Feature.BUSINESS_CHALLENGES)` [EV `notification-counters.service.ts:322–328`]);
- `challenge_status = 'active'`, `approval_status = 'approved'`, `status = 1`, `deleted_at IS NULL`, `dead_line >= UTC_DATE() OR NULL`;
- internal-platform challenges only while their CFA is open (`program_type = business_challenge`, `status = 1`, not test mode, not closed);
- unapproved startups see `privacy_type = 'public'` only;
- returns `applied` (a `challenge_participants` row) and `viewed`.
- It selects `uuid, title, createdAt, closesAt, viewed, applied` only — **not** `sectoral_interest_ids` — and has **no partner scoping**.

### 5. Notification Centre pieces (relevant only if OQ-1 picks bell/notifications)

- `InAppCategory` has 7 keys; **none fits recommendations** (`connectionRequests, jobApplications, applicationUpdates, deadlines, communityActivity, communityPosts, eventReminders`) [EV `core/constants/enum.ts:388–396`]. A bell-delivered recommendation would need a new key (e.g. `recommendations`) in the backend enum + `NOTIFICATION_TYPE_IN_APP_CATEGORY` [EV :409–429] and a new row in the frontend In-app table (SAN-1478 D-6).
- Writer + cron precedents: SAN-1471 `ApplicationStatusNotificationsService`, SAN-1472 `EventReminderService` (`specs/features/SAN-1472-event-reminders.spec.md` §P-4–P-6).
- SAN-1381 Decision #3: the `bell` number never counts generic `notifications` rows.
- dashboard-v2 catch-up card / "You're all caught up" + one suggested action picked from enabled modules [EV `sc-saas-frontend/src/app/modules/dashboard-v2/components/dashboard-catch-up/dashboard-catch-up.component.ts:102–110`]; dashboard-v2 only (SAN-1381 OQ-8).

### 6. Other capabilities checked

- **ai-startups-analyzer:** admin-only LLM scoring of program applications against a program "thesis" (`POST /api/v1/generate-thesis/`, `upload-csv`) [EV `specs/features/FAI-002-enrichment-thesis.spec.md:10, 70–82`]. The "thesis" there is a *program's evaluation rubric*, not an investor's investment thesis; it is called only by sc-saas-admin, costs LLM spend per call, and has no user-facing or matching endpoint. **Not reusable for EX-07** → rule-based MVP.
- **Directory search** (`modules/search/`) filters by the same master ids and is partner-scoped [EV `search/module.spec.md:58, 64`].
- **FeatureGuard** is AND across listed flags and fails *open* when a flag is `undefined` (`saasFeatures[f] === false` check) [EV `core/guards/feature-guard.ts:15–24`].

## Overlap with other Phase 2/3 items

| Item | Overlap | Recommended handling |
|---|---|---|
| EX-02 "Your next actions" (SAN-1469, Backlog, not specced) | Lists "deadlines within 72 h not yet applied to" — the same challenges can appear in both | EX-07 = *fit* (why this suits you); EX-02 = *urgency* (act now). No de-duplication in the MVP; a closing-soon chip on a recommended challenge is allowed [DDP → OQ-14] |
| EX-01 catch-up / EX-08 empty state (SAN-1381) | The empty state's single suggested action is module-based, not personal | Unchanged in the MVP [DDP → OQ-14] |
| FR-U3 opportunities counter (SAN-1381) | Same live/eligible challenge set | Reuse the same eligibility SQL; do not change the counter |
| EX-09 Profile views (Phase 3) | Same `profile_views` table | Activity signals deferred (OQ-4); no conflict |
| EX-19 / SAN-1478 preferences | Only if recommendations become bell rows | No new InAppCategory under the default (OQ-1) |
| EX-20 / SAN-1479 DPDP consent | Concerns off-platform channels (email/WhatsApp opt-in) | No off-platform channel in the MVP (OQ-9) |

## Proposed design — recommended MVP (every [DDP] decided as written on 2026-10-08, amended by D-0 below)

**P-1 — Surface: the existing dashboard-v2 card, renamed, no bell.** [DDP → OQ-1, OQ-2, OQ-15]
- When `notification_centre_enabled` is on, the existing `app-dashboard-recommendations-v2` card is titled **"Recommended for you"** and, for startups, gains a **Challenges** tab placed first (when `business_challenges` is on).
- No `notifications` rows, no bell count, no badge, no cron, no new InAppCategory.
- Flag off → the card is byte-for-byte today's "Recommendations" card.

**P-2 — Challenges to apply to** (new route `GET api/v1/startups/recommended/challenges`)
- **Base set = exactly `getLiveChallenges` eligibility** (§4), minus `applied` challenges. Extract the WHERE clause into one shared SQL fragment / repository method so the counter and the recommendation can never drift (NFR-03 spirit).
- **Match:** overlap between `challenges.sectoral_interest_ids` and the startup's `startup_industries` (same `JSON_CONTAINS` id-or-string idiom; ids filtered with `Number.isFinite` per SAN-478).
- Challenges with NULL/empty sectors are treated as "Open to all sectors" and ranked after sector matches [DDP → OQ-6].
- **Rank:** number of shared sectors DESC → `closesAt` ASC (NULL last) → `created_at` DESC. **Limit 6** [DDP → OQ-12].
- **Response item:** `{ uuid, title, corporateName (unless hide_corporate_info), closesAt, viewed, matchReasons: [{ type: 'sector', labels: string[] } | { type: 'open_to_all' } | { type: 'closing_soon', closesAt }] }`. Labels come from `industry_domains.name`.
- Guards: `JwtAuthGuard, RolesGuard`, `@Roles(Role.STARTUP)`, `@Features(Feature.STARTUP, Feature.BUSINESS_CHALLENGES, Feature.NOTIFICATION_CENTRE_ENABLED)` on the method (class already has `@UseGuards(FeatureGuard)`). Startup identity from the JWT session only (`session.startupId`), never from a param.

**P-3 — Mentors to request / investors aligned with the startup** (existing routes, behaviour changes only with the flag on)
- **Additive `matchReasons[]` per item** (always present; additive JSON field, safe for old clients):
  - investors: `sector` (shared sector names), `business_model` (shared business model names);
  - mentors: `sector`, `technology`, `mentorship_area`.
- **Ranking fix (flag on):** sort by `totalPoints` DESC, then `approvedOn` DESC as the tie-breaker [DDP → OQ-7].
- **Relaxed matching (flag on):** sector overlap required; business model (investors) and technology / mentorship area (mentors) become score boosts instead of hard AND filters [DDP → OQ-16, dev lead for the query shape].
- **Exclusions:** keep today's (approved, `is_search_results = 1`, hidden list, existing connection with the 180-day rule). Mentors additionally exclude mentors with a `mentorship` row for this startup in `pending`/`approved` [DDP → OQ-4].
- **Mentor list capped at 12** like investors [DDP → OQ-12].
- Stage and ticket size are **not** matched in the MVP (§2) [DDP → OQ-3].
- Corporates and the investor/mentor/corporate → startups routes are unchanged [DDP → OQ-5].

**P-4 — Defect fixes bundled because the MVP touches the same code** (dev lead to confirm, OQ-17)
- Hoist `getAllMembersIds()` out of the loop and batch the connection lookup into one query (defect 4).
- Filter instead of `delete`, so no holes are returned (defect 5).
- Stop overwriting `investmentDetails` with sector names; return names in `matchReasons` instead — **only when the flag is on**, to keep flag-off responses identical (defect 2).
- Frontend: hide the "hide" action on mentor cards (defect 6) until a hide-mentor route exists [DDP → OQ-11].

**P-5 — "Why recommended" (explainability)**
- Each card shows one short line built from `matchReasons`, e.g. "Matches your sectors: FinTech, AgriTech", "Also: SaaS business model", "Open to all sectors", "Closes in 2 days".
- Only the viewer's own overlap with fields already shown on the target's public profile is surfaced; no hidden data.

**P-6 — Performance**
- On-demand, per dashboard load; no precompute/cron (data volumes per tenant are directory-sized; existing recs are already on-demand).
- Challenges: one SQL + one `industry_domains` lookup. Investors/mentors: one candidate SQL + one batched connection SQL + master-name lookups (batched).
- Target p95 ≤ 300 ms for `recommended/challenges` on the largest tenant (borrowed from NFR-01; the BRD's own budget for EX-07 is [NOT SPECIFIED]).
- `EXPLAIN` the challenges query; `JSON_CONTAINS` on JSON columns cannot use an index, so the candidate set is bounded by the status/deadline predicates first.

**P-7 — Privacy and tenancy**
- One deployment = one tenant; every query runs on this deployment's DB; no host/tenant hard-coding (invariant #5).
- Person recommendations only ever include approved profiles with `is_search_results = 1` (the user's own "show me in search" opt-in) — unchanged from today.
- Hub/spoke: challenges follow `getLiveChallenges` (no partner filter today); person recommendations stay tenant-wide as today [DDP → OQ-8].
- No email/WhatsApp; no new personal data stored [DDP → OQ-9].

## Acceptance criteria

**Gate**
- [ ] With `notification_centre_enabled` off: the dashboard card title, tabs, items, order and the JSON of `GET startups/recommended/investors|mentors|corporates` are identical to today except for the additive `matchReasons` field; `GET startups/recommended/challenges` returns 403.
- [ ] With `business_challenges` off: no Challenges tab; the route returns 403.
- [ ] Non-startup sessions get 403 from `recommended/challenges` (RolesGuard).

**Challenges**
- [ ] A startup with sectors {FinTech, AgriTech} sees a live, eligible, not-applied challenge tagged FinTech, with the reason "Matches your sectors: FinTech".
- [ ] Applied challenges, expired challenges (deadline before today), inactive / unapproved / soft-deleted challenges and internal challenges whose CFA is closed or in test mode never appear.
- [ ] An unapproved startup sees only public challenges (same rule as `getLiveChallenges`). (Only reachable if OQ-13 shows the card to unapproved startups.)
- [ ] Every challenge in the list is also counted by the FR-U3 opportunities counter for the same user (shared eligibility; automated test compares the two sets).
- [ ] Order: 2 shared sectors before 1; equal scores order by nearest deadline; "open to all sectors" items come after all sector matches (per OQ-6). At most 6 items.
- [ ] A startup with no sectors gets only "open to all sectors" challenges (or an empty state), never an error.

**Mentors and investors (flag on)**
- [ ] Items are ordered by match strength first (a 2-category match before a 1-category match regardless of approval date).
- [ ] An investor sharing the sector but not the business model is included (OQ-16 default), ranked below one sharing both.
- [ ] Each item carries `matchReasons` with human-readable labels; the card shows the "why" line.
- [ ] Already-connected profiles (except rejections older than 180 days) and hidden investors never appear; mentors with a pending/approved mentorship with this startup never appear (OQ-4 default).
- [ ] No `null`/hole entries in any response; mentors capped at 12.
- [ ] The number of SQL queries per request does not grow with the number of candidates (connection lookup batched).

**UI**
- [ ] With the flag on, a startup's dashboard-v2 card reads "Recommended for you" with tabs Challenges / Investors / Mentors / Corporates (each only when its module/persona is enabled); clicking a challenge opens `/challenges/{uuid}/details` [EV route `sc-saas-frontend/src/app/app-routing.module.ts:185`].
- [ ] Empty tab shows a short empty message ("No matching challenges right now — complete your sectors to get better matches" or similar, copy per OQ-18), not a blank card.
- [ ] The mentor card no longer offers a "hide" action that calls an investor route (OQ-11 default).

**Isolation and security**
- [ ] All new/changed queries read only this deployment's DB, use only the session's `startupId`/`userId`, and pass `/check-isolation`.
- [ ] The new route's auth model is stated in code and module spec: JWT + RolesGuard(STARTUP) + FeatureGuard.

## Per-repo plan

### backend (`sc-saas-backend`) — SAN-1831, first

- `modules/notifications/repositories/notification-counters.repository.ts`: extract the live-challenge WHERE clause (:213–225) into a reusable fragment/method; `getLiveChallenges` keeps its exact output.
- New `RecommendationsRepository` method (location: `modules/startup/repositories/` or a small `modules/recommendations/` provider — dev lead's call, OQ-17) `getRecommendedChallenges(startupId, startupApproved, startupSectorIds, limit)` returning rows + `sectoral_interest_ids`.
- `modules/startup/startup.controller.ts`: `GET recommended/challenges` next to :480–545, guards per P-2.
- `modules/startup/startup.service.ts`: `getRecommendedChallenges(session)`; in `getRecommendedInvestors` (:153–337) and `getRecommendedMentors` (:344–482): `matchReasons`, flag-on ranking fix, batching, hole-free filtering, mentor cap, mentorship exclusion.
- `modules/investor/repositories/investor.repository.ts:2172–2194` and `modules/mentors/repositories/mentor.repository.ts:1202–1236`: flag-on relaxed matching (sector required, others scored) per OQ-16.
- `core/constants/api-success-message.ts`: `RECOMMENDED_CHALLENGES_FETCHED_SUCCESSFULLY`.
- Module specs: update `modules/startup/module.spec.md`, `modules/notifications/module.spec.md` (shared eligibility), `modules/investor/module.spec.md`, `modules/mentors/module.spec.md`.
- Jest: challenge eligibility parity with `getLiveChallenges`; sector scoring and ranking; open-to-all handling; no-sector startup; flag off → 403 and byte-identical investor/mentor payload apart from `matchReasons`; ranking fix; relaxed matching; batching (query count); no holes; mentor cap; mentorship exclusion. `npm run build`, `npm run lint`.

### frontend (`sc-saas-frontend`) — SAN-1832, after backend

- `core/service/api-endpoint.service.ts`: `RECOMMENDED_CHALLENGES` (`startups/recommended/challenges`) near :262–269.
- `core/service/recommended.service.ts`: `getRecommendedChallenges()`.
- New `shared/common-components/recommended-challenges/` (card list, reason line, closing-soon chip, link to `/challenges/{uuid}/details`).
- `modules/dashboard-v2/components/dashboard-recommendations-v2/`: when `features.notification_centre_enabled`, title "Recommended for you" and a first "Challenges" tab for startups when `features.business_challenges`; otherwise unchanged.
- `recommended-investors` / `recommended-mentors` components: render the "why" line from `matchReasons` when present; tolerate missing field (old backend).
- `recommended-mentors.component.*`: hide the "hide" action (OQ-11 default).
- Karma: tab list per persona and flags; reason-line rendering; empty state; flag off = old title/tabs. `npm run build`.

### tenants / admin / tenants-admin / 3rdparty-webservices / ai-startups-analyzer

- **No change under the recommended defaults.**
- **tenants (+ backend `Feature`, frontend `IFeatures`, admin `config.php`):** only if OQ-10 picks a dedicated flag such as `recommendations_enabled` (`/trace-flag`).
- **admin:** only if OQ-3 picks an admin-maintained stage mapping, or OQ-1 picks a cron that operators enable through the generic `cron_jobs` page.
- **3rdparty-webservices:** only if OQ-1 adds an email digest.
- **ai-startups-analyzer:** not used (§6).

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| API (#2) — NEW `GET api/v1/startups/recommended/challenges` | New route, startup-only | `/audit-contract` vs `core/service/recommended.service.ts` + `api-endpoint.service.ts` |
| API (#2) — `GET startups/recommended/investors`, `/mentors` | Additive `matchReasons[]` always; ordering, matching breadth, mentor cap and `investmentDetails` shape change **only with `notification_centre_enabled` on** | `/audit-contract` (frontend `recommended-*` components are the only consumers; no admin caller [EV grep]) |
| Flags (#1) | None new under the default; consumes `notification_centre_enabled`, `business_challenges`, `startups`, `new_dashboard_layout` | `/trace-flag notification_centre_enabled`, `/trace-flag business_challenges` |
| Shared eligibility with SAN-1381 counters | Refactor of `getLiveChallenges` WHERE into a shared fragment; output must stay identical | Jest parity test |
| Tenant scoping (#5) | Per-deployment DB; session-derived ids only; hub/spoke unchanged (OQ-8) | `/check-isolation` |
| Auth (#4) | New route uses existing `JwtAuthGuard` + `RolesGuard`; no change to the JWT model | — |
| Verification shape (#3), PowerPitch (#6) | Not touched | — |

## Test plan

There is no "guardian" test skill in this workspace; say so in the PR wherever automated coverage can't be added.

- **backend:** jest per the plan; `npm run build`; `npm run lint`. Manual on a dev tenant: startup with 2 sectors, 5 challenges (2 matching, 1 open-to-all, 1 applied, 1 expired) → expect 3 in the right order; investor with sector-only match appears with flag on, not with flag off; mentor with a pending mentorship is excluded; `EXPLAIN` the challenges query.
- **frontend:** karma per the plan; `npm run build`; manual dashboard-v2 walk-through as startup / investor / mentor with the flag on and off.
- **cross-repo:** flag off → no visible change; tenant A only → tenant B unaffected; a challenge shown in the card is also in the opportunities count.

## Rollout

1. **backend** — new route (403 until the flag is on), additive `matchReasons`, flag-gated behaviour changes. No migration, no new table or column.
2. **frontend** — tab, reason line, mentor hide fix; tolerant of an older backend (missing `matchReasons` / 404 on the new route → tab hidden).
3. Enable per tenant with the existing `notification_centre_enabled` rollout; verify on the internal tenant first.

## Out of scope

- ML / embeddings / LLM ranking; ai-startups-analyzer.
- Ticket-size and instrument matching (startup side is free text / commented out).
- Program (CFA) recommendations (no sector data on `application_programs`; covered by the FR-U3 opportunities counter).
- Bell notifications, email/WhatsApp digests, new InAppCategory, cron precompute — unless OQ-1 changes this.
- Changing the weekly `STARTUP_RECOMMENDATIONS_FOR_INVESTOR` email cron.
- Removing or wiring the unused `startup_suggestion` / `investor_suggestion` types.
- Legacy (non-`new_dashboard_layout`) dashboards (OQ-15).
- Recommendations for service providers, individuals, partners, program office, job seekers.

## Open questions

None. Resolved by Mahima on 2026-10-08: every OQ-1 … OQ-18 takes its recommended default, **amended by D-0**.

### D-0 — Existing behaviour must not change when the flag is off (Mahima, 2026-10-08)

With `notification_centre_enabled` off, every existing recommendation route and the dashboard card behave exactly as today: same items, same order, same response fields, same buttons. Concretely:

- `matchReasons` is added to responses **only when the flag is on** (overrides the "always additive" default).
- Ranking fix (OQ-7), relaxed strictness (OQ-16), mentor cap/exclusion, removal of null/empty slots, and removal of the broken mentor hide button (OQ-11) apply **only when the flag is on**.
- The per-candidate query (N+1) fix may apply to every tenant **only if its output is identical**; this must be proven by regression tests that compare old vs new output.
- `investors|mentors|corporates/recommended/startups` routes are untouched.
- The dashboard-v2 card template is unchanged when the flag is off; rename to "Recommended for you" and the challenges tab only when on.
- Before changing any existing route, check every consumer (frontend, admin cURL, any other caller) and keep the response contract intact.
- Acceptance adds: flag-off regression tests for each touched existing route showing identical output before/after.

| OQ | Decision |
|---|---|
| OQ-1 Surface | dashboard-v2 card only |
| OQ-2 Card | extend the existing card, renamed "Recommended for you" when the flag is on |
| OQ-3 Stage | no stage matching in MVP |
| OQ-4 Activity | exclusion only (applied, connected, hidden, existing mentorship) |
| OQ-5 Personas | startups only |
| OQ-6 Sector-less challenges | included as "Open to all sectors", ranked last |
| OQ-7 Ranking fix | flag-on only |
| OQ-8 Hub/spoke | no change (tenant-wide) |
| OQ-9 Privacy / DPDP | no new consent; approved, search-visible profiles and public fields only |
| OQ-10 Gate | `notification_centre_enabled` + module flags (`business_challenges` for challenges) |
| OQ-11 Hide | no hide for challenges; broken mentor hide button removed (flag-on only, per D-0) |
| OQ-12 Counts | challenges 6, investors 12, mentors 12 |
| OQ-13 Unapproved startups | card stays approved-only |
| OQ-14 EX-02 / EX-08 overlap | no de-duplication; empty state unchanged |
| OQ-15 Legacy dashboards | dashboard-v2 only |
| OQ-16 Strictness | sector required, other categories add score, empty lists skipped (flag-on only) |
| OQ-17 Placement (dev lead) | `StartupService`; share eligibility with counters; bundle fixes (subject to D-0) |
| OQ-18 Copy | as proposed in the spec |

## Linear tracking

- **Parent:** SAN-1481 (project "Enhancement", assignee Mahima Sharma, In Progress). No new project.
- **Sub-issues:** priority Low, assignee Mahima Sharma, project Enhancement, parent SAN-1481, labels `Feature` + repo badge. Only repos that need changes under the recommended defaults; add tenants/admin sub-issues later only if OQ-1, OQ-3 or OQ-10 require them. Each sub-issue's description now states the spec was **approved by Mahima on 2026-10-08 with D-0** (updated 2026-10-08). Both are **In Review** (not Done) pending Mahima's review, commit and a dev-tenant smoke check.

| Repo | Issue | Notes |
|---|---|---|
| backend | [SAN-1831](https://linear.app/sanchiconnect/issue/SAN-1831/backend-notifications-p3-ex-07-recommended-for-you) | — |
| frontend | [SAN-1832](https://linear.app/sanchiconnect/issue/SAN-1832/frontend-notifications-p3-ex-07-recommended-for-you) | blocked by SAN-1831 |

## Implementation notes (2026-10-08)

Implemented on `ai_native_setup_mahima` in both repos, **uncommitted**, on top of the uncommitted SAN-1471 / SAN-1472 work (not reverted or reformatted). No migration, no new flag, no notification type, no cron. The legacy-dashboard, tenants, admin, tenants-admin, 3rdparty and analyzer repos are untouched.

### What was built

**backend (SAN-1831)**
- `GET api/v1/startups/recommended/challenges` — `startup.controller.ts`. Auth: `JwtAuthGuard` + `RolesGuard` with `@Roles(Role.STARTUP)` (same as the sibling `recommended/*` routes) + class-level `FeatureGuard` with `@Features(STARTUP, BUSINESS_CHALLENGES, NOTIFICATION_CENTRE_ENABLED)`. The startup comes from the JWT session only. Tenant-scoped by the deployment DB (invariant #5); no partner filter (OQ-8, same as the FR-U3 counter).
- Shared eligibility: `LIVE_CHALLENGES_FROM_WHERE_SQL` + `liveChallengesWhereParams()` exported from `notification-counters.repository.ts`; `getLiveChallenges` now uses them, and its SQL text and bind params are **byte-identical** to before (snapshot recorded before the extraction).
- `StartupRecommendationsRepository` (new, `modules/startup/repositories/`): challenge candidates (shared eligibility + `NOT EXISTS challenge_participants`), batched newest-connection lookup, active-mentorship mentor ids.
- `InvestorRepository.getRecommendedInvestorsBySector` and `MentorsRepository.getRecommendedMentorsBySector` (new, flag-on only; sector required, other categories scored; ids bound as parameters). The existing `getRecommendedInvestors` / `getRecommendedMentors` queries are unchanged.
- `StartupService`: `getRecommendedChallenges`; `getRecommendedInvestors` / `getRecommendedMentors` branch to new `...ForYou` methods only when `saasFeatures.notification_centre_enabled === true`.

**frontend (SAN-1832)**
- `RECOMMENDED_CHALLENGES` endpoint, `RecommendedService.getRecommendedChallenges()` (no toast on error), `core/domain/recommendation.model.ts`.
- New `shared/common-components/recommended-challenges/` (link to `/challenges/{uuid}/details`, corporate name unless hidden, reason line, closing-soon chip, empty state copy "No matching challenges right now. Complete your sectors to get better matches.").
- `shared/utils/recommendation-reasons.ts` (reason line / closing chip copy per OQ-18).
- `DashboardRecommendationsV2Component`: with the flag on, title "Recommended for you", a first "Challenges" tab for startups when `business_challenges` is on, and `[showReasons]="true"` for the investor and mentor lists. The tab is dropped if the route errors (older backend / 403), as the Rollout section asks.
- `RecommendedInvestorsComponent` / `RecommendedMentorsComponent`: `@Input() showReasons = false`.

### D-0 evidence — existing behaviour with the flag off

| Existing surface touched | Consumers checked | Change with flag off | Proof |
|---|---|---|---|
| `GET startups/recommended/investors` → `StartupService.getRecommendedInvestors` | Frontend `RecommendedService.getRecommendedInvestors` → `RecommendedInvestorsComponent` (dashboard-v2 card and legacy startup dashboard). No caller in sc-saas-admin, tenants, tenants-admin or 3rdparty (grep). No backend caller except the controller; the weekly `STARTUP_RECOMMENDATIONS_FOR_INVESTOR` cron uses different repository methods. | Only the team-member list is read once per request (lazily, at the same point in the loop) instead of once per candidate. Per-candidate connection lookups, name lookups, holes, double sort and slice are unchanged. | `sc-saas-backend/src/modules/startup/startup-recommendations.flag-off.spec.ts`: 12 snapshots (investors mixed / 14 candidates / all connected, mentors mixed / connected, corporates) for flag `false` and flag missing. Recorded by running the spec against the **unchanged** service before any edit, then re-run with `--ci` after the changes: all pass, and the `.snap` file is byte-identical to the pre-change copy (`cmp`). Covers item order, every field, `null` slots and the arguments of every `getConnectionDetails` call. |
| `GET startups/recommended/mentors` → `getRecommendedMentors` | Frontend `RecommendedMentorsComponent` (both dashboards). Same grep as above. | Same team-list change only. | Same spec. |
| `GET startups/recommended/corporates` | Frontend `RecommendedCorporatesComponent`. | **Not changed** (code untouched). | Same spec, corporates snapshot. |
| `investors|mentors|corporates/recommended/startups` | — | **Not touched.** | — |
| `NotificationCountersRepository.getLiveChallenges` (FR-U3 counter) | `NotificationCountersService` (counters endpoint, bell). | Refactor to the shared fragment. | `live-challenges-eligibility.spec.ts`: SQL text + params snapshot recorded before the extraction; identical after (`cmp`). |
| dashboard-v2 `DashboardRecommendationsV2Component` | `DashboardV2Component` (only host). | Title via interpolation; new tab/inputs only when the flag is on. | `dashboard-recommendations-v2.component.recommended-for-you.spec.ts`: renders the **pre-change template verbatim** (from git HEAD) next to the current one with the same state, for 6 cases (startup with all modules + business_challenges on, flag explicitly false, startup mentors-only, investor, mentor, corporate), and asserts the normalised DOM and tab list are equal. Normalisation removes only Angular comment anchors, `ng-reflect-*`/`_ngcontent` attributes and ngbNav's global id counter. |
| `RecommendedInvestorsComponent` / `RecommendedMentorsComponent` | dashboard-v2 card and legacy startup dashboard (`modules/startups/pages/dashboard`). | New input defaults to `false`; with it, the mapped items are exactly as before. | `recommended-investors.component.reasons.spec.ts` (items equal the old mapping, null / user-less entries still filtered). |

The N+1 fix is split per D-0: the **team-list hoist** applies to all tenants (proven identical above); the **batched connection lookup** is not provably identical at SQL level with mocks, so it runs only in the flag-on path.

### Deviations from the spec text

1. **`matchReasons` only with the flag on** (D-0 overrides P-3 "always additive"; already stated in D-0).
2. **`investmentDetails` is still overwritten with sector names in the flag-on path** (P-4 bullet 3 not done). The investor card (`investors-search-card`, shared with the search pages) renders `investmentDetails` as the sector badges; changing the shape would break it. Sector names are also in `matchReasons`.
3. **Mentor "hide" removal (OQ-11 / defect 6): nothing to remove.** `recommended-mentors.component.html` renders `app-mentor-search-card`, which has no hide action; the hide-capable card is commented out. `hideStartup()` is unreachable and was left untouched.
4. **Flag-on extras**: investors / mentors without a top-level user row are dropped (the frontend already filtered them for investors; for mentors they would crash `mentor-search-card`). Duplicate ids in the startup's own sector list are de-duplicated before scoring.
5. **Closing-soon window = 72 hours** (not specified in the spec; aligned with EX-02's 72 h deadline notion). Chip copy "Closes today" / "Closes in N days".
6. **Tab name is the fixed "Challenges"**, not the tenant's `business_challenges_title` (some tenants call the module "Open Innovation") — copy per OQ-18.
7. **A missing startup on `recommended/challenges` throws `STARTUP_PROFILE_NOT_ATTACHED`** (session self-lookup convention from SAN-606), not `STARTUP_NOT_FOUND`.
8. **Ranking/strictness for challenges is done in TypeScript** over the eligible set, not with `JSON_CONTAINS` in SQL; sector ids are parsed with the same `Number.isFinite` rule (and `null` ids ignored).

### Verification

- backend: `npx tsc --noEmit -p tsconfig.json` clean. Jest (scratch config stubbing `@aws-sdk/client-sesv2`): startup + notifications + mentors + investor + job + cron = 21 suites / 367 tests pass, 14 snapshots pass. Full suite: 62 of 68 suites pass; the 6 failing suites (`program-management.service`, `programs.repository`, `application-programs.repository`, `in-app-notification-settings`, `global-onboarding-design`, `partner-domain-access`) fail on SAN-1471/1472 or older uncommitted changes (`notifyApplicationStatus` stub missing, `event_reminder` mute mapping, onboarding hero fields, timing) and import none of the SAN-1481 files. eslint: 0 errors in new files and in the SAN-1481 hunks of existing files (the pre-existing prettier errors in `investor.repository.ts`, `mentor.repository.ts`, `startup.controller.ts` were left alone).
- frontend: `npx tsc --noEmit -p tsconfig.app.json` clean; `ng build --configuration development` (output in the scratchpad) succeeds with no warning from a touched file; Karma (temporary tsconfig) 37/37 pass across 4 new specs. Karma's "Some of your tests did a full page reload!" also appears with an untouched spec (`toast.service.spec.ts`), so it is a harness issue, not SAN-1481.
- Contract check: response shapes match `core/domain/recommendation.model.ts`; flag-on items keep every field the cards read. Isolation check: all new queries use session ids only, bind ids as parameters, and read only the deployment DB.

### Still open

- Manual dev-tenant run (flag off: dashboard unchanged; flag on: challenge order, sector-only investor, mentor with pending mentorship excluded) and `EXPLAIN` of the challenges query — not done here.
- The existing `dashboard-recommendations-v2.component.spec.ts` ("should create", no Store provider) was left as is.
