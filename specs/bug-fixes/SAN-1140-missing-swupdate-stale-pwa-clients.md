---
id: SAN-1140
title: Missing SwUpdate handling — PWA clients frozen on old JS, re-firing already-fixed Sentry errors
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1140/sentry-missing-swupdate-handling-pwa-clients-silently-frozen-on-old-js
repos: [frontend]
created: 2026-09-29
updated: 2026-09-29
---

# SAN-1140 — sc-saas-frontend never calls SwUpdate, so old clients never pick up new deploys

## Request

Sentry triage task (`/bug-fix`, Production Defects project): pick unresolved `sc-saas-frontend` production issues (last 14d), file Linear tasks for genuine bugs, mark already-fixed ones resolved with a comment, investigate fixes without breaking existing flows.

## Investigation finding

Querying `sc-saas-frontend`'s Sentry errors (production, 14d) grouped by `release` showed **20 different release hashes** actively producing errors simultaneously — evidence that a large number of clients are running arbitrarily old cached bundles, not the current deployed build. One of those releases (`sc-saas-frontend@51eb6706`) was already independently confirmed stale in an earlier session's triage (2026-08-24, workspace memory `sentry-fixes-merged-not-deployed`).

Cross-checked five other Sentry groups reported as still firing against the current `ai_native_setup_sandeep` code and confirmed **all five are already fixed**:
- `SC-SAAS-FRONTEND-EP` / `-3F` — ngx-ui-loader "master" duplicate (SAN-920/SAN-814)
- `SC-SAAS-FRONTEND-G9` — `auth.guard.ts` null `accountType` (SAN-213/SAN-535 — `checkAccountType()` is only ever called after a `!sessionUser` guard)
- `SC-SAAS-FRONTEND-G8` — `handleDurationChange()` null `.split()` (SAN-485/SAN-647 — the latter's own title says "already fixed, pending deploy")
- `SC-SAAS-FRONTEND-F0` — `hiring-manager-contact.component.ts` undefined `mobileNumber` (optional-chained, SAN-378 class)
- `SC-SAAS-FRONTEND-GE` — `dashboard-v2.component.ts` `userType.type` (default-initialized `userType = { type: 'all', label: 'All' }`, comment cites SC-SAAS-FRONTEND-30) — this exact class has been "fixed" 3+ times before (SAN-205, SAN-371/483, SAN-918/1046) and kept reappearing, itself a signal pointing away from a code-logic root cause and toward a deploy/caching one.

## Root cause

`app.module.ts:81-86` registers `ServiceWorkerModule` with `registrationStrategy: 'registerWhenStable:30000'`, but nothing in the app ever imports or uses `SwUpdate`. Angular's service worker downloads a new version in the background but — by design — never forces an already-open tab or installed PWA instance to activate it; that requires the app to subscribe to `SwUpdate.versionUpdates` and act on `VERSION_READY`. Without it, a client can run a build from weeks ago indefinitely, especially an iOS "Add to Home Screen" PWA (confirmed: the SC-SAAS-FRONTEND-GE event triggering this investigation was exactly that — Mobile Safari, iOS, at `connect.trise.tripura.gov.in`).

## Fix

`src/app/app.component.ts`:
- Injected `SwUpdate`.
- Added `listenForAppUpdates()` (called from `ngOnInit()` alongside the existing `listenForInstallPrompt()`), subscribing to `swUpdate.versionUpdates`, filtered to `VersionReadyEvent` (`evt.type === 'VERSION_READY'`), guarded by `swUpdate.isEnabled` (false outside production, matching `ServiceWorkerModule.register({ enabled: environment.production })`).
- Added `showUpdatePrompt` state, `reloadForUpdate()` (`document.location.reload()`), `dismissUpdatePrompt()`.

`src/app/app.component.html`:
- Added a dismissible "Update Available / Refresh" banner, structurally mirroring the existing `showInstallPrompt` PWA-install banner exactly (same CSS classes, same close-button pattern) — no new styling needed, no risk of diverging visual language.

## Design decisions taken (not asked, judgment calls)

- **Manual refresh via a dismissible banner, not a silent auto-reload.** Several of the bugs this investigation traced back to this root cause are mid-form crashes (`handleDurationChange`, `mobileNumber`, dashboard search). Silently reloading the page the instant a new version is detected risks discarding in-progress user input — trading a rare crash for a guaranteed data-loss annoyance on every deploy. A user-triggered refresh, exactly like the existing install-prompt pattern already accepted in this app, was judged the safer default.
- **Mirrored `showInstallPrompt`'s exact markup/class structure** rather than introducing a new banner component, so there's no new CSS to review and the interaction pattern is already familiar/tested in this codebase.

## Contract check (step 5)

No API contract, feature flag, or tenant-scoped query is touched by this change — `/audit-contract`, `/trace-flag`, and `/check-isolation` don't apply here. Stated explicitly rather than silently skipped.

## Verified

- `npx tsc --noEmit -p tsconfig.app.json` — clean, no errors.
- `SwUpdate`/`VersionReadyEvent` API confirmed directly against `node_modules/@angular/service-worker/service-worker.d.ts` — the filter expression used (`filter((evt): evt is VersionReadyEvent => evt.type === 'VERSION_READY')`) matches Angular's own documented example in that file verbatim, not guessed from memory.
- `git diff --stat` — only `app.component.ts` and `app.component.html` touched (plus pre-existing, unrelated local changes to `app.component.ts`'s `getTenantDetails()` from the user's own in-progress local dev work, left untouched).

## Not verified — genuinely outstanding

No live test: reproducing a real `VERSION_READY` event requires two successive deploys observed from a client, which isn't possible from this sandbox. No automated test added — this repo has no existing pattern for testing service-worker runtime events, and per the standing workspace process, that's stated explicitly rather than silently skipped.

## Rollout

Not committed, not pushed — per standing instruction, awaiting review. Sentry groups EP, 3F, G9, G8, F0, GE were marked `resolved` with a comment explaining they were confirmed fixed in code, with this same stale-client root cause noted so a future recurrence isn't mistaken for a fresh regression before checking the event's `release` tag.

## Open questions

None blocking. Possible future follow-up (not decided): escalate to an auto-reload after the prompt has been ignored for N minutes, once the manual-refresh version is confirmed working in production — left as an option, not committed to.
