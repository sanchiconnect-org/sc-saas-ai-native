---
id: SAN-834
title: "profileDetails.mobileNumber read without guard in edit-profile and notification-settings"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-834
sentry:
  - SC-SAAS-FRONTEND-ES
repos: [frontend]
commit: sc-saas-frontend@537c9e64 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-834 — profileDetails.mobileNumber unguarded (2 remaining call sites)

## Root cause
`Uncaught (in promise): TypeError: undefined is not an object (evaluating 't.profileDetails.mobileNumber')`. A sibling call site (`program-public-apply.component.ts:213-220`) was already fixed 2026-08-24 (commit `f0484689`, SAN-482) with an early-return guard `if (!this.profileDetails) return`. Two other call sites were never fixed:
- `edit-profile.component.ts:214`
- `notification-settings.component.ts:180` (`handleSameAsMobileNumber()`)

Both read `this.profileDetails.mobileNumber` unguarded when `profileDetails` hasn't loaded yet.

## Fix
`this.profileDetails?.mobileNumber` at both remaining call sites — same effect as the already-fixed sibling, just via optional chaining instead of an early return, matching each file's existing style.

No API/DTO/flag/tenant-scoping impact — two-line optional-chaining addition.

## Blast radius
`sc-saas-frontend`'s account edit-profile page and notification-settings page ("same as mobile number" checkbox flow).

## Verification
`npx tsc --noEmit` and full `ng build --configuration development` (AOT) both clean, no new errors on either file. No automated test suite exists for this repo yet — manual repro (open both pages with profile data loading slowly, toggle "same as mobile number," confirm no crash and correct value once loaded) is the substitute verification, still to be done by hand before commit.

## Related
Same root cause/fix pattern as SAN-482 (SC-SAAS-FRONTEND-3D, `program-public-apply.component.ts`) — that fix wasn't audited for other `profileDetails.mobileNumber` call sites at the time; this ticket closes the remaining two.
