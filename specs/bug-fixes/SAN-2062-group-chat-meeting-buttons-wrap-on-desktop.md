# SAN-2062 — Group chat meeting buttons wrap under the title on desktop and sit flush together

- **Linear:** [SAN-2062](https://linear.app/sanchiconnect/issue/SAN-2062) (Repo: Frontend). Reported by Ritu Raj while testing [SAN-2061](https://linear.app/sanchiconnect/issue/SAN-2061). High, assignee Vishali. Milestone: Enhancement → In-house chat speed up.
- **Classification:** UI/layout. Follow-up to SAN-2058 and SAN-2060, whose class-only fixes did not take effect.
- **Branch:** `ai_native_setup_vishali`. Commit: `305c121e9`.
- **Status:** Done in Linear (2026-10-27). Not yet merged into `ai_native_setup` or deployed.

## Problem

Seen on dev (thub.sanchidev.in), desktop Chrome at 1440×900, in the group chat "QA Startup 1793070519638/sanchi startup mahima":
- **Setup Instant meeting** and **Schedule meeting** wrap onto a second line under the title instead of sitting on the title row.
- The two buttons touch (0px apart).
- The header's computed style was `flex-wrap: wrap`, `align-items: normal`, `gap: normal`, although the template had `align-items-lg-center gap-3`.

## Root cause

1. **Missing utilities.** The app's compiled CSS (`styles.*.css`) contains only a subset of Bootstrap utilities. Checked against the deployed `styles.460013e5da78d0c2.css`:
   - `gap-3`, `d-inline-flex` and `px-lg-4` are absent;
   - `gap-2`, `gap-4`, `gap-5`, `align-items-lg-center`, `flex-lg-row`, `px-4`, `px-7` and `text-nowrap` are present.

   The SAN-2058 and SAN-2060 classes therefore did nothing, with no build error.
2. **The header wraps.** `.card .card-header` sets `flex-wrap: wrap`, and the title block had no flex sizing. A long group name (about 497px) plus the buttons did not fit in about 750px, so the buttons wrapped.
3. **The buttons stretch.** Both `<a>` buttons had `ngbDropdownItem`, a leftover from a dropdown that is now commented out. It adds `.dropdown-item` (`display: block; width: 100%`), so each button filled its share of the row.

## Fix (sc-saas-frontend)

- **Chat header** — `conversation-details.component.scss`, on `#kt_chat_messenger_header`:
  - `gap: .75rem`.
  - At ≥992px: `flex-wrap: nowrap; align-items: center`, and the title block (`> :first-child`) gets `flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere`. It shrinks and wraps its text; the buttons keep their width (`flex-shrink-0`).
  - The non-existent `align-items-lg-center gap-3` classes are removed from the template.
- **Meeting buttons** — `add-meeting-button.component.{html,scss}`:
  - `ngbDropdownItem` is removed, with `role="button" tabindex="0"` added so the buttons stay focusable.
  - The container is `.meeting-actions` (`display: flex; align-items: center; gap: .75rem`), and each `.btn` is `inline-flex`, centred, `nowrap`.
  - This also applies in the CometChat message header.
- **Chat list padding (SAN-2060 regression)** — `message-list.component.{html,scss}`:
  - The header and rows are back to `px-4`.
  - New `.chat-list-gutter` gets 1.75rem side padding only at `max-width: 991.98px`. Before this, `px-lg-4` was missing, so desktop had the mobile padding.

## Verification

- `bash scripts/gates.sh build unit-tests`: build exit 0, unit-tests 1338/1338 SUCCESS.
- Every utility class still used in the three templates was confirmed present in the deployed stylesheet.
- Not done: no browser check. After deploy, re-check:
  - the same group chat at 1440px: buttons on the title row, spaced, centred;
  - the desktop chat list padding is 16px again;
  - at 390px: buttons below the title, list gap at both edges;
  - the CometChat header for non-in-house tenants.

## Lesson

Before relying on a Bootstrap utility in this app, check that it exists in the compiled stylesheet, for example `grep -c '\.gap-3{' dist/**/styles.*.css`. Otherwise put the layout in the component's SCSS.
