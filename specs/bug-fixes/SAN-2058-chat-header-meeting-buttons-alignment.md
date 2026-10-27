# SAN-2058 — Chat header meeting buttons misaligned and cramped

- **Linear:** [SAN-2058](https://linear.app/sanchiconnect/issue/SAN-2058) (Repo: Frontend). Improvement, Low, assignee Vishali.
- **Classification:** UI/layout.
- **Branch:** `ai_native_setup_vishali`. Commit: `68f8442b5`.

## Problem

In a group chat, the header's **Setup Instant meeting** / **Schedule meeting** buttons sit on the top edge of the header instead of lining up with the conversation title. The buttons also have almost no side padding.

## Root cause

- The header (`#kt_chat_messenger_header`) is a Bootstrap `card-header`, which stretches its children to full height (`align-items: stretch`).
- The right-hand wrapper (`d-flex justify-content-end`) had no `align-items-center`, so `app-add-meeting-button` sat at its top.
- The buttons used `px-1`, and only the first one had a `me-3` gap.

## Fix (sc-saas-frontend; classes only)

- `conversation-details.component.html`:
  - The header gets `py-3 align-items-lg-center gap-3`. On mobile it still stacks (`flex-column`), now with a gap.
  - The right-hand wrapper gets `align-items-center flex-shrink-0`.
- `add-meeting-button.component.html`:
  - The container gets `align-items-center gap-3`, replacing `me-3` on the first button.
  - Both buttons get `px-4 d-inline-flex align-items-center text-nowrap`, replacing `px-1`.

`app-add-meeting-button` is also used in the CometChat message header (`cometchat-message-header.component.html`), which gets the same button spacing.

## Verification

- The build and unit-test gates passed on the same tree before commit (build exit 0, 1330/1330).
- Not done: not seen rendered in a browser.
- To check after deploy:
  - the group-chat header at desktop and mobile widths;
  - the CometChat header for non-in-house tenants.
