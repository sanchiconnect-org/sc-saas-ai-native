---
id: SAN-2033
title: "[disabled] with a reactive form directive on partners/mentors/program-office industry-technology"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2033
sentry: [SC-SAAS-FRONTEND-Z]
repos: [frontend]
related: [SAN-1660]
commit: frontend@e1aa558cd (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2033: redundant [disabled] bindings removed

## Root cause
* Over 30 days, FRONTEND-Z fired 2 events on thub dev, on `partners/edit/industry-technology` (`045b5af1c`, 10-23).
* The `investors/edit/organization-details` path was fixed earlier by SAN-1660.
* Some inputs bind both `[formControlName]` and `[disabled]="isMaxTechnologiesSelected"`. In Angular 13, the `disabled` input on `FormControlName` only logs this warning; it never disables the control (`@angular/forms` `forms.mjs:5114`).
* All three components already disable and enable the controls programmatically in `industrySelectionChange()`.

## Fix
Removed the redundant bindings:
* `partner-industry-technology.component.html:152`
* `mentor-technology-industry.component.html:43, 111`
* `program-office-technology-industry.component.html:43, 65`

`step-choose-industries` was not touched: it isn't a formControlName binding.

## Blast radius / existing-flow impact
None. The binding never had an effect, and the controls are disabled exactly as before.

## Verification
* Targeted specs: `npx ng test --watch=false --browsers=ChromeHeadlessCI --include=<connect-button, connections-v3, dashboard-v2, program-public-apply, app.component specs>` → `TOTAL: 48 SUCCESS`.
* `npx tsc -p tsconfig.app.json --noEmit` → 0; `npx tsc -p tsconfig.spec.json --noEmit` → 0.
* `npm run gates` (sc-saas-frontend, all five frontend tickets together):

```
passing tests: 1304 (floor 1295)
  0    openapi-types
  0    loader-floor
  0    build
  0    unit-tests
  0    test-floors
=> passed
```
