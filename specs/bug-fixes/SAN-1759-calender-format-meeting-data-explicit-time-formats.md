# SAN-1759 — calender formatMeetingData re-parses already-formatted times without a format

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1759 (Sentry SC-SAAS-FRONTEND-14)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (non-idempotent in-place mutation, moment deprecation fallback)

## Evidence
Sentry SC-SAAS-FRONTEND-14 (moment deprecation warning, fallback to native `Date()`): 129 events / 105 users, still firing on a release that already had the SAN-151 fix.

## Root cause
`formatMeetingData()` in `calender/helpers.ts` rewrites each `CalenderEvt.timeFrom`/`timeTo` in place to `'hh:mm a'`. When the same event objects pass through it a second time, it re-parsed `"YYYY-MM-DD 11:00 am"` with `moment.utc(string)` and no format; moment cannot recognise that as ISO/RFC2822 and falls back to `Date()`, logging the warning.

## Fix
`src/app/modules/calender/helpers.ts`: new `CALENDER_TIME_FORMATS = ['YYYY-MM-DD HH:mm:ss','YYYY-MM-DD HH:mm','YYYY-MM-DD hh:mm a']` and `parseCalenderUtc(date, time)` (`moment.utc(..., formats)`), used for both the from and to times, so raw API times and already-formatted ones resolve identically on every pass.

## Not fixed
The in-place mutation itself was kept, so `formatMeetingData()` is still not idempotent in general; it is only safe because of the explicit formats (recorded in the module spec Invariants).

## Contract impact
None. No API, flag or auth change; tenant scoping untouched (frontend only). Module spec updated: `sc-saas-frontend/src/app/modules/calender/module.spec.md`.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json` in `sc-saas-frontend`: exit 0.
- A node script on moment-timezone ran 9 cases (raw 24-hour with and without seconds, already-formatted 12-hour, first and second pass): 0 deprecation warnings.
- No automated test added: the guardian skill is blocked workspace-wide and Karma cannot run (SAN-1653). Not run in a browser.

## Commit
sc-saas-frontend `306c9bd5b` on `ai_native_setup_aman`, pushed. Not deployed.

## Sentry
Sentry SC-SAAS-FRONTEND-14 resolved 2026-10-07 under the 'fix in code => resolve' rule. Reopen it if it recurs on a build that contains the commit (check the event release tag with `git merge-base --is-ancestor`).
