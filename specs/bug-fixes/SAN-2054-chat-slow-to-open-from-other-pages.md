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

## Follow-up (2026-10-27) — 17 s main-thread freeze from the emoji picker

**Report.** After the fixes above were deployed to dev (frontend PR #1966, backend PR #2052; the served chunks contain `takePrefetchedMessages`), chat was still slow:
- on a hard refresh of `/chat/conversations/:uuid`;
- when opening it from the sidebar "Messages" button;
- when opening it from a connection's chat icon.

The APIs themselves were fast (messages 53 ms, list 156 ms).

**Evidence.** A Chrome Performance trace of a hard refresh on thub.sanchidev.in (`Trace-20261027T110430.json.gz`):
- JS was loaded by about 0.7 s, and the list and messages requests were sent at about 1.0 s.
- At 1108 ms one main-thread task ran for **17,256 ms**, inside `ScConversationsComponent.getConversationsList()` → `detectChanges()`.
- The list, the socket polls and `mark-read` only *finished* at about 18.4 s because the thread was blocked. The server was not slow.
- CPU profile of that task:
  - 55% `getImageData` in the `emojiFallback` pipe (`supportsEmoji()`);
  - 35% `parseFromString` / `getInertBodyElement` (Angular `[innerHTML]` sanitising, about 2,415 inert documents);
  - both are under the `emoji-button` template.

**Root cause.** `ngx-emoji-picker` 0.1.6:
- `EmojiPickerApiDirective`'s constructor calls `initPicker()`. That builds the whole `EmojiPickerComponent` (every emoji as an `emoji-button`) as soon as `[(emojiPickerIf)]` renders, then only shows or hides it.
- Each button creates a canvas, draws the emoji and reads back a pixel to test emoji support, then sanitises its `innerHTML`.
- `chat-message-form` renders with the chat page, so every chat open or refresh paid this cost. The library is the same version as before; the cost was always there, hidden behind the slow APIs until they were fixed.

**Fix (sc-saas-frontend, `8dd06de39`, `chat-message-form.component.{html,ts,spec.ts}`).**
- The 😄 button is a plain `<span>` until it is first clicked.
- `openEmojiPicker()` then sets `emojiPickerMounted = true` and `toggled = true`, so the directive mounts already open. From then on it behaves as before.
- The first click is marked `emojiPickerExempt`, which the picker's `document:click` close handler ignores. Without it, the mounting click would close the picker straight away.
- The cost is now paid only on the first open of the picker, not on every page render. `emojiPickerIf` is used nowhere else in the app.

**Verification.**
- `bash scripts/gates.sh build`: exit 0.
- `bash scripts/gates.sh unit-tests`: 1328/1328 SUCCESS, including 2 new specs (not mounted before the click; mounts and opens on the first click, with the click exempt).
- Not done: no manual browser check of the picker and no new trace after deploy. To check after deploy: 😄 opens the picker, an outside click closes it, and selecting an emoji inserts it.

**Other dev-server findings (not code; for infra / Nirmal, no issue filed).** thub.sanchidev.in:
- serves JS without gzip/brotli (`vendor.js` 3.6 MB raw);
- sends `Cache-Control: no-cache, no-store` on content-hashed files;
- speaks HTTP/1.1 only (ALPN) on both the frontend and the API;
- runs Angular in dev mode (`production:false`). `docs/DEPLOYMENT.md`'s `--configuration devserver` does not exist in `angular.json`.

These are minor next to the freeze.
