# SAN-1768 / SAN-1769 — Bell panel lists only connection requests

- **Linear:** SAN-1768 (Repo: Backend), SAN-1769 (Repo: Frontend) — Bug, Medium, assignee Mahima Sharma
- **Related:** SAN-1765 / SAN-1766 (job-application rows, committed in d9e75a20)
- **Classification:** CODE_ERROR (plus meetings added to the bell at the user's request, 2026-10-07)

## Problem
The bell count went up for new programs, new events, new wall posts and new job applications, but the panel only ever listed connection requests.

## Root cause
`counters.bell` is derived live from source tables: connections + wall posts since the last visit + unviewed job applications + (mode B) new programs/challenges/events. The panel list is `GET notifications`, which reads only the `notifications` table, and only connection requests (and since SAN-1765, job applications) write rows there. Programs and challenges are also created from `sc-saas-admin` (PHP), so writing rows at creation time would miss them. New meetings weren't counted at all.

## Fix
Backend (`sc-saas-backend`):
- `notifications/repositories/notification-counters.repository.ts`:
  - `getWallPostsSince()` uses the same WHERE as `countWallPostsSince`, newest first, with a limit.
  - `getNewMeetingsSince()` returns meetings someone else set up with the user since the previous login, excluding rejected, cancelled and completed ones.
- `notifications/notification-counters.service.ts`:
  - `getCounters` now wraps a shared private `load()`.
  - `counters.meetings` is new, and the bell adds it.
  - New `getLiveFeed()` builds items from the same rows: mode-B fresh programs/challenges/events, wall posts (only if not muted), and meetings. They're sorted newest first, max 20.
- `notifications/notifications.controller.ts`: `GET notifications` merges the live items into page 1 when the notification centre is on.
  - Each live item is marked `isLive: true`, `category: new`, with uuid `live:<type>:<uuid>`.
  - Each `url` matches the sidebar badge's page: `/call-for-applications`, `/search/challenges`, `/calender/events`, `/community-feed`, `/calender`.
  - With the flag off, the response is unchanged.
- Specs: added the new repository methods to the mocks in the counters, isolation and timezone specs.

Frontend (`sc-saas-frontend`):
- `notifications.enum.ts` — `live_*` types.
- `notifications.component.ts` — icons and CTAs. It no longer calls mark-read for live items.
- `notification-bell.component.ts` — no mark-read for live items.
- `notifications.model.ts` — optional `meetings` counter.

## Behaviour notes
- A live item leaves the list the same way its count drops:
  - programs/challenges/events once opened or applied to;
  - wall posts once the wall is visited;
  - meetings once the next login moves "previous login" forward.
- "Mark all as read" doesn't remove live items. They come back unread on the next fetch until the item is opened or the section visited.
- Job applications stay on SAN-1765 rows, so they aren't duplicated. Applications made before that deploy have no row.
- Meetings aren't gated by a module flag and can't be muted. No in-app category exists for them.

## Verification
- Backend: `tsc --noEmit` clean apart from one existing unrelated error (`@aws-sdk/client-sesv2`). ESLint: no errors on the touched files. Jest `src/modules/notifications` + `src/modules/job`: 7 suites, 104 tests pass.
- Frontend: `tsc --noEmit -p tsconfig.app.json` clean.
- No new test asserts the live feed or meetings in the bell (proposed, waiting for go-ahead). Not exercised against a running backend.

## Commit
_pending — Mahima commits_
