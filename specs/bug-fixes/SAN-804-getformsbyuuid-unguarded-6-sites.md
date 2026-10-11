---
id: SAN-804
title: "[Sentry SC-SAAS-FRONTEND-1] getFormsByUUID/getFormsByIDs unguarded across 6 call sites — forms-management/uuids network blip — 175 users"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-804
sentry:
  - SC-SAAS-FRONTEND-1
repos: [frontend]
commit: pending (uncommitted on ai_native_setup_vishali — user verifying locally first)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-804 — unhandled getFormsByUUID()/getFormsByIDs() failures (6 sites)

## Root cause
`FormManagementService.getFormsByUUID()`/`getFormsByIDs()`
(`sc-saas-frontend/src/app/core/service/form-management.service.ts:81-92`) toasts + re-throws on
error. `Http failure ... 0 Unknown Error` is a client-side network blip. This Sentry bucket
(SC-SAAS-FRONTEND-1) is shared with SAN-509 and SAN-375 (both Done, different call sites) — today's
event is a third, distinct `forms-management/uuids/*` call. Of the 7 `.subscribe()` sites named in
the ticket, 6 had no `error` callback at all.

## Fix
Converted the 6 sites from bare-callback `.subscribe((res) => {...})` to
`.subscribe({ next: (res) => {...}, error: () => {} })`, matching the established pattern from
SAN-509/375/504/507:
- `src/app/modules/vs-programs/vs-program-details-page/vs-program-details-page.component.ts:106`
- `src/app/modules/vs-programs/vs-program-details-page/vs-program-details-edit-page-links/vs-program-details-edit-page-links.component.ts:105`
- `src/app/modules/dynamic-forms/dynamic-form-submit/dynamic-form-submit.component.ts:115`
- `src/app/modules/dynamic-forms/dynamic-form-preview/dynamic-form-preview.component.ts:91`
- `src/app/modules/programs/programs-details-page/programs-details-page.component.ts:178`
- `src/app/modules/programs/programs-details-page/program-details-edit-page-links/program-details-edit-page-links.component.ts:126`

## Not in scope
The 7th call site, `application-program-management-dynamic-form.component.ts:353-355`, already had
an `error` handler added under SC-SAAS-FRONTEND-2W — that part of the ticket description was stale;
no change made there.

## Blast radius
None — purely additive error handling, `next`/success-path behavior unchanged at all 6 sites.

## Verification
`npx tsc --noEmit --skipLibCheck` across the whole project: zero errors in any of the 6 touched
files (baseline pre-existing errors are unrelated `*.spec.ts` test-runner-types issues). No
automated test added — user opted to skip given the size of the remaining Urgent/High queue;
gap noted rather than silently skipped.
