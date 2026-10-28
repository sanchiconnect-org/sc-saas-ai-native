# SAN-2102 — Clean chat header; header breaks with a thread open; thread carries over on chat switch

- **Linear:** [SAN-2102](https://linear.app/sanchiconnect/issue/SAN-2102) (Repo: Frontend). Medium, assignee Vishali. Milestone: Enhancement → In-house chat speed up. Related: SAN-2062, SAN-2060.
- **Classification:** UI/layout plus one small behaviour fix. All changes are in sc-saas-frontend; there is no API, flag or tenant-scoping impact.
- **Branch:** `ai_native_setup_vishali`. Commit: `944ac969b`.
- **Status:** Done in Linear (2026-10-27). Not yet merged into `ai_native_setup` or deployed.

## Problem

In the in-house chat (`modules/chat/.../conversation-details`):
1. **Cluttered header.** It had a 40px avatar, 20px member circles each with its own online dot, and a grey `btn-light` "Setup Instant meeting" button. The design (screenshots on the issue) calls for:
   - a 48px avatar ring with an edit badge;
   - the name in bold, with an edit pencil;
   - a "● Online" status line next to stacked member avatars;
   - an outlined "Setup Instant meeting" button and a primary "Schedule meeting" button.
2. **Header breaks with a thread open.** The chat card is 60% wide, and the header overflowed it.
3. **Group with no logo.** The initials circle looked offset inside the avatar ring.
4. **Names as stored.** Lowercase names were shown in lowercase.
5. **Plain "Setup Instant meeting" button.** It had no background or border.
6. **Thread carried over.** After switching to another conversation, the previous conversation's thread panel stayed open.

## Root cause

2. **No `min-width: 0`.** `#kt_chat_messenger` is a flex item without `min-width: 0`, so it couldn't shrink below its content. The header pushed past the card instead of fitting.
3. **Size mismatch.** `ngx-avatars` was rendered at size 48 inside a ring whose inner size is 40px (48 minus 3px padding and 1px border per side). Its `line-height` follows `size`, so stretching it with CSS also misplaces the initials.
5. **Metronic reset.** Metronic's `.btn:not(.btn-outline):not(...)` reset has higher specificity than the component's selectors, so it removed the border and background.
6. **No reset on switch.** `replyingOn` / `replies` were never cleared when the `selectedConversation` input changed.

## Fix (sc-saas-frontend)

- **Header markup and styles** — `conversation-details.component.{html,scss,ts}`:
  - One layout for group and one-to-one chats: `.chat-header-info` (avatar, title, meta) and `.chat-header-actions`.
  - All layout lives in component SCSS, because the compiled CSS ships only a subset of Bootstrap utilities (see SAN-2062).
  - New getters: `isConversationOnline` (true when any member other than me is online), `headerMembers` (first 3) and `extraMemberCount` (+N).
  - Desktop (≥992px): one row with the name truncating. Mobile: the title row, then the buttons.
  - `#kt_chat_messenger { min-width: 0 }`.
  - The old `.card .card-header { align-items: normal !important }` override is removed; it stopped the desktop header from centring.
- **Thread open** — the header gets `.chat-header--compact`. `app-add-meeting-button` gets a new `@Input() compact` (default `false`), which makes both buttons square and icon-only with their labels in tooltips. The CometChat header doesn't pass it, so it keeps full labels.
- **Initials avatar** is rendered at `size="40"`, with no CSS stretching.
- **Names** — `text-capitalize` (present in the compiled CSS) is added to:
  - the conversation list name;
  - the header name;
  - the thread header name;
  - sent and received message authors;
  - the typing-indicator name (only the name, not "is typing").

  It uppercases only the first letter of each word, so "McDonald" is kept. The members modal already uses `| titlecase` and is unchanged.
- **Meeting button** — `add-meeting-button.component.{html,scss}`:
  - `.btn-meeting-outline` uses `#f5f8fa` with a `#e4e6ef` border (`!important`, to beat the Metronic reset), and `#eef0f8` on hover.
  - The icons are now outline style (`bi-camera-video`, `bi-calendar3`).
  - The restyle also shows in the CometChat header.
- **Thread on chat switch** — in `ngOnChanges`, when `selectedConversation.uuid` changes, `closeThread()` runs. `fetchReplies()` now ignores a response whose thread is no longer `replyingOn`. Without that guard, a late response would `unshift(null)` into `replies`.

## Verification

- `bash scripts/gates.sh` (all gates) passed on the first pass: openapi-types, loader-floor, build, unit-tests 1338/1338, and test-floors.
- After the follow-up changes, `build` and `unit-tests` were re-run: exit 0, 1338/1338 SUCCESS.
- The `.text-capitalize` utility was confirmed present in the built `styles.*.css`.
- Not done:
  - **No automated tests were added**, because the guardian skill doesn't exist yet.
  - **No browser check yet.** After deploy, check on dev:
    - a group chat at 1440px with and without a thread open;
    - a group with no logo;
    - a one-to-one chat;
    - the 390px mobile layout;
    - switching chats with a thread open;
    - the CometChat header for non-in-house tenants.

## Follow-up (2026-10-28): long chat names hid the meeting buttons on mobile and tablet

No separate Linear issue; this fixes a layout gap in the header redesign above. Commit: `sc-saas-frontend@51a7dc1e9` on `ai_native_setup_vishali`, pushed.

### Problem

With a long chat name (e.g. "Pilani Innovation Entrepreneurship Development Society (Pieds) - Meity Incubator / Vami Dummy"):
- **Mobile and tablet (<992px):** the header grew past the card. The name didn't truncate, and "Setup Instant meeting" / "Schedule meeting" were pushed off the right edge.
- **iPad Pro (1032px, chat list beside the chat):** the desktop single-row header had no room. The name shrank to "P…" and "Schedule meeting" was cut off. The message area's right edge was clipped as well.

### Root cause

- **Below 992px — Metronic's wrap.** The global `.card-header` sets `flex-wrap: wrap`. In the header's column layout, a wrapping line is as wide as its widest item, so the long `nowrap` name set the header's width. The desktop rule already set `nowrap`, which is why desktop was unaffected.
- **992px and up — no room for one row.** The single-row layout kept the full-label buttons at their natural width (`flex-shrink: 0`), however narrow the card was.
- **Clipped messages.** The header's minimum width (the buttons plus padding) could stretch `.chat-main-wrapper`, which had no `min-width: 0`, past its column. This is the likely cause of the clipped right edge.

### Fix

In `conversation-details.component.scss`:
- **Mobile/tablet header:** `flex-wrap: nowrap` in the base `#kt_chat_messenger_header` rule, so the name truncates and the buttons sit on their own row.
- **Desktop header (≥992px):** `flex-wrap: wrap`, with a 260px `flex-basis` on `.chat-header-info` and `margin-left: auto; max-width: 100%` on `.chat-header-actions`. When the card is too narrow, the buttons wrap to their own right-aligned row. At 1440px and wider they stay on one row.
- **Chat wrapper:** `.chat-main-wrapper { min-width: 0 }`.

In `add-meeting-button.component.scss`:
- **Button group:** `.meeting-actions` gets `flex-wrap: wrap; justify-content: flex-end`, so on narrow phones the two buttons stack instead of overflowing.
- **CometChat header:** it uses the same component. It only changes if the buttons don't fit on one line.

### Verification

- Tested in headless Chrome on a page built with the app's real `build.css`, the protected-layout wrappers and a 280px sidebar.
  - The bug reproduced there before the fix.
  - After the fix, at 500, 700, 960, 1032, 1440 and 1920px, the name truncates with "…", both buttons are visible, and the card stays inside its column.
- Not done:
  - `npm run gates` was not run.
  - No automated tests were added (no guardian skill yet).
  - No check in the running app. On dev, check a long-named group chat in iPhone, iPad Pro and 1440px views, with and without a thread open.
- On that test page the chat page also scrolls sideways a little at 1032 and 1440px. This comes from the page's own `.row` margins (with the container's padding set to 0), not from the chat header. It wasn't changed; if it shows up in the real app, it needs its own issue.

## Open

- On mobile, the thread panel still takes 40% of the width (`w-40`). This is outside SAN-2102's scope; a separate issue is needed if it should become full-screen on small viewports.
