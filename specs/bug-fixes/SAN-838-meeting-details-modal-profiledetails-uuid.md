---
id: SAN-838
title: "meeting-details-modal crashes reading 'uuid' on profileDetails before missing optional chaining"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-838
sentry:
  - SC-SAAS-FRONTEND-FA
repos: [frontend]
commit: sc-saas-frontend@34c30b40 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-838 — meeting-details-modal profileDetails race

## Root cause
`meeting-details-modal.component.html:11`:
```html
<div *ngIf="modalData?.event?.canEdit && (profileDetails.uuid === modalData?.event?.user?.uuid) && modalData.event?.meetingLocationType !== 'in_person'"
```
`profileDetails` is set asynchronously in `meeting-details-modal.component.ts`'s `ngOnInit` via a store subscription (`this.profileDetails$.pipe(...).subscribe((res) => { if (res) { this.profileDetails = res; } })`). Every other property in this expression uses `?.` except `profileDetails` itself, which is `undefined` until the first store emission, throwing `TypeError: Cannot read properties of undefined (reading 'uuid')`.

A second unguarded read of the same async `profileDetails` object exists at line ~100 (`profileDetails.accountType !== ACCOUNT_TYPE.STARTUP`) — same root cause, same race, just not the one Sentry's stack pointed at.

## Fix
`profileDetails?.uuid === modalData?.event?.user?.uuid` at line 11, and `profileDetails?.accountType !== ACCOUNT_TYPE.STARTUP` at line ~100 (defense-in-depth against the identical race, fixed alongside rather than as a separate ticket). Identical result once `profileDetails` loads; only tolerates the undefined window.

No API/DTO/flag/tenant-scoping impact — template-only optional-chaining additions.

## Blast radius
`sc-saas-frontend`'s calendar meeting-details modal.

## Verification
Full `ng build --configuration development` (AOT) — exit code 0, no errors on this file. No automated test suite exists for this repo yet — manual repro (open a meeting details modal from the calendar, confirm it renders without crashing before profile data resolves) is the substitute verification, still to be done by hand before commit.
