---
id: SAN-2032
title: "Network 0/504 fault echoes reach Sentry; some call sites hide the status, and HW leaked an applicant email in prod"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2032
sentry: [SC-SAAS-FRONTEND-HP, SC-SAAS-FRONTEND-HV, SC-SAAS-FRONTEND-HW, SC-SAAS-FRONTEND-HS, SC-SAAS-FRONTEND-2W]
repos: [frontend]
related: [SAN-470, SAN-562, SAN-1899, SAN-1930, SAN-1992]
commit: frontend@865618f41 (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2032: normalise the fault-log call sites

## Root cause
* The `beforeSend` in `src/main.ts` has **no** status-0 or 5xx filter. SAN-1930 only recommended one, and SAN-1992 left the decision pending. The only HTTP drops today are the `HANDLED_HTTP_FAULT` message list and the thrown-401 drop added by SAN-1673.
* `metrics.service.ts`, `profile.service.ts` and `investor-dashboard.service.ts` called `httpFaultMessage(fault)` without a status fallback. A failure with an empty body therefore logged the generic "Something went wrong" and hid the status (HS, and F2 earlier).
* Five services (corporate, individual-profile, mentors, program-office, service-provider) all log a copy-pasted `getIndividualInvestorCompleteness` warn label (HV).
* HW: in prod, `program-public-apply.component.ts` logged `error?.message`, which contains the URL, and that URL contains the applicant's email. SAN-1899 (`ebde31ce4`) already removed that on the branch, but it isn't deployed.
* HP and 2W are expected network faults. 2W's latest event comes from a July build.

## Fix (call sites only; the filter is **not** implemented)
* `httpFaultMessage(fault, `HTTP ${fault?.status}`)` at:
  * `metrics.service.ts:57`
  * `profile.service.ts:95`
  * `investor-dashboard.service.ts:49, 67, 82, 111, 125`
* Warn labels renamed to the method each one sits in:
  * `getCorporateProfileCompleteness`
  * `getInvididualProfileCompleteness` (the misspelling is the method's real name)
  * `getMentorProfileCompleteness`
  * `getProgramOfficeProfileCompleteness`
  * `getServiceProviderProfileCompleteness`
* `program-public-apply.component.ts`: logs `applicationProgramManagementApplicationDetails( ${httpFaultMessage(error, `HTTP ${error?.status}`)} )`. It still skips 404 and status 0. `httpFaultMessage` reads only the response body, so the URL and the email never reach the log.
* Tests (3) in `program-public-apply.component.spec.ts`:
  * a 500 whose `error.message` carries the email URL logs only `( Boom )`;
  * a 502 with no body logs `( HTTP 502 )`;
  * 404 and status 0 log nothing.

## Blast radius / existing-flow impact
Only log text changes. Toasts and UI are unchanged, and no spec asserted on the old strings.

## Decision pending (dev lead, open since SAN-1930 / SAN-1992)
Should `beforeSend` drop the console-warn echoes `( HTTP 0 )` and `( HTTP 502|503|504 )`? And should it also drop thrown status-0/5xx `HttpErrorResponse`s? Dropping the thrown ones also hides missing error handlers (the SAN-1978 / SAN-2031 class of bug).

## Ops
* Deploy HEAD; this also removes the email PII path.
* Redeploy the stale tenants: startupchhattisgarh, trise, firstwings, isba, ciicies, acicvgu and sineedge.
* Consider deleting the HW event in Sentry, since it contains PII.

## Verification
* Targeted specs: `npx ng test --watch=false --browsers=ChromeHeadlessCI --include=<connect-button, connections-v3, dashboard-v2, program-public-apply, app.component specs>` → `TOTAL: 48 SUCCESS`.
* `npx tsc -p tsconfig.app.json --noEmit` → 0; `npx tsc -p tsconfig.spec.json --noEmit` → 0.
* `npm run gates` (sc-saas-frontend, all five frontend tickets together):

```
passing tests: 1304 (floor 1295)
  0    openapi-types
  0    loader-floor
  0    build
  0    unit-tests
  0    test-floors
=> passed
```
