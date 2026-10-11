# SAN-1668 — browser-extension, wallet and in-app-browser errors reported as app errors

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1668 (Sentry SC-SAAS-FRONTEND-A2, A3, A4, A5, A6, 9H, 4H, 70, 8Y, 8Z, 9Q, 9R, 9W, CT, CV, CW, GD, E1, 9V, 41, 3Q)
- **Repo:** sc-saas-frontend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** NOISE (third-party code)

## Problem
About 20 unresolved production issues, each 1 to 18 users, are raised by code that is not in this bundle:
- an extension's injection: `[Injection][W] [Rpc Adaptor] ...`, `[Gen AI Tracker] ...`;
- an autofill extension: `ReferenceError: xbrowser is not defined` in `execute_auto_fill`; `Invalid call to runtime.sendMessage(). Tab not found.`;
- dev tools: `[locator-js]` / `[locatorjs]`; Cently: `[cently:rd:site] failed to patch window.location setter`;
- wallet extensions: `Error restoring session ...: Failed to connect to MetaMask` / `Transport request timed out`, `ObjectMultiplex - orphaned data for stream "metamask-..."`, `@polkadot/util ... multiple versions`;
- the Android in-app browser: `Error invoking postMessage: Java ...`, culprit `iabjs://navigation_performance_logger_android`.

## Fix
`src/main.ts` `beforeSend` drops an event when its message, exception value or `Type: value` text matches a `FOREIGN_NOISE` pattern (anchored to the foreign component's own wording), or when it is an
`Error invoking ...` whose stack has an `iabjs://` frame. Everything else is untouched, so a first-party error that merely mentions a wallet or an extension is still reported.

## Not fixed
Nothing here can be fixed from this repo; these are third-party components. If a real defect hides behind one of these wordings it will be dropped too, which is the cost of the filter.

## Contract impact
None. Sentry filtering only; no API, flag, tenancy or auth change.

## Verification
A node script extracted the real `FOREIGN_NOISE` list from `main.ts` and ran 24 cases: 15 real event titles are dropped (as value and as `Type: value`), and 9 look-alike first-party messages are kept
(`Cannot read properties of ... 'get'`, a 504 `Http failure response`, `Failed to connect to MetaMask while paying the registration fee`, and so on). 24/24. `tsc --noEmit` and `ngc` exit 0.
No automated test added (none exists for main.ts).

## Commit
sc-saas-frontend `7902cc3d6` on `ai_native_setup_aman`. Not deployed.
