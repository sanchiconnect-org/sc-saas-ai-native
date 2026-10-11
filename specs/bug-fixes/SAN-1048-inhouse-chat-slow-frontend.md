---
id: SAN-1048
title: "In-house chat slow to load — double load on route remount, empty-state flash, scroll request flood, full reload on every socket message"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1048
repos: [frontend]
related: [SAN-1049, SAN-1051]
project: Enhancement (milestone: In-house chat speed up)
commit: sc-saas-frontend@d9b54771 (branch ai_native_setup_vishali, PR #1881; combined with SAN-1051)
created: 2026-09-28
updated: 2026-09-29
---

# SAN-1048 — In-house chat slow to load (frontend)

## Problem
Opening `/chat/conversations` (tenant `chat_type = inhouse`) shows a loader, then "No chats available yet", then a second load. Only after that do the list and messages appear.

## Root cause (CODE_ERROR)
1. `chat-routing.module.ts` had two route configs (`conversations` and `conversations/:userId`) for the same component. `ScConversationsComponent` auto-navigates from the list URL to the first conversation. Because the route config changed, Angular destroyed and re-created the component, so the conversation list was fetched **twice** before messages loaded.
2. The empty state was shown whenever `conversations.length === 0`, including while loading.
3. `MessageListComponent.onScroll` never updated `lastScrollTop`, so every scroll event fired a "load more" request.
4. Every `MESSAGE_NOTIFICATION_RECEIVED` socket event reloaded the list. That went through `getSelectedConversation()`, which left and rejoined the socket room, refetched all messages and marked them read again.

## Fix
- `modules/chat/chat-routing.module.ts`: one route using `conversationsMatcher`, which matches `conversations` and `conversations/:userId`. The component is reused and only the `userId` param changes.
- `pages/sc-conversations/sc-conversations.component.ts`:
  - new `isLoading` flag, cleared on the first response.
  - loader stop moved from `complete` to `finalize`, so the loader also clears on error.
  - `loadingMore` in-flight guard on `loadMoreConversations()`.
  - `getSelectedConversation()` returns early when the conversation is already open (only refreshes the reference).
  - auto-select navigation uses `replaceUrl`.
  - `markRead()` guards against an empty message list.
  - route-param subscription is now `takeUntil(destroyed$)`.
- `pages/sc-conversations/sc-conversations.component.html`: empty state only when `!isLoading`.
- `pages/sc-conversations/message-list/message-list.component.ts`: `onScroll` tracks `lastScrollTop` and emits only when scrolling down within 100px of the bottom.

## Regression review (flows the old refetch was hiding)
Before this fix, every notification refetched the open conversation's messages, which hid two other bugs. With the refetch gone, both are fixed explicitly:
- `core/service/socket.service.ts`: `listenTOChatRooms()` kept only the last of its three `fromEvent` subscriptions in `chatSub`, so the `message_received` and `reply_message_received` listeners leaked on every room join. That caused duplicate pushes after switching conversations. It now keeps all of them in `chatSubs[]`, cleared on leave and before re-subscribing. The module spec was updated.
- `sc-conversations.component.ts` `MESSAGE_RECEIVED` handler: skips a message whose `uuid` is already shown, and applies the same `\n` → `<br>` conversion `getConversationMessages()` uses. Without that, a multi-line message pushed to the recipient would show on one line.
- Checked, unchanged: every entry link (`/chat/conversations` and `/chat/conversations/<uuid>` from the header, connections, dashboards, calendar and connect-button) still matches through `conversationsMatcher`. The sender still refetches page 1 after send or upload. File messages already arrive over the socket with a signed URL (`uploadFile` signs before `emitToRoom`). Avatar and name edits refresh the header through the updated reference.

## Follow-up: older messages not loading on the first scroll up (2026-09-28)
**Root cause:** in `conversation-details.component.html` the `infiniteScroll` directive sat on an inner div, with `[infiniteScrollContainer]="messagesWrapperRef?.nativeElement"`. That `@ViewChild` lives inside `*ngIf="profileDetails"`, so it is still `undefined` when ngx-infinite-scroll 13.0.2 first sets up.
- With its default `scrollWindow = true`, the directive attached to `window`. It re-attached to the pane on a later `ngOnChanges`, with a fresh scroll state (`lastScrollPosition = 0`).
- The programmatic scroll-to-bottom could therefore go unseen, and the user's first upward scroll was read as scrolling *down*, so `scrolledUp` never fired.
- The distance was also set on the wrong side: `[infiniteScrollDistance]` is the *down* distance, but only `(scrolledUp)` is handled.
- A first page that didn't fill the pane had no scrollbar, so it could never ask for page 2.
- After a page was prepended, the view stayed pinned at `scrollTop = 0`, and a further scroll up from there can't fire.

**Fix (`pages/sc-conversations/conversation-details/`):**
- Template: `infiniteScroll` moved onto the scrolling `.chat-wrapper` element itself with `[scrollWindow]="false"`. The container input was dropped, and `[infiniteScrollUpDistance]="2"` replaces the down distance.
- Component:
  - `loadOlderMessages()` records `scrollHeight`/`scrollTop` before requesting the next page.
  - When `selectedMessages` changes, `ngOnChanges` → `afterMessagesRendered()` restores the offset for pages > 1, so the previously visible message stays in place.
  - If the pane doesn't overflow and more pages exist, it requests the next page directly.
  - Pending scroll state is cleared when the conversation changes.

**Guard (2026-09-29):** the next page is fetched automatically only when the pane is visible (`el.clientHeight > 0`). When the pane is hidden (`d-none` on screens under 1000px) or not laid out yet, `scrollHeight` and `clientHeight` are both `0`, so `0 <= 0` would pull every page of history.

**Unchanged:** the parent's scroll-to-bottom for page 1 (initial load and after send) still runs; restoring only applies to pages > 1. There is no API/DTO change. The `.chat-wrapper` class used by the parent is still on the same element.

## Verification
- `tsc --noEmit -p tsconfig.app.json` passes; `ng build --configuration local` (see Linear comment).
- No automated regression test added (proposed, pending go-ahead).
- Manual check: open `/chat/conversations`. Expect a single list request, no "No chats" flash, one messages request, no request storm when scrolling the list, and no messages refetch when a notification arrives.
