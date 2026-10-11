---
id: SAN-839
title: "Missing IntersectionObserver polyfill causes ng-lazyload-image \"it.observe is not a function\" crash"
type: bug-fix
status: blocked
linear: https://linear.app/sanchiconnect/issue/SAN-839
sentry:
  - SC-SAAS-FRONTEND-68
repos: [frontend]
commit: none — fix not yet applied, blocked on a dependency-addition decision (see below)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-839 — ng-lazyload-image missing IntersectionObserver polyfill

## Investigation
`TypeError: it.observe is not a function`, culprit `ng-lazyload-image`'s `getObservable()`. 35 occurrences / 34 users at 10% trace sampling (~350 real hits estimated).

This is not an app-level null-check bug. `ng-lazyload-image` relies on the native `window.IntersectionObserver` API unless a custom `LAZYLOAD_IMAGE_HOOKS` provider is registered. Grepped `shared.module.ts`, `app.module.ts`, all lazy modules, and `src/polyfills.ts` — there is no `LAZYLOAD_IMAGE_HOOKS` provider and no `IntersectionObserver` polyfill anywhere in the app. On browsers/environments where native `IntersectionObserver` is missing or broken (old Safari, some in-app webviews, bot/crawler UAs — the captured event's uncaught `onerror` outside Angular's zone on a public unauthenticated `/programs/apply/...` URL is consistent with crawler traffic), the library's fallback isn't a real observer and throws.

## Fix
Not implemented. The fix requires adding a new npm dependency (`intersection-observer` polyfill) and running `npm install`, which changes `package.json`/the lockfile and the build in a way none of the other SAN-829–838 batch fixes do. Held pending an explicit go-ahead before installing.

Proposed change once approved: `npm install intersection-observer --save`, plus one import line in `src/polyfills.ts`. No app code/behavior change on browsers that already support native `IntersectionObserver` — it only fills the gap on ones that don't.

## Blast radius
Would be `sc-saas-frontend`-wide (any component using `ng-lazyload-image`'s `lazyLoad` directive), but scoped in practice to browsers/crawlers lacking native `IntersectionObserver` support.

## Verification
Not yet — pending implementation. Once added, verify via manual repro on a browser/tool with `IntersectionObserver` disabled (or a bot-UA emulation) that lazy images still load without throwing.
