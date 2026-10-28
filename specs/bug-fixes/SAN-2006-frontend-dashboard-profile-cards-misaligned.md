---
id: SAN-2006
title: "Startup dashboard 'Your next actions' and 'Why complete your profile' cards: misaligned text and blank gaps"
type: bug-fix
status: in-progress
linear: https://linear.app/sanchiconnect/issue/SAN-2006
repos: [frontend]
related: [SAN-1469, SAN-1473]
commit: not committed yet (branch ai_native_setup_sandeep)
created: 2026-10-23
updated: 2026-10-23
---

# SAN-2006: dashboard profile-completion cards look unfinished

## Problem
On `/startups/dashboard` (development, `thub.sanchidev.in`, profile at 18% and 48%):
* every line in "Your next actions" and "Why complete your profile" starts after a blank gap;
* in "Why complete your profile" the item title ("Industries are missing") is indented about 8px further than its description line;
* rows have almost no vertical spacing and no separator lines, and title and description look alike.

## Evidence
Two screenshots from the reporter (18% and 48%, development). Not reproduced on a running server by the fix author.

## Root cause
* **Class:** CODE_ERROR (CSS), two separate causes.
* **"Why complete your profile"** (inline in `dashboard-v2.component.html`): `dashboard-v2.component.scss` (lines 41-57) styles every `ul li` of the template with `display: inline !important`, and sets `padding: 0.5rem !important` on any `a` and `span` inside. The card's `li` rows were therefore inline: `py-2` and `border-bottom` did nothing (no spacing, no separators), and the title link got 8px of padding, which is the extra indent.
* **"Your next actions"** (`dashboard-next-actions`, its own component, so the page scss does not apply): the `ol` used `class="list-unstyled"`, and that class is **not defined** in `src/assets/css/build.css` (0 matches), so the list kept the browser's default left padding: the blank gap before each action.
* The template has no icon element, so the gap was never a missing icon.

## Fix (sc-saas-frontend only, 2 templates)
* `src/app/modules/dashboard-v2/dashboard-v2.component.html`: the "Why complete your profile" list is now `div role="list"` with `div role="listitem"` rows (not `ul/li`, so the page scss does not match them). Title is `d-block fs-6 fw-bolder`, description `fs-7 text-gray-600 mt-1`, rows `py-3` with `border-bottom` between them.
* `src/app/modules/dashboard-v2/components/dashboard-next-actions/dashboard-next-actions.component.html`: the `ol` gets `p-0` and `list-style: none`; rows `py-3`.
* `src/app/modules/dashboard-v2/module.spec.md`: "Watch out for" entry added.

## Blast radius / existing-flow impact
* `sc-saas-frontend` only, templates only. No TypeScript, API, flag or tenant-scoping change.
* The click targets and routing are unchanged (`[routerLink]="gap.url"`, the next-actions button and `act()` are as before).
* Other users of `list-unstyled` (`membership.component.html`, `challenge-form.component.html`, `course-detail.component.html`) may show the same left gap. **Not checked and not changed** here.

## Verification
* `npx ngc -p tsconfig.app.json --noEmit` (compiles the templates): exit 0, no output.
* `npm run gates` (production build + Karma + test floors) **not run**.
* No automated test added: the change is CSS/markup only and Karma needs a browser. A computed-style test was proposed and skipped.
* **Not verified in a browser.** To check on development at desktop and phone width:
  1. Title and description share one left edge in "Why complete your profile".
  2. Rows have spacing and separator lines between them.
  3. "Your next actions" has no blank gap before the action text.

## Commit
Not committed yet.
