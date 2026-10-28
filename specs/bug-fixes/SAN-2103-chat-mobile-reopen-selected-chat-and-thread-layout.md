# SAN-2103 — Chat on mobile: selected chat won't reopen; thread squeezed to 40%; thread panel has no spacing

- **Linear:** [SAN-2103](https://linear.app/sanchiconnect/issue/SAN-2103) (Repo: Frontend). Medium, assignee Vishali. Milestone: Enhancement → In-house chat speed up. Follow-up to [SAN-2102](https://linear.app/sanchiconnect/issue/SAN-2102).
- **Classification:** mobile UI/layout plus one navigation bug. All changes are in sc-saas-frontend; there is no API, flag or tenant-scoping impact.
- **Branch:** `ai_native_setup_vishali`. Commit: `76f4ebb24`.
- **Status:** Done in Linear (2026-10-27). Not yet merged into `ai_native_setup` or deployed.

## Problem

Seen locally in Chrome device mode, iPhone 16 (393×852):
1. **Selected chat won't reopen.** After going back to the conversation list (☰), tapping the highlighted (current) conversation did nothing; the list stayed on screen.
2. **Thread squeezed.** Opening a thread kept the desktop 60/40 split, leaving both the chat and the thread about 200px wide.
3. **No spacing in the thread panel.** "Thread / name" sat flush against the left edge, the close ✕ was a tiny target, and replies had no side gutter.

## Root cause

1. **The list only closes on a route change.** `sc-conversations` sets `sidebarOpen = false` only from the `route.params` subscription (via `getSelectedConversation()`). The list item is a plain `routerLink` to `/chat/conversations/<uuid>`. For the current conversation, that URL is already active, so the router does nothing and `sidebarOpen` stays `true`.
2. **No mobile thread layout.** The chat card uses `[ngClass] w-60` and the thread panel uses `w-40`, and both are global `!important` utilities in `styles.scss`. There were no small-screen rules.
3. **Thread header styles.** The thread header used `card-header px-2` and inherited Metronic's card-header layout. The replies wrapper had no padding, whereas the main list wraps messages in `.px-5`.

## Fix (sc-saas-frontend)

- **Reopening the selected chat:**
  - `message-list.component.ts/html`: new `@Output() conversationClick` is emitted from `(click)` on every list item, alongside the existing `routerLink`.
  - `sc-conversations.component.ts/html`: `(conversationClick)="handleConversationClick()"` sets `sidebarOpen = false`.

  On desktop `sidebarOpen` is already `false`, so this is a no-op there.
- **Full-width mobile thread** — `conversation-details.component.{html,scss}`:
  - `.chat-main-wrapper` gets `[class.thread-open]="replyingOn"`.
  - At `max-width: 991.98px`, `#kt_chat_messenger` is hidden and `.thread-panel` is `width: 100% !important` with no left border. `!important` is needed to beat `.w-40` / `.w-60`.
  - `.thread-panel > .card-body` is `flex: 1; overflow: hidden`, so replies scroll inside the panel.
  - `closeThread()` clears `replyingOn`, which brings the chat back.
- **Thread spacing** — the header is restyled as `.thread-header`:
  - padding `0.875rem 1.25rem`, matching the chat header, with a bottom divider;
  - "Thread" in bold, with the name below in small grey text, truncated;
  - `.thread-header-close`: a 34px round close button with `role="button"`, `tabindex`, `aria-label` and Enter support.

  The replies wrapper gets `.thread-messages` (padding `0.5rem 1rem 0`).

## Verification

- `bash scripts/gates.sh build unit-tests` passed: build exit 0, unit-tests 1338/1338 SUCCESS.
- Not done:
  - **No automated tests were added**, because the guardian skill isn't available yet.
  - **No browser check after the final edits.** On dev, check at 393px:
    - go to the list, then tap the selected chat: the chat opens;
    - Reply on a message: the thread opens full width, and ✕ brings back the chat;
    - the thread header and replies have side spacing;
    - at ≥992px the thread is still a 40% side panel.

## Open

- On mobile, the site-wide floating chat button (bottom-right) covers the thread's and the chat's send buttons. It is a separate global widget and was not changed here; it needs its own issue if it should move or hide on `/chat`.
