---
id: SAN-1473
title: "Notifications Phase 2 — EX-06 Profile completeness with a reason"
type: feature
status: done                    # approved 2026-10-08 (OQs resolved by Mahima); implemented 2026-10-08; browser check pending
linear: https://linear.app/sanchiconnect/issue/SAN-1473/notifications-p2-ex-06-profile-completeness-with-a-reason
owner: Mahima Sharma
source: "BRD v1.1, EX-06 (W-01 annotation 5), Phase 2"
repos: [frontend]
contracts:
  api: ["None — reuses the existing GET */profile_completeness responses unchanged"]
  flags: [notification_centre_enabled]   # EXISTING — gate (OQ-4)
  events: []
tenant_scoped: false            # display only
depends_on: [SAN-1381]
created: 2026-10-08
---

# EX-06 Profile completeness with a reason

## Reference
- **BRD (from Linear):**
  > A completeness meter that explains the benefit of each missing field, e.g. "Add your sector and stage to appear in investor searches". Better profiles also sharpen eligibility matching for FR-U3.

## Current state (checked 2026-10-08)
- **The backend already returns field-level gaps.** Every persona's `GET …/profile_completeness` returns `forms.<section> = {total, completed, percentage, missingFields: string[]}`. The `missingFields` entries are plain messages, e.g. "Industries are missing" [EV `startup.repository.ts:1822-2156`, `core/utils/app.utils.ts:63` `calculateCompleteness`]. **No reason text exists anywhere.**
- **The frontend turns gaps into linked lists.** `getMissingFieldsMap()` [EV `shared/utils/common-methods.ts:520`] builds groups of missing fields, each linking to its edit page via `MissingFormKeyToUrlMapping` [EV `shared/constants/constants.ts:31`].
- **Where that list shows:**
  - In a popover on the persona completeness widgets: startup `app-startup-raise-fund-switch` [EV lines 148-162], plus the `{mentor,corporate,partner,service-provider,program-office,individual}-profile-completeness` widgets.
  - **dashboard-v2** shows the percentage only [EV `dashboard-v2.component.html:50-58`].
- **What actually feeds investor search and matching** [EV `startup.repository.ts:1065` searchStartupOrLiveDeal; `investor.repository.ts:2115` getRecommendedInvestors]:
  - industries and sub-categories, primary industry, technologies, business models
  - product stage, funding stage, revenue stage, instruments
  - country, state, city
  - Industries and business models also drive recommended-investor matching.
- **Existing bug (out of scope; Gap Register G-015):** the partner report puts its data under `mentorInformation` [EV `partner.repository.ts:932`], so partner "missing" links point at the mentor edit page.

## Proposed design (recommended defaults)
- **P-1 Copy [DDP OQ-3]:** a frontend constant `PROFILE_GAP_BENEFITS` maps each known missing-field message to a one-line benefit. Examples:
  - "Industries are missing" → "Add your industries so investors searching your sector find you, and to get recommended investors."
  - "Product stage is missing" → "Add your product stage to appear in stage-filtered investor searches."

  Unknown messages (custom forms, documents, new fields) fall back to a per-section benefit. If there's no section benefit either, no reason is shown.
- **P-2 Placement [DDP OQ-1]:**
  - (a) Each missing field in the existing completeness popovers gets its benefit as a second line. This covers every persona widget, with one shared helper.
  - (b) **dashboard-v2:** under the percentage meter, a "Why complete your profile" list shows the **top 3** missing items with their benefit, each linking to its edit page. They are ranked by benefit priority: search/matching fields first.
- **P-3 Personas [DDP OQ-2]:**
  - Startup gets field-level benefits for all built-in criteria.
  - The other personas get section-level benefits ("Complete your mentor profile to appear in mentor search and get session requests"), plus field-level benefits where the field obviously feeds search (industries / sectors, expertise, location).
- **P-4 Gate [DDP OQ-4]:** shown only with `notification_centre_enabled`. With the flag off, the widgets look exactly as today.

## Acceptance criteria
- [ ] A startup missing industries sees "Industries are missing" plus its benefit line in the popover, and in the dashboard-v2 top 3.
- [ ] Search/matching gaps rank above cosmetic ones (e.g. logo) in the top 3.
- [ ] An unknown message shows its section benefit, or no reason; it never breaks the layout.
- [ ] 100 % → no "Why complete" list.
- [ ] Flag off → widgets are unchanged.
- [ ] No backend or API change.

## Open questions

None. All four were resolved by Mahima on 2026-10-08, by accepting the recommended defaults: popovers plus a dashboard top 3; startup at field level and other personas at section level; hardcoded copy; flag-gated.

## Implementation notes (2026-10-08)

Frontend only, uncommitted on `ai_native_setup_mahima`.

- `shared/constants/profile-gap-benefits.ts`: field-level benefits for every built-in startup criterion, plus section-level benefits for all persona sections and custom forms. Each has a `rank`, and search/matching fields rank first.
- `getMissingFieldsMap()` now adds `benefit` and `benefitRank` to each item. The extra properties don't affect existing consumers: nav links, the guard and the stepper.
- **All 8 completeness popovers** (startup, investor, corporate, mentor, partner, service provider, program office, individual) show the benefit under each missing field, only with `notification_centre_enabled`.
- **dashboard-v2:** a "Why complete your profile (N%)" card under the next-actions card shows `topProfileGaps()`, the top 3 linked items. Custom-form links use the persona's route prefix.
- **Verification:** Karma 26/26, including the new `profile-gap-benefits.spec.ts` (field reason, section fallback, top-3 order, empty). The AOT build passes. Not run: a browser check.
- **Not fixed (Gap Register G-015):** the partner completeness report uses the `mentorInformation` key, so partner links and reasons follow the mentor section.
