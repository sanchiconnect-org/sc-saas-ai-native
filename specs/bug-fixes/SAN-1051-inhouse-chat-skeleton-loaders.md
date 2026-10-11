---
id: SAN-1051
title: "In-house chat: skeleton loaders for conversation list and message pane + fix misplaced search icon"
type: enhancement
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1051
repos: [frontend]
related: [SAN-1048, SAN-1049]
project: Enhancement (milestone: In-house chat speed up)
commit: sc-saas-frontend@d9b54771 (branch ai_native_setup_vishali, PR #1881; combined with SAN-1048)
created: 2026-09-29
updated: 2026-09-29
---

# SAN-1051 — In-house chat skeleton loaders (frontend)

## Problem
While `/chat/conversations` loads (tenant `chat_type = inhouse`), the page shows only the `ngx-ui-loader` spinner over an empty layout. The message pane has no loading state when a conversation is opened or switched. The search icon in the chat list sits low and on top of the "Search …" placeholder.

## Change
- `pages/sc-conversations/sc-conversations.component.html/.ts`:
  - While `isLoading` is true (from SAN-1048), a skeleton layout shows: a search bar, six conversation rows, a chat header and alternating message bubbles.
  - New `messagesLoading` flag. It is set in `getSelectedConversation()` when a conversation is opened or switched, and cleared in the `finalize` of the page-1 message fetch, so it also clears on error. It is passed to `conversation-details`.
- `pages/sc-conversations/conversation-details/conversation-details.component.html/.ts`: new `@Input() messagesLoading`. Placeholder bubbles replace the message list while it is true. The `#messagesWrapper` scroll element stays in the DOM, so infinite scroll and scroll-position restore are unaffected.
- The skeleton is **not** shown for the refetch after sending a message or for loading older pages, so the chat doesn't flash.
- Styling: CSS-only shimmer (`.sk`, `.sk-line`, `.sk-circle`, `.sk-bubble`) in both components' `.scss`. No new dependency. Animation is off under `prefers-reduced-motion`.
- `ngx-ui-loader` and its start/stop calls are unchanged (requested).
- Search icon, `pages/sc-conversations/message-list/message-list.component.html/.scss`: the theme doesn't apply `top-50 translate-middle-y` / `px-15` here, so the icon sat low and the placeholder wasn't padded. These are replaced with scoped `.chat-search-icon` (absolute, `top: 50%`, `translateY(-50%)`) and `.chat-search-input` (`padding-left: 3rem`).

## Contract impact
None. No API/DTO, feature-flag or tenant-scoping change.

## Verification
- `tsc --noEmit -p tsconfig.app.json` passes.
- Manual: load `/chat/conversations` and expect the list skeleton, then the list. Switching conversations should show the message skeleton, then the messages. Sending a message should not show the skeleton. The search icon should be vertically centred, left of the placeholder.
- No automated test added.
