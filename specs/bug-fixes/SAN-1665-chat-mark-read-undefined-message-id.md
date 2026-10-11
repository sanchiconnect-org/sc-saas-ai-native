# SAN-1665 — chat `markRead` PATCHes `messages/undefined/mark-read`

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1665 (Sentry SC-SAAS-FRONTEND-2J newest events, and 72)
- **Repo:** sc-saas-frontend · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR

## Problem
`Http failure response for .../chat/conversation/<uuid>/messages/undefined/mark-read: 400`, unhandled, reported by Angular's error handler (2J: 1,038 users, 2,683 events,
newest events today on community.ginserv.in; 72: thub).

## Root cause
`ScConversationsComponent.markRead()` (`src/app/modules/chat/pages/sc-conversations/sc-conversations.component.ts`) built the URL from `this.selectedMessages[0].uuid` and
called `.subscribe()` with no error handler. A socket-pushed or not-yet-persisted first message has no `uuid`, so the backend answered 400. The method also zeroed the local unread
count even though nothing was marked.

## Fix
Return early when `selectedMessages[0]?.uuid` is missing (so the unread count is left alone), and subscribe with an empty error callback so a failed mark-read, a background
call, cannot surface as an uncaught error. No change when the uuid exists.

## Caveat
SC-SAAS-FRONTEND-2J is a catch-all group for unhandled `Http failure response ... OK` errors across endpoints (it earlier showed `connections/requests/received` and
`mentorship/stats` 401s). This fixes the chat mark-read source of its newest events; other endpoints can still appear under it, and it reopens if so.

## Contract impact
None. The backend route and its 400 are unchanged; the client now does not send the malformed request. No flag, tenancy or auth change.

## Verification
`tsc --noEmit` and `ngc` exit 0. No automated test added (no spec exists for this component). Not checked in a browser.

## Commit
sc-saas-frontend `b5d287055` on `ai_native_setup_aman`. Not deployed.
