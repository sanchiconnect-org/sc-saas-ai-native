---
id: SAN-831
title: "community-feed-stats-count crashes reading 'uuid' before profileData loads from store"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-831
sentry:
  - SC-SAAS-FRONTEND-F4
repos: [frontend]
commit: sc-saas-frontend@3d911978 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-831 — community-feed-stats-count profileData race

**Correction (2026-09-18):** this ticket originally also cited SC-SAAS-FRONTEND-EY as the same bug — that was wrong. EY is actually "Cannot set properties of undefined (setting 'isActive')" in the investors module, an unrelated, still-unfixed issue. Removed from this ticket; not yet tracked elsewhere.

## Root cause
`community-feed-stats-count.component.ts:117`:
```ts
get showOwnProfile() { return !(!this.userDetails || this.userId === this.profileData.uuid) }
```
Guards `userDetails` but not `profileData`, which is populated asynchronously from an NgRx store subscription. Angular can evaluate this template getter before the first store emission lands, throwing `TypeError: Cannot read properties of undefined (reading 'uuid')`.

## Fix
`this.userId === this.profileData?.uuid` — identical result once `profileData` loads; during the async gap the getter now just evaluates falsy instead of throwing, matching the existing intent of the surrounding `!this.userDetails ||` short-circuit.

No API/DTO/flag/tenant-scoping impact — one-line optional-chaining addition.

## Blast radius
`sc-saas-frontend`'s `community-feed-stats-count` shared component, used wherever community feed / profile stats are rendered.

## Verification
`npx tsc --noEmit` and full `ng build --configuration development` (AOT) both clean, no errors on this file. No automated test suite exists for this repo yet — manual repro (load a page rendering this component under network throttling to widen the async gap, confirm no crash) is the substitute verification, still to be done by hand before commit.
