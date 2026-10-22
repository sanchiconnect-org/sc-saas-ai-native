---
id: SAN-1986
title: "dynamic-form-submit crashes reading 'map' of null when a form has fields: null (SC-SAAS-FRONTEND-HR)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1986
sentry: [SC-SAAS-FRONTEND-HR]
repos: [frontend]
commit: frontend@0ddace11a (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1986: dynamic-form-submit crashes on a form with `fields: null`

## Root cause
* **Sentry:** `Uncaught (in promise): TypeError: Cannot read properties of null (reading 'map')`.
  * 3 events, 1 user, 2026-10-21, app.sanchiconnect.com `/forms/form/submit/<uuid>`, Chrome on macOS, production.
  * Release `3fe291506`. `git diff 3fe291506 -- dynamic-form-submit.component.ts` is empty, so the code is unchanged since that release. This is a live bug, not deploy lag.
* **Where:** `src/app/modules/dynamic-forms/dynamic-form-submit/dynamic-form-submit.component.ts:428` (`getEventDetails`), reached from `getFormsList()` → `getEventDetails()`.
* **How it fails:** a form that comes back with `fields: null` (no sections). The two statements just above already guard it (`(this.formObject.fields || [])`), but the "hide invisible fields" step did `this.formObject.fields.map(...)` unguarded and threw inside the async function.
* **Effect:** the promise rejects before `buildForm()` and `initiateParticipation()` run, so the form page never finishes loading (`dataLoading` stays true).
* Prior `null.map` tickets (SAN-943, SAN-658, SAN-486) were other call sites.

## Fix
`this.formObject.fields = (this.formObject.fields || []).map(...)`, the same guard the lines above use.
* A form with sections is processed exactly as before.
* A form with `fields: null` is treated as a form with no sections. `buildForm()` and `patchForm()` already handle `[]`.

## Blast radius / existing-flow impact
* One expression in one component. The behaviour only differs where it used to throw.
* No API, DTO, flag or tenant-scoping impact.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → exit 0.
* Two new specs in `dynamic-form-submit.component.spec.ts`:
  * `fields: null` → `formObject.fields` is `[]`, and `buildForm`/`initiateParticipation` still run;
  * invisible fields are still hidden and sections left empty are still dropped.
* `npx ng test --watch=false --browsers=ChromeHeadless --include=<dynamic-form-submit spec> --include=<step-two-product spec>` → `Executed 6 of 6 SUCCESS`, `TOTAL: 6 SUCCESS`.
* Lint: the repo has no lint configured (see `sc-saas-frontend/CLAUDE.md`), so none was run.
* Full `npm run gates` not run here (the coordinator runs it once for the sweep).

## Related
SAN-943, SAN-658, SAN-486 (other `null.map` sites). Same 2026-10-22 Sentry sweep: SAN-1991, SAN-1993, SAN-1994, SAN-1982.
