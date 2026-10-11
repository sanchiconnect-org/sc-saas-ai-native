---
id: SAN-1049
title: "In-house chat API slow — N+1 member/admin profile lookups in getConversations, sequential signed URLs, per-message markRead updates"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1049
repos: [backend]
related: [SAN-1048, SAN-1051]
project: Enhancement (milestone: In-house chat speed up)
commit: sc-saas-backend@5d16e541 (branch ai_native_setup_vishali)
created: 2026-09-28
updated: 2026-09-29
---

# SAN-1049 — In-house chat API slow (backend)

## Problem
`GET api/v1/chat/conversation` and `GET api/v1/chat/conversation/:uuid/messages` respond slowly, which makes the in-house chat UI slow.

## Root cause (CODE_ERROR) — `src/modules/chat/chat.service.ts`
1. `getConversations` awaited `getUsersBasicInfoWithProfile` twice per conversation (members + admins), one after another. Each call is a `UserEntity.find` joining 8 profile relations, so a page of 20 took about 40 heavy queries.
2. `getConversationMessages` awaited `uploadService.getSignedURl` for each FILE message in turn.
3. `markMessageAsRead` fired one un-awaited UPDATE per unread message. The surrounding try/catch couldn't catch their rejections.

## Fix
- `chat.service.ts` `getConversations`: collects all member and admin IDs on the page, makes one `getUsersBasicInfoWithProfile` call, and picks each conversation's users from that shared list. Filtering the shared list keeps the old order and dedup behaviour. The response shape is unchanged, so there is **no API contract change**.
- `chat.service.ts` `getConversationMessages`: per-message processing runs through `Promise.all`, so signed URLs are generated concurrently.
- `chat-messages.repository.ts`: new `markMessagesReadByUser(ids, userId)`, a single `UPDATE ... SET read_by_user_ids = JSON_ARRAY_APPEND(COALESCE(read_by_user_ids, JSON_ARRAY()), '$', userId) WHERE id IN (...)`. `markMessageAsRead` awaits it and logs failures via `this.logger.error`.

## Out of scope
The `JSON_CONTAINS` scans (`readByUserIds` for unread counts, `members` for group membership) can't use an index. Replacing them with a per-member last-read pointer needs a migration and should get its own spec.

## Verification
- Bulk mark-read SQL was checked read-only (`SELECT` only) on the dev DB (MySQL 8.4.11). SQL NULL → `[7]`, JSON `null` → `[7]`, `[3,5]` → `[3,5,7]`. This matches the old per-row push. The final expression is `CASE WHEN JSON_TYPE(col)='ARRAY' THEN JSON_ARRAY_APPEND(...) ELSE JSON_ARRAY(id) END`.
- All 763 `chat_conversations` rows on dev store `members`/`admins` as JSON integers, so the batched lookup matches exactly. IDs are also passed through `Number()` as a safety net.
- `tsc --noEmit` passes. ESLint on the touched files reports only warnings that were already there (plus CRLF noise from the Windows checkout).
- No automated regression test added (proposed, pending go-ahead).
- Manual check: conversation list and messages return the same payload as before, faster; unread badges clear after opening a conversation.
