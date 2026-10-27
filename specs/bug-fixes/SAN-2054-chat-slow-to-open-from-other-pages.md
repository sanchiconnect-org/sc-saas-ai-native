# SAN-2054 — Chat takes long to open from other pages

- **Linear:** [SAN-2054](https://linear.app/sanchiconnect/issue/SAN-2054) (Repo: Frontend). Improvement, Medium, assignee Vishali. Follow-up to SAN-2042 / SAN-2053 ([list record](SAN-2041-SAN-2042-chat-conversation-list-slow.md), [messages record](SAN-2052-SAN-2053-chat-messages-slow.md)).
- **Classification:** CODE_ERROR (performance).
- **Branch:** `ai_native_setup_vishali`. Commits: `56b1ba06c` and `9d25a0310`. The second only restores the header file's CRLF line endings, so read the change as `git diff 56b1ba06c~1 9d25a0310`.

## Problem

Opening a chat from anywhere is slow. This covers every `/chat/conversations/:uuid` link: Connections "Message", the dashboard sidebar, meeting details, notifications and the header icon.

## Root cause

Everything ran back to back:
1. the lazy `chat` chunk (~31 kB transfer) downloaded on first use;
2. the chat page started;
3. the conversation list API ran;
4. the messages API ran (since SAN-2053, in parallel with the list, but only after the page was up);
5. nothing rendered until the list returned.

## Fix (sc-saas-frontend)

- `protected-layout-header.component.ts`:
  - On `NavigationStart` to `/chat/conversations[/:uuid]`, only for in-house chat, it calls `prefetchConversations()` (skipped when already in chat) and `prefetchMessages(uuid)`. These overlap the chunk load and the page start-up.
  - The idle prefetch also preloads the chat chunk, which is the same chunk the router loads (the build still emits one chunk).
- `conversation.service.ts`:
  - The list prefetch is kept as a shared in-flight observable (`getInFlightConversations()`).
  - A one-shot messages prefetch, per profile and kept 30 s (`prefetchMessages()` / `takePrefetchedMessages()`).
- `sc-conversations.component.ts`:
  - Joins both requests, falling back to a normal fetch on error.
  - The SAN-2053 component-local early fetch now goes through the service.

## Verification

- `tsc --noEmit -p tsconfig.app.json` exit 0.
- Chat page and service specs: 16 SUCCESS. Header spec: 4 SUCCESS.
- `npm run gates` passed: 1326 unit tests (floor 1295).
- Not done: no manual browser check.

## Known gaps

- Existing behaviour, not fixed: a conversation older than the newest 20 is not in page 1 of the list, so opening it from Connections shows "Conversation not found" and redirects. Fixing it needs a single-conversation endpoint (API contract change) or page-through logic. It needs its own issue.
- A message arriving between the prefetch and joining the room (≤30 s) can be missing until the next refresh.
