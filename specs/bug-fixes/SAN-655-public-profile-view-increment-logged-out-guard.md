---
id: SAN-655
title: "checkAndIncrementProfileView crashes reading 'id' of undefined for logged-out visitors on public profiles"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-655
sentry: [SC-SAAS-FRONTEND-BB, SC-SAAS-FRONTEND-2N]
related: [SAN-512, SAN-515]
repos: [frontend]
commit: sc-saas-frontend@d7af42b9 (branch ai_native_setup_vishali)
created: 2026-09-28
updated: 2026-09-28
---

# SAN-655 — guard `loggedInUserDetails?.id` in all public-profile view counters

## Root cause
Every public-profile page calls `checkAndIncrementProfileView()` after loading the profile, building `{ userId: this.loggedInUserDetails.id || '' }`. For a visitor who is not logged in (public profile links, crawlers), `loggedInUserDetails` is `undefined`, so `.id` throws before the `|| ''` fallback can apply.

- The ticket's own group, **BB** (`investor-public-profile-v2`, 1 event, release 022eafd6), was already fixed by `2fe7ae95` (SAN-512..515), which is in production.
- That fix only touched the investor page. The identical line was left unguarded on 5 sibling pages. **SC-SAAS-FRONTEND-2N** (symbolicated to `mentor-public-profile.component.ts:143`) has 42 events / 21 users in production, last seen 2026-09-11. The line is still unguarded in every production release in use (`90bde7be`, `33244b02`, `c2de0b1e`).

## Fix
`'userId': this.loggedInUserDetails.id || ''` → `'userId': this.loggedInUserDetails?.id || ''` in:
- `modules/mentors/pages/profile/mentor-public-profile/mentor-public-profile.component.ts`
- `modules/corporate/pages/profile/corporate-public-profile-v2/corporate-public-profile-v2.component.ts`
- `modules/individual-profile/pages/individual-public-profile/individual-public-profile.component.ts`
- `modules/program-office/profile/profile-office-public-profile/profile-office-public-profile.component.ts`
- `modules/service-provider/pages/profile/service-provider-public-profile/service-provider-public-profile.component.ts`

This matches the pattern already shipped on the investor and startup siblings.

## Blast radius
`sc-saas-frontend` only. No API/DTO/flag change. For logged-in users the value is identical. Logged-out visitors now send `userId: ''`, which is what the existing `|| ''` fallback always intended, instead of crashing.

## Verification
- `tsc -p tsconfig.app.json --noEmit` clean.
- Confirmed the unguarded line exists at `90bde7be`, `33244b02` and `c2de0b1e`.
- No automated test added (workspace "guardian" skill unavailable). Manual check: open a public mentor/corporate profile link in a logged-out browser. The page loads with no console TypeError, and the view increment request still fires.

## Open questions
None.
