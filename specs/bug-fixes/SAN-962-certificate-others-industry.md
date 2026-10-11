---
id: SAN-962
title: Tripura certificate Industry sector omits "Others" free-text industries
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-962
repos: [backend]
created: 2026-09-23
updated: 2026-09-23
---

# SAN-962 — merge `startupOtherIndustries` into the certificate's Industry sector text

## Request

Startup Edit Profile → Industry/Technology step lets an admin/startup check standard industries
(Healthcare, Finance, Electric Vehicles, ...) and, separately, check "Others" and type a free-text
value (e.g. "AI"). The Tripura Recognition Certificate's body sentence ("The Start-Up is working in
**{industry sector}** Industry sector.") showed the checked standard industries but never the "Others"
value.

## Investigation finding

Two genuinely separate fields, by design, not a bug in how the data is stored:

- `startups.startupIndustries` — `number[]`, fixed lookup-table ids into `industry_domains`. Cannot
  hold free text; this is what the checkbox grid submits.
- `startups.startupOtherIndustries` — `string[]`, free text (e.g. `["AI"]`). This is what "Others"
  submits — a completely separate payload key end-to-end (frontend `industry-technology.component.ts`,
  DTO `industry-technology.dto.ts`, backend `startup.repository.ts`).

## Root cause

`sc-saas-backend/src/modules/certificates/certificates.service.ts`'s `resolveIndustrySector()` read
only `startupIndustries`. It deliberately excluded `startupOtherIndustries`, per its own docstring:
"the profile's Industry Domain block does not render it either." That premise is stale — the
currently-routed public profile (`StartupPublicProfileV2Component`,
`startup-public-profile-v2.component.html:377-380`) already renders `startupOtherIndustries` as chips
in the same Industry Domain block, alongside `startupIndustries`. Only the older, unrouted
`StartupPublicProfileComponent` still omits it. The certificate formatter was never updated to match.

## Fix

`resolveIndustrySector()` now also reads `user.startup.startupOtherIndustries` (already loaded
alongside `startupIndustries` on the same `startup` relation — `UserRepository.getUserById()` already
includes it, so this adds no new query) and appends those free-text entries after the resolved
fixed-option names, deduped case-insensitively against them, before joining into the final
comma-separated string.

## Design decisions taken (not asked, judgment calls)

- **Dedupe case-insensitively.** Not explicitly requested, but an Others entry that happens to restate
  an already-checked standard industry name (e.g. typing "Healthcare" into Others when Healthcare is
  already checked) would otherwise double it in the sentence — a small correctness gap worth closing
  while touching this exact merge logic, not scope creep.
- **Appended after, not interleaved with, the fixed-option names.** Matches the order the public
  profile itself uses (`startupIndustries` chips first, `startupOtherIndustries` chips after) —
  keeping the certificate's ordering consistent with what the startup's own profile shows, rather than
  inventing a different order.
- **Left the point-in-time/live-read caveat already documented on this method untouched** — this fix
  doesn't change that behavior (still a live read, not a snapshot), so it wasn't relitigated here.

## Verified

- `npx tsc --noEmit` clean, `npx eslint` clean (0 new errors/warnings — pre-existing unrelated
  unused-import warnings only) on the changed file.
- Confirmed `startup.startupOtherIndustries` is already loaded by `UserRepository.getUserById()`'s
  existing `relations: ['startup', ...]` — same relation `startupIndustries` already relies on — so no
  new query was introduced.
- Also corrected a pre-existing, unrelated drift in `certificates/module.spec.md`: it claimed
  `industrySector` resolved from `startupIndustryPrimaryId`, but the actual code (confirmed by its own
  docstring) reads `startupIndustries` — fixed while updating this section rather than left stale.

## Not verified — genuinely outstanding

No live end-to-end test: this environment has no login to submit the Industry/Technology form or view a
rendered certificate. Needs a real check — select standard industries + Others with a custom value on a
Tripura-themed startup, then view/regenerate its certificate — to confirm the sentence includes the
Others value with correct formatting and no duplication.

## Rollout

Not committed. Awaiting review and a real test from the user.

## Open questions

None blocking.
