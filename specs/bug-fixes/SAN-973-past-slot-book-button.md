---
id: SAN-973
title: 1:1 event slot modal shows Book on slots whose time has already passed today
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-973
repos: [frontend]
assignee: Mahima Sharma
created: 2026-09-24
updated: 2026-09-24
---

# SAN-973 — no Book button on a 1:1 slot whose start time has passed

## Problem

In the 1:1 event details modal ("Book your slot"), today's slots that had already started still showed an enabled **Book** button. Reported with a screenshot: an event on Sep 24, 10:00–11:00 AM slots, viewed after 11 AM.

## Classification

CODE_ERROR.

## Root cause

`EventDetailsOneOnOneModalComponent.getSlotView()` picks each slot row's state (mine-pending/approved/rejected → not-eligible → limit-locked → full → open) but had no time check. The backend listing already sets `slot.canApply = false` for today's past slots (`sc-saas-backend/src/modules/events/events.service.ts`), but the frontend never read that field.

## Fix (sc-saas-frontend)

`src/app/shared/common-components/event-details-one-on-one-modal/`:
- `.component.ts`: new `isSlotInPast(slot, date)`. It compares the slot start (date + `timeFrom`) against now in the event's timezone (`Asia/Kolkata`), anchored the same way as `formatSlotTime()`. `getSlotView()` returns a new `past` state right after the startup's own-application states, so a startup's own Applied/Approved/Rejected row still shows on a past slot. `handleBook()` also refuses a past slot, for the case where the modal stays open past the slot's start time.
- `.component.html`: new `past` row with the time range and a "Time passed" badge, and no Book button.

## Not changed

- `public-events.component.html` also lists slots, but its Book button has no click handler (commented out), so it can't book anything.
- The backend booking write path (`attendEvent`) doesn't reject a past slot by itself. This is a separate backend gap and not part of this frontend-only issue.

## Verification

- `tsc --noEmit -p tsconfig.app.json` clean.
- The Karma suite can't compile because of old spec errors, so no automated tests ran. The repo has no lint setup.
- Manual check in the browser not done yet.

## Commit

Pending (not committed).
