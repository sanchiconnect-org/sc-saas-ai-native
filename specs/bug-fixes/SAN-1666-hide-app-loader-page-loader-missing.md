# SAN-1666 — `hideAppLoader` throws when `#pageLoader` is already gone

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1666 (Sentry SC-SAAS-FRONTEND-GR 3 events / 2 users, GQ 1 event)
- **Repo:** sc-saas-frontend · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR

## Problem
`Error: The selector "#pageLoader" did not match any elements`, culprit `hideAppLoader(src/app/app.component)`, production, last 2 days.

## Root cause
`AppComponent.hideAppLoader()` used `renderer.selectRootElement('#pageLoader')`, which throws when the splash `<div id="pageLoader">` from `index.html` is not in the DOM (removed or never
rendered, for example on a second call or a cached shell). The throw aborts the caller.

## Fix
`document.getElementById('pageLoader')`, hiding it only if present. Identical behaviour when the element exists.

## Contract impact
None. No API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` and `ngc` exit 0. No automated test added (no spec for this method).

## Commit
sc-saas-frontend `fef12ea62` on `ai_native_setup_aman`. Not deployed.
