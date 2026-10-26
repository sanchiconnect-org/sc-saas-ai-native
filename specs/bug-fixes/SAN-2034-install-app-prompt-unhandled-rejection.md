---
id: SAN-2034
title: "installApp(): BeforeInstallPromptEvent.prompt() rejection is unhandled (NotAllowedError)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2034
sentry: [SC-SAAS-FRONTEND-HT]
repos: [frontend]
related: []
commit: frontend@8ba8388d7 (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2034: PWA install prompt rejection handled

## Root cause
* FRONTEND-HT: 1 event on prod `218edca78`, `startups.ieema.org/programs/apply/…`, from Chrome on Linux at a Google Cloud IP. It looks like a bot or synthetic click.
* `installApp()` called `deferredPrompt.prompt()` and never handled its rejection.
  * `prompt()` rejects with `NotAllowedError` when there is no user gesture.
  * It rejects with `InvalidStateError` when called twice on the same event.

## Fix
`app.component.ts` `installApp()`:
* keeps the existing "installApp clicked" log;
* returns if there is no saved prompt, as before;
* clears `deferredPrompt` before calling `prompt()`;
* then runs `Promise.resolve(prompt.prompt()).then(() => prompt.userChoice).then(log outcome).catch(() => {}).finally(() => showInstallPrompt = false)`.

Tests (2) in `app.component.spec.ts`:
* `prompt()` rejects with NotAllowedError and `installApp()` is called twice: `prompt()` runs once, `deferredPrompt` is null and the banner is hidden.
* The user accepts: the banner closes.

## Blast radius / existing-flow impact
* A real click still shows the native install dialog and logs the user's choice.
* Only difference: the banner now also closes when `prompt()` rejects.

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
