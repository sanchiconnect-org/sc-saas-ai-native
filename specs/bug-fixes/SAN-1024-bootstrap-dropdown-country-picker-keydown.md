---
id: SAN-1024
title: "bootstrap Dropdown parentNode crash in phone country picker"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1024
sentry: [SC-SAAS-FRONTEND-G5]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1024

## Root cause (CODE_ERROR, library interaction)
bootstrap.js document keydown handler assumes a `[data-bs-toggle=dropdown]` next to every `.dropdown-menu`; ngx-intl-tel-input's `.country-dropdown` has none → ArrowUp/Down/Escape crash.

## Fix
`src/main.ts`: keydown listener on <html> stops those keys only inside `ngx-intl-tel-input .dropdown-menu.country-dropdown`.

## Existing-flow check
A broader `.dropdown-menu` match would have broken Escape-to-close on ~20 ngbDropdown menus (ng-bootstrap listens on document keydown) — deliberately narrowed. ngx-intl-tel-input uses keyup (search, esc) → unaffected.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
