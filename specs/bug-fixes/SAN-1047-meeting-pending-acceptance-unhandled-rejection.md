# SAN-1047 — fetchMeetingsWithPendingAcceptance() rethrow surfaces as unhandled promise rejection

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1047
- **Repo:** sc-saas-frontend · **Type:** Bug · **Priority:** Medium · **Assignee:** Sandeep
- **Classification:** CODE_ERROR

## Problem
Sentry `SC-SAAS-FRONTEND-2W` (one of 6 groups in the SAN-1045 umbrella investigation).
`MeetingService.fetchMeetingsWithPendingAcceptance()` toasts on HTTP failure and rethrows. All 3
callers subscribed with a bare `(res) => {...}` next-callback and no `error:` handler, so the
already-toasted failure additionally surfaced as an unhandled rejection — pure Sentry noise on top
of a failure the user already saw.

## Root cause
- `src/app/modules/dashboard-v2/components/dashboard-sidebar/dashboard-sidebar.component.ts:262`
- `src/app/modules/calender/calender-component/full-calender-component.ts:110`
- `src/app/modules/calender/calender-component/calender-notes/calender-notes.component.ts:97`

## Fix
Converted all 3 `.subscribe((res) => {...})` calls to the object-form
`.subscribe({ next: (res) => {...}, error: () => {} })`, matching the established no-op-error
pattern already used for this class of bug (SAN-509, `startup-all-required-details-form.component.ts`).
Zero change to any success path — only the previously-unhandled rejection is now absorbed.

## Verification
- `tsc --noEmit -p tsconfig.json`: 0 errors in the 3 edited files (3,926 pre-existing errors
  elsewhere, all in the vendored CometChat kit — unrelated)
- Added `src/app/core/service/meeting.service.spec.ts`: asserts the service still toasts *and*
  emits an error on a 504, locking down the contract the fixed callers now rely on
- `tsc --noEmit -p tsconfig.spec.json`: 0 errors in the new spec (16 pre-existing errors elsewhere,
  unrelated files)
- `ng test --include=meeting.service.spec.ts`: could not run — same repo-wide gap as SAN-1004, the
  Karma bundle fails to compile due to ~16 pre-existing unrelated broken specs, 0 of 0 executed

## Commit
sc-saas-frontend@016f34063 (branch ai_native_setup_sandeep) — "fix(meeting): update fetchMeetingsWithPendingAcceptance to handle errors correctly and prevent unhandled rejections"
