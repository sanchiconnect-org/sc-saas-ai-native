---
id: SAN-833
title: "Unguarded res.features read duplicated across 8 profile-type services — crashes reading 'features'"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-833
sentry:
  - SC-SAAS-FRONTEND-B0
repos: [frontend]
commit: sc-saas-frontend@5ee71f61 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-833 — res.features unguarded across 8 profile-type services

## Root cause
`mentors.service.ts:94-99` (and 7 identical copies):
```ts
store.pipe(select(getBrandDetails)).subscribe((res) => {
  if (res) {
    if (res.features.logout_on_rejection) { ... }
  }
});
```
Guards `res` but not `res.features`, throwing `TypeError: Cannot read properties of undefined (reading 'features')` (culprit: `Object.next` in the mentor-forms module, but Sentry's minified stack doesn't distinguish which of the 8 copies actually fired). The identical unguarded pattern is duplicated verbatim in:
- `corporate.service.ts:95`
- `individual-profile.service.ts:97`
- `investor-dashboard.service.ts:101`
- `mentors.service.ts:96`
- `partners.service.ts:198`
- `program-office.service.ts:95`
- `service-provider.service.ts:95`
- `startup-dashboard.service.ts:50`

This will recur for every profile type until all 8 are fixed, not just mentors.

## Fix
Added `?.` to `res.features` in all 8 files (`res.features?.logout_on_rejection`), matching the existing `if (res)` guard style already used in each. Same one-line change repeated 8 times — no behavior change once `getBrandDetails` emits with a populated `features` object.

No API/DTO/flag/tenant-scoping impact — 8× identical optional-chaining addition.

## Blast radius
`sc-saas-frontend`: all 8 profile-type dashboards (corporate, individual, investor, mentor, partner, program-office, service-provider, startup) that read `getBrandDetails` for the `logout_on_rejection` feature flag.

## Verification
`npx tsc --noEmit` and full `ng build --configuration development` (AOT) both clean, no new errors across all 8 files. No automated test suite exists for this repo yet — manual repro (load 2-3 different profile-type dashboards, confirm no crash and `logout_on_rejection` toast still fires when the flag is set) is the substitute verification, still to be done by hand before commit.

## Confidence note
Sentry's stack trace only pins the crash to the mentor-forms module's minified `Object.next`; the other 7 files were found by pattern-matching the identical unguarded code, not by direct stack-trace attribution. Given the pattern is byte-for-byte identical across all 8 (same `store.pipe(select(getBrandDetails)).subscribe` shape), high confidence this is the same defect class recurring per profile type, not a coincidence.
