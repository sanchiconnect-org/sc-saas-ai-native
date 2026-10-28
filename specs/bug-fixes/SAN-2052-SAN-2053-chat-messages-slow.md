# SAN-2052 / SAN-2053 — Chat messages slow to load (worst after a hard refresh)

- **Linear:** [SAN-2052](https://linear.app/sanchiconnect/issue/SAN-2052) (Repo: Backend), [SAN-2053](https://linear.app/sanchiconnect/issue/SAN-2053) (Repo: Frontend). Improvement, Medium, assignee Vishali. Follow-ups to SAN-2041 / SAN-2042 ([record](SAN-2041-SAN-2042-chat-conversation-list-slow.md)).
- **Classification:** CODE_ERROR (performance).
- **Branch:** `ai_native_setup_vishali` in both repos. Commits: backend `40db17a3` + `cdc45519` (lint fix, below), frontend `6838288ec`. Merged to `ai_native_setup` (backend PR #2052).
- **Still slow after a hard refresh?** The main cause was the emoji picker, not this API. See [SAN-2054 follow-up](SAN-2054-chat-slow-to-open-from-other-pages.md#follow-up-2026-10-27--17-s-main-thread-freeze-from-the-emoji-picker).

## Problem

`GET api/v1/chat/conversation/:uuid/messages?page=1` (dev: `api.thub.sanchidev.in`) is slow, most of all after a hard refresh of `/chat/conversations/:uuid`.

## Root cause (from reading the code, not profiled against the DB)

**Backend**, `ChatService.getConversationMessages()` → `ChatMessagesRepository.getConversationMessages()`:
1. The user was loaded with all 8 profile relations (only `user.id` is used), and the conversation was looked up only after that.
2. `chat_conversations.uuid` had no index, so `findOne({ uuid })` scanned the table. Every chat route does this lookup.
3. `WHERE conversation_id = ? ORDER BY created_at DESC` had only the FK index on `conversation_id`, so MySQL sorted every message of the conversation.
4. `paginate()`'s count was `COUNT(*) FROM (<full SELECT joined to users>)` over all of the conversation's messages.

File messages get S3 signed URLs, but signing is local (aws-sdk `getSignedUrl`, no network call), so it isn't a cost.

**Frontend:** on a hard refresh, `ScConversationsComponent` requested the messages only once the conversation list had returned, so the two slow calls ran back to back.

## Fix

**Backend (SAN-2052)**
- `chat.service.ts`: `getUserIdOnlyById()` in parallel with `getChatConversationByUUID()`. The membership check is unchanged.
- `chat-messages.repository.ts`: LIMIT/OFFSET page plus a lean count (no `users` join, `withDeleted` as before), in parallel, returning the same `Pagination` shape.
- `chat-conversations.entity.ts` / `chat-messages.entity.ts`: `@Index('IDX_chat_conversations_uuid', ['uuid'])`, `@Index('IDX_chat_messages_conversation_created', ['conversationId', 'createdAt'])`.
- Migration `src/core/database/migrations/1793075221055-ChatLookupIndexes.ts`.
- Spec `chat-messages.repository.spec.ts`.

**Frontend (SAN-2053)**
- `sc-conversations.component.ts`: `startEarlyMessagesFetch()` starts page 1 of the URL's conversation as the route resolves, only while no list is loaded. `getConversationMessages()` reuses it for the same uuid and falls back to a normal fetch if it failed.
- `conversation.service.ts`: `getMessage(id, page, silent = false)`.
- Spec block "early messages fetch (SAN-2053)" in `sc-conversations.component.spec.ts`.

## Verification

- Backend: `tsc --noEmit` exit 0. `jest src/modules/chat`: 5 passed. `npm run gates`: test (1709 passed, 23 skipped), test-floors, openapi-floors, build and unguarded-routes all exit 0. Lint locally showed only CRLF noise (`Delete ␍`), but that hid one real prettier error: the `@Index('IDX_chat_messages_conversation_created', [...])` line in `chat-messages.entity.ts` was too long. CI's lint gate failed with exit 123 on PR #2052, and `cdc45519` wraps the line. To spot real errors locally, run `bash scripts/gates.sh lint 2>&1 | grep -v 'Delete ␍'`.
- Frontend: `tsc` exit 0. Chat specs 11 SUCCESS. `npm run gates` passed (1319 unit tests, floor 1295).
- Not done: the `migrations` CI workflow (needs MySQL 8) wasn't run locally. No latency measured before/after. No manual browser check.
