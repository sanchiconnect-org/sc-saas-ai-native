---
id: SAN-999
title: "Startup Basic Information: invalid-fields badge ignores missing Founder name when startup_founders_advisory is on"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-999
repos: [frontend]
commit: sc-saas-frontend@<pending, branch ai_native_setup>
created: 2026-09-25
updated: 2026-09-25
---

# SAN-999 — Founder name not counted in Basic Information's "N field(s) are not complete yet"

## Problem
With `startup_founders_advisory` ON, the Team → Leadership Team section (founder Name*) is rendered on the Basic Information tab. The profile-completion popup correctly lists "Founder name is missing" (backend `startup.repository.ts` adds `founders[0]?.name` to the Basic Information criteria when the flag is on). The in-page badge and the NEXT STEP gate don't include it, so the two indicators disagree and users can't find the field.

## Root cause
`countInvalidFields` and `checkInvalidFields()` in `startup-information.component.ts` only check `startupInfoForm`, `pitchForm`, `productInfoForm`, the business model selection and the logo. They never look at the `foundersInfo` FormArray. Classification: CODE_ERROR.

## Fix
`sc-saas-frontend/src/app/modules/startups/pages/edit/startup-information/startup-information.component.ts`:
- new `getInvalidFounderControls()`: returns the invalid controls across all founder rows, and `[]` when the flag is off or the form isn't initialised yet.
- `countInvalidFields` adds that count. This count also gates NEXT STEP.
- `checkInvalidFields()` marks those controls as touched, so "Name is required" is shown.

## Behaviour notes
- A narrower variant (count only when no founder has a name) was tried and then reverted at the user's request (2026-09-25).
- Counted: an empty Name in any founder row (including a blank extra row added with "+") and an invalid LinkedIn URL. Such rows were previously skipped silently when saving. With the flag on, NEXT STEP stays disabled until they are fixed or the extra row is deleted.

## Verification
`tsc --noEmit -p tsconfig.app.json`: no errors in the touched file. The repo has no lint config. No automated test added. Not yet verified in a browser.
