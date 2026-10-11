---
id: SAN-814
title: "ngx-ui-loader 'master' duplicated on mentor edit custom-forms page (extra-intro-mentors)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-814
sentry: [SC-SAAS-FRONTEND-3F, SC-SAAS-FRONTEND-AZ, SC-SAAS-FRONTEND-B1]
related: [SAN-836, SAN-812, SAN-811, SAN-433]
repos: [frontend]
commit: sc-saas-frontend@4eb072fe (branch ai_native_setup_vishali)
created: 2026-09-28
updated: 2026-09-28
---

# SAN-814 — remove the second bare `<ngx-ui-loader>` in extra-intro-mentors

## Root cause
Every event on 3F (production, ~85 events / 16 users, last 2026-09-24), AZ and B1 is on a `/<type>/edit/custom-forms/:uuid/:slug` page. `extra-intro-mentors.component.html` renders two bare `<ngx-ui-loader>` elements: one always rendered (line 2) and one inside the `*ngIf="!isPreviewPage"` toolbar. Both register the global `"master"` loaderId (`NgxUiLoaderComponent.ngOnInit → bindLoaderData`). This is part of the systemic SAN-433 family.

- The program-office twin (`extra-intro-program-office`) was fixed by **SAN-836** (`1f57b9aa`), with this exact one-line deletion.
- The mentors template was never fixed. A 2026-09-24 production event on release `c2de0b1e`, which contains SAN-836, proves the mentors page still collides. Both loaders are present at `90bde7be`, `33244b02` and `c2de0b1e`.
- The service-provider and partners variants were fixed earlier by SAN-630 and SAN-548/SAN-632.

## Fix
`modules/mentors/pages/edit/extra-intro-mentors/extra-intro-mentors.component.html`: deleted the `<ngx-ui-loader></ngx-ui-loader>` inside the `*ngIf="!isPreviewPage"` toolbar. The unconditional loader at the top of the template stays, so the page loader still shows and hides as before. This is identical to the SAN-836 diff.

## Blast radius
`sc-saas-frontend`, one template. No logic change.

## Verification
- `tsc -p tsconfig.app.json --noEmit` clean. The template change is an element deletion only.
- No automated test added. Manual check: log in as a mentor, go to Edit profile → a custom-forms step. The page loader shows and hides normally, and there's no `loaderId "master" duplicated` console error.

## Open questions
None. SAN-812 and SAN-811 are duplicates (same root cause, dev-env events).
