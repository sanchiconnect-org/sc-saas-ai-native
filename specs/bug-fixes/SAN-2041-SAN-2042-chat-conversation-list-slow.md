# SAN-2041 / SAN-2042 — Chat conversation list is slow to open

- **Linear:** [SAN-2041](https://linear.app/sanchiconnect/issue/SAN-2041) (Repo: Backend), [SAN-2042](https://linear.app/sanchiconnect/issue/SAN-2042) (Repo: Frontend). Improvement, Medium, assignee Vishali.
- **Classification:** CODE_ERROR (performance).
- **Branch:** `ai_native_setup_vishali` in both repos. Commits: backend `4af9843c`, frontend `96edea717`.

## Problem

`GET api/v1/chat/conversation?page=1&limit=20` (dev: `api.thub.sanchidev.in`) is slow. The in-house chat page waits on it with a full-screen loader every time it opens.

## Root cause (from reading the code, not profiled against the DB)

`ChatService.getConversations()` → `ChatConversationRepository.getConversations()`:

1. `getUserById()` loaded the requesting user with all 8 profile relations, but only `user.id` was used.
2. `getUserBasicInfoWithProfileByIds()` loaded **every column** of 8 profile tables (startup, investor, corporate, mentor, service_provider, partner, program_office, individual) for every member of every conversation on the page. Group chats can hold whole organisations, so this was the heaviest part.
3. `paginate()` ran its count as `SELECT COUNT(*) FROM (<full joined SELECT with lastMessage>)`, which builds a derived table of every matching conversation.
4. Not fixed (needs a schema change, out of scope): the `OR … JSON_CONTAINS(members)` filter forces a full scan of `chat_conversations`, and the unread count evaluates `JSON_CONTAINS(read_by_user_ids)` on every message of the page's conversations. Indexes don't help either of these. The real fix is a per-user read pointer (`last_read_message_id`) plus a maintained membership table, which needs `/spec-new`.

## Fix

**Backend (SAN-2041)**
- `src/modules/user/repositories/user.repository.ts`: `getUserBasicInfoWithProfileByIds()` now selects only the columns `getCompanyUUID()` / `getOrganizationNameWithMentorNull()` read. New `getUserIdOnlyById()`.
- `src/modules/chat/chat.service.ts`: `getConversations()` uses `getUserIdOnlyById()`.
- `src/modules/chat/repositories/chat-conversations.repository.ts`: the page query and a lean count query (no `lastMessage` join) run in parallel. The response is built as the same `Pagination` shape (`items`, `meta`, no `links`). The API contract is unchanged.

**Frontend (SAN-2042)**
- `src/app/core/service/conversation.service.ts`: in-memory cache of page 1, keyed by profile UUID. `prefetchConversations()` is silent and deduped, and skips the fetch if the cache is fresh (60 s). A socket `message_notification_received` marks the cache stale.
- `protected-layout-header.component.{ts,html}`: prefetches during idle time (2 s after the profile loads, then `requestIdleCallback`). It only does this when `features.chat` is on, `chat_type === 'inhouse'`, and the account type can see the chat icon. Hovering the chat icon re-prefetches if the cache is stale.
- `sc-conversations.component.ts`: renders the cached page 1 immediately, with no loader, and revalidates in the background. Every fresh page 1 response refreshes the cache. If the URL's conversation isn't in the cache, it waits for the fresh list, so a newly created chat isn't reported as "not found".

## Verification

- Backend: `tsc --noEmit` exit 0. `jest src/modules/chat src/modules/user`: 4 suites, 14 tests passed. `npm run gates`: test, test-floors, openapi-floors, build and unguarded-routes all exit 0. Lint shows 3127 errors, all `Delete ␍` (CRLF from `core.autocrlf` on this Windows checkout, normalised to LF on commit; an untouched file shows the same). With `endOfLine: auto` it reports 0 errors.
- Frontend: `tsc --noEmit -p tsconfig.app.json` exit 0. `npm run gates` passed (1309 unit tests, floor 1295).
- Regression tests: backend `chat-conversations.repository.spec.ts` (3 passed); frontend `conversation.service.spec.ts` + `sc-conversations.component.spec.ts` SAN-2042 block (8 SUCCESS). Frontend gates rerun after adding them: 1316 SUCCESS.
- Not done: no before/after latency measured against the dev DB, and no manual browser check yet (see the Linear handover notes).
