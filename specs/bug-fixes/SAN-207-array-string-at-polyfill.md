---
id: SAN-207
title: "Array/String.prototype.at() missing on in-app-browser engines — feature-detected polyfill"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-207
sentry: [SC-SAAS-FRONTEND-3C]
repos: [frontend]
commit: sc-saas-frontend@15d03e3ba
created: 2026-09-28
updated: 2026-09-28
---

# SAN-207 — .at() polyfill for non-evergreen in-app-browsers

## Root cause
Filed 2026-08-03 with only a minified stack trace (`TypeError: this.o.at is not a function`) and no way to identify the call site. Re-investigating today surfaced the full event detail (not available at filing time): `browser: Instagram 408.0.0` on Android 10, same `/programs/apply/sup4919/supernova-incubation-programme` page as the sibling ticket SAN-209/SC-SAAS-FRONTEND-3A — both are the same underlying class of bug: Instagram's in-app Android WebView using an older JS engine than this app assumes.

`.at()` is an ES2022 Array/String method. `sc-saas-frontend/src/polyfills.ts`'s own header comment states the app's polyfill setup targets only "evergreen browsers" (recent auto-updating Chrome/Safari/Edge) — there's no `core-js` or any ES2022 polyfill, so any in-app-browser WebView lacking native `.at()` throws as soon as anything in the bundle calls it.

## Fix
Added a small, feature-detected inline polyfill for `Array.prototype.at` and `String.prototype.at` directly in `polyfills.ts`. No new dependency — the method's behavior is trivial to implement natively (index normalization + bounds check), and pulling in all of `core-js` for one ES2022 method would be disproportionate. Both are guarded with `if (!...prototype.at)`, so they're a complete no-op on any browser/engine that already has native support.

`tsconfig.json`'s `lib` is `["ES2021", "dom"]` (no `.at()` typings), so both assignments are cast through `any` rather than bumping the lib target just for this.

## Blast radius
`sc-saas-frontend`, `polyfills.ts` only. Zero behavior change for any browser with native `.at()` support (the vast majority of traffic) — purely additive for engines missing it.

## Verification
`npx tsc --noEmit -p tsconfig.app.json` clean (the actual build config, excluding spec files). Manually verified the polyfill's index-normalization logic matches the ES2022 spec (negative indices count from the end, out-of-range returns `undefined`).

## Rollout
Neither SC-SAAS-FRONTEND-3A nor -3C has recurred in Sentry in 24-46+ days even before this fix (likely the specific in-app-browser/campaign traffic that triggered them has stopped), so there's no way to positively confirm this fix resolves live traffic. Still a real, correct fix for the underlying engine gap — worth having in case similar traffic returns.

## Open questions
None.
