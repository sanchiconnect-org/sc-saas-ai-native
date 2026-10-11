# SAN-1835: Chat on mobile is slow to load and goes back to the conversation list while typing

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1835
- **Repo:** sc-saas-frontend
- **Assignee:** Mahima Sharma
- **Priority:** High

## Problem
On `demo.sanchiapp.com`, which uses `chat_type: inhouse`:
1. On mobile, the chat page shows the skeleton and spinner for a long time before it loads.
2. While the user types a message, the page suddenly goes back to the conversation list. This only happens on mobile.

## Root cause
1. **Goes back while typing (CODE_ERROR).** `ScConversationsComponent` re-ran `checkWindowSize()` on every `window:resize` event. On screens narrower than 1000px, that sets `sidebarOpen = true`, which hides the open conversation (`d-none`) and shows the conversation list. On mobile, the window resizes whenever the keyboard opens or closes, and when the address bar shows or hides. So typing triggered the jump back to the list.
2. **Slow load (partly CODE_ERROR).** There are two causes:
   - The `chats-wrapper` template rendered `<app-conversations>` (CometChat) when `chat_type !== 'inhouse'`. That condition is also true while `brandDetails` is still `undefined`, so CometChat could start (spinner, SDK init) before the in-house chat. This is fixed.
   - The lazy `chat` chunk bundles the whole CometChat UI kit and SDK. In the dev build, about 1.7 MB of source in that chunk is CometChat (UI kit 571 KB, `@ctrl` emoji-mart 797 KB, `@cometchat-pro/chat` 323 KB). In-house chat needs only about 180 KB. Every in-house tenant still downloads all of it, which hurts on mobile networks. This is **not fixed yet**: moving CometChat into its own lazy module is a separate refactor.
   - Backend API latency (`GET chat/conversation` followed by `.../messages`) has not been measured on a device yet.

## Fix (files changed)
- `src/app/modules/chat/pages/sc-conversations/sc-conversations.component.ts`: the resize handler now changes the layout only when the width crosses the 1000px breakpoint. Height-only resizes (keyboard, address bar) are ignored.
- `src/app/modules/chat/pages/chats-wrapper/chats-wrapper.component.html`: nothing renders until `brandDetails.features` is loaded, then exactly one chat implementation renders.

## Verification
- `ng build --configuration development` passes.
- Not tested on a real device yet. No automated regression test added yet; one is proposed and waiting for approval.

## Commit
Not committed yet.
