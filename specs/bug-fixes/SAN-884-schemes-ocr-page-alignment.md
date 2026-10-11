---
id: SAN-884
title: "Schemes/OCR page — header, tab bar, and content don't share the same left/right edge"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-884
sentry: []
repos: [frontend]
commit: sc-saas-frontend@0ee97e32, sc-saas-frontend@992222b2 (branch ai_native_setup_vishali)
created: 2026-09-21
updated: 2026-09-22
---

# SAN-884 — Fix Schemes/OCR page alignment

## Root cause
CODE_ERROR — a container-width mismatch, not a spacing/margin bug. In `operational-cost-reimbursement.component.html`, the header/toolbar uses `container-xxl` (matching this component's own stated reference, `call-for-applications.component.html`), but everything below it — the Schemes/OCR tab bar and both tabs' content — was wrapped in a single `<div class="ocr-page container py-4">`, using plain `container` instead.

Confirmed against this app's actual compiled Bootstrap rules (`src/assets/css/build.css`):
- `.container` caps at `max-width: 1140px` from the 1200px breakpoint, and only matches `.container-xxl` (1320px) at 1400px and above.
- `.container-xxl` stays effectively full-width (gutter padding only, no max-width) below 1400px.

So for any viewport roughly between 1200px and 1400px — a very common laptop range (1280, 1366, 1440) — `.container-xxl` renders much wider than `.container`. Both are horizontally centered (`margin: auto`), so their left edges land at different offsets from the viewport edge, visibly misaligning the header against the tab bar and content below it. `call-for-applications.component.html` (the page this component mirrors) avoids this by keeping its header **and** its main content section both on `container-xxl` — only its own tab bar sits in a separate, intentionally narrower `.toolbar > .container` bar with its own border, a deliberate secondary box, not the same one as the main content.

## Fix
`operational-cost-reimbursement.component.html`: changed the wrapping div's class from `container` to `container-xxl`, matching the same container class already used for the equivalent section on the reference page. No routing, tab-switching (`selectTab`/`activeTab`), guard, or data-fetching logic touched.

### Follow-up 1 — top spacing (direct user feedback with screenshot)
After the width fix, the user reported too much empty space between the header and the tab bar. Cause: the header toolbar already carries its own `pt-10` top padding; `.ocr-page` additionally had `py-4` (top **and** bottom), so the top gutter effectively doubled. Changed `container-xxl py-4` → `container-xxl pb-4` (dropped the top padding, kept the bottom one for spacing above the footer). (The user separately added `mt-4` to the tab `btn-group` on disk — left as-is, their own spacing preference, not reverted.)

### Follow-up 2 — summary card layout (direct user feedback with screenshot)
The Status/Scheme-window summary card — part of this ticket's "top section text alignment" scope — looked lopsided: both metric blocks bunched at the left with a large empty gap on the right, made more noticeable by the wider `container-xxl` card from the width fix. First attempt changed the row to `d-flex flex-wrap justify-content-between gap-10` (spreading the two blocks to the card's edges).

### Follow-up 3 — reverted the edge-spread, just tightened the gap (direct user feedback)
Spreading to the edges was the wrong direction — the user wanted the two blocks to stay left-aligned as before, just closer together. Final: `d-flex flex-wrap gap-4` (no `justify-content-between`, `gap-10` → `gap-4`).

### Follow-up 4 — re-spread Scheme window to the card's far right edge (direct user request, 2026-09-22)
Reopened after the previous fix shipped. New request: put "Scheme window" at the end/right side of the card, opposite "Status" — the same edge-spread layout Follow-up 3 had reverted. Confirmed with the user before reapplying (given the recorded prior reversal); user explicitly asked to redo it. Changed the row back to `d-flex flex-wrap justify-content-between` (no `gap-4` — the two blocks push to the card's own edges instead of needing a manual gap).

## Blast radius
`.ocr-page` has no dedicated CSS rule of its own (confirmed via grep of the component's `.scss` and the module) — it's a marker class only, so the visual behavior comes entirely from the Bootstrap `container`/`container-xxl` utility swap. Both the Schemes tab's card grid (`col-12 col-sm-6 col-lg-4`) and the OCR tab's month grid (`row-cols-1 row-cols-sm-2 row-cols-lg-3 row-cols-xl-4`) are already responsive column classes that degrade/upgrade with available width — widening the container only gives them more room at wide viewports, the same as `call-for-applications`'s own grid already does.

## Final shipped state
`operational-cost-reimbursement.component.html`:
- Wrapping div: `class="ocr-page container-xxl pb-4"` (plus the user's own `mt-4` added directly to the tab `btn-group`).
- Summary card row: `class="d-flex flex-wrap justify-content-between"` (Follow-up 4 — supersedes Follow-up 3's `gap-4`).

## Verification
`tsc --noEmit` clean after every round, including Follow-up 4. Earlier rounds also ran `ng build --configuration local` and diffed the compiled Ivy `consts` array against the live dev-server bundle. No automated test applies — this is a CSS/markup-only visual fix with no visual-regression tooling in this repo; final confirmation is the user's own visual check at a few common widths.
