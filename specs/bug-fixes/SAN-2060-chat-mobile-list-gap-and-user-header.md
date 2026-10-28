# SAN-2060 — Chat on mobile: list touches the screen edges, one-to-one header is right-aligned

- **Linear:** [SAN-2060](https://linear.app/sanchiconnect/issue/SAN-2060) (Repo: Frontend). Improvement, Low, assignee Vishali.
- **Classification:** UI/layout (mobile).
- **Branch:** `ai_native_setup_vishali`. Commit: `96d1a4d9f`.

## Problem

In-house chat on a phone (thub.sanchidev.in):

1. **Chat list.** The "Chats" heading, the search box and every conversation row (avatar, name) sit about 4px from the left and right screen edges.
2. **One-to-one chat header** (e.g. Baltej Singh). The avatar and name sit at the right of the header. Group chats show them on the left.

## Root cause

1. `sc-conversations.component.html` wraps the page in a `.container` with `padding: 0 !important` and a Bootstrap `.row`. The row's negative gutter (−12px each side) is no longer cancelled by container padding, so it pulls the content outward. The list header (`#kt_chat_contacts_header`) and the rows (`.chat-item`) have `px-4` (16px), which leaves about 4px visible.
2. In `conversation-details.component.html`, the user-chat `card-title` had `justify-content-end`.
   - On mobile the header is `flex-column`, so its left block stretches to the full width and the title is pushed right.
   - On desktop (`flex-lg-row`) the block shrink-wraps, which is why it never showed there.

## Fix (sc-saas-frontend; classes only)

- `message-list.component.html`: the list header and each chat row use `px-7 px-lg-4`.
  - Mobile: 28px of padding, about 16px visible after the gutter.
  - Desktop: unchanged.
- `conversation-details.component.html`: the user-chat `card-title` uses `justify-content-start align-items-center`, the same as the group header.

The page-level fix would be `g-0` on the `.row`, but that also moves the desktop layout by 12px. It was left out to keep this change mobile-only.

## Verification

- `bash scripts/gates.sh build`: exit 0.
- Not done: not yet seen on a phone or in a mobile emulator.
- To check after deploy at phone width:
  - the chat list has an even gap on both sides;
  - a one-to-one chat header shows the avatar and name on the left;
  - desktop is unchanged.

## Correction (2026-10-27) — desktop padding regression, fixed in SAN-2062

`px-lg-4` is not in the app's compiled CSS, which ships only a subset of Bootstrap utilities. So `px-7 px-lg-4` applied 28px of padding on **desktop** too, and the "desktop unchanged" claim above was wrong.

Fixed in `305c121e9` ([SAN-2062](SAN-2062-group-chat-meeting-buttons-wrap-on-desktop.md)):
- the list header and rows are back to `px-4`;
- a new `.chat-list-gutter` class in `message-list.component.scss` sets `padding: 0 1.75rem` only at `max-width: 991.98px`.

The one-to-one header change (`justify-content-start align-items-center`) was fine: both classes exist.
