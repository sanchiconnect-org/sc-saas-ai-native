---
id: SAN-2117
title: "calendar-availability status-0 rejection is an uncaught promise in the meeting modals"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2117
sentry: [SC-SAAS-FRONTEND-2V]
repos: [frontend]
related: [SAN-2032, SAN-1930]
commit: frontend@ef99df15e (branch ai_native_setup_vishali, pushed)
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2117: awaited availability fetch with no catch

## Root cause
* 2V: 11 events / 11 users, regressed, prod sineedge on release `218edca78`. Nothing has touched these call sites since that release, so this is not deploy lag.
* `getMeetingAvailability()` does `await meetingService.getUsersAvailabilityById(uid).toPromise()` with no catch, and its callers are `async` subscribe callbacks. A status-0 failure becomes an unhandled rejection and stops the caller; in edit-meeting-event, `meetingForm` was never built.

## Fix
try/catch in three components. On failure: `this.calenderAvilablity = {} as IMeetingAvailability; return;`. The cast fixes a TS2739 that a bare `{}` raised.
* `shared/common-components/accept-connection-modal/accept-connection-modal.component.ts:176`
* `shared/common-components/add-meeting-button/add-meeting-modal/add-meeting-modal.component.ts:210`
* `modules/calender/calender-component/edit-meeting-event/edit-meeting-event.component.ts:172`

Facility-booking availability uses a different endpoint and is out of scope.

## Blast radius / existing-flow impact
Frontend only. Success path unchanged. On failure the modal still opens, with no availability restriction, instead of breaking.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → 0 (all 3 files confirmed via `--listFiles`); `npm run gates` → all 5 gates 0 (1338/1338)
* Manual: block `meetings/users/calendar-availability/*` and open each modal.
