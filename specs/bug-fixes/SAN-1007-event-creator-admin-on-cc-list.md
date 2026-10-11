---
id: SAN-1007
title: Copy the admin who created a 1:1 event on every email that goes to its CC list
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1007
repos: [backend, admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1007 — the event's creator admin is copied wherever the CC list is

## Request

"All mails which go to the CC mail also go to the admin who created that event."

## Investigation finding

There's no record of who created an event:
- the `events` table has no creator/owner-admin column;
- `sc-saas-admin/modules/events/list.php` `createEvent` inserts only uuid, title, status, publish flags
  and dates;
- `spa_admin_logs` records event publish/delete/archive, but never event creation.

So the creator has to be recorded from now on.

## Decisions (user)

- **Scope:** every email that goes to the CC list, whether an admin or an applicant triggered it.
- **Existing events:** no creator copy. Their creator is unknown, and we won't guess.

## Fix

- **sc-saas-backend**
  - New nullable column `events.created_by_admin_id` (`EventsEntity.createdByAdminId`), created by
    TypeORM `synchronize` on the next boot.
  - Added to `EventsRepository.getEventInformationByUUID()`'s explicit select (cancel event loads the
    event through it; the other paths use `findOne`, which loads every column).
  - In every entry point that emails the CC list, right after the event is loaded, the creator admin's
    email is added (de-duplicated) to `event.ccEmails` **in memory only**. Nothing saves the event back:
    the one `updateByEntity` in cancel event is a partial update. Entry points:
    `events.service.ts` approve, reschedule, reject, cancel event, remove attendee (reversal / pending
    reject), attend (Manual acknowledgment, the three alerts, and Automatic-mode booking), withdraw;
    `admin-actions.service.ts` speaker-chosen and event-live.
- **sc-saas-admin**: `list.php` saves `created_by_admin_id = (int) $_SESSION['admin_user_id']` on
  **create** and on **copy** (a copy belongs to the admin who made it). It's null for a non-admin session
  (e.g. partner).

## Resulting recipients

Everything the CC list receives, the creator admin now receives too: speaker chosen, event live,
application received, new application, slot full, withdrawn, accept (meeting scheduled), reject /
auto-reject, reschedule, reversal and cancel event. If the creator is also the admin who did the action,
they get one copy, not two (de-duplicated).

## Verified

- `npx tsc --noEmit` clean; existing ses-email + admin-actions suites pass (5 suites, 40 tests).
- `php -l` clean on `list.php`.
- Not exercised against a live tenant.

## Rollout (load-bearing)

**Deploy sc-saas-backend first.** The column exists only after the backend has booted once. If admin
deploys first, creating or copying an event fails with an unknown-column database error.

## Open questions

None.
