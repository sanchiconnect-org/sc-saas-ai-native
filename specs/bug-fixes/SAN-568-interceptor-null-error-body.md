# SAN-568 — Interceptor crashes reading `error.error.message` on a 401/403 with an empty body

- **Linear:** SAN-568 (SC-SAAS-FRONTEND-6W)
- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra (taken over from vishali kashyap) · **Classification:** CODE_ERROR (best-supported cause, not proven)

## Problem
`TypeError: Cannot read properties of null (reading 'message')`, culprit `?(main)`, 3 users / 20 events.

## Evidence
The Sentry event has no first-party frame, so the site cannot be tied to a line from the event. `add-token-header.http-request-interceptor.ts`
read `error.error.message` in its 401 and 403 branches; a 401/403 with an empty body gives `error.error === null`, which throws exactly this
error. `main.ts` `beforeSend` guards every read with `?.`/`typeof`, so it is not the source.

## Fix
Use `error.error?.message` in both branches. The toast text and redirect behaviour are unchanged.

## Contract impact
None. No API, flag, tenancy or auth-model change; the 401/403 handling is the same, only a null body no longer crashes it.

## Verification
- `tsc --noEmit` and `ngc` clean. No automated test added.
- If SC-SAAS-FRONTEND-6W fires on a build containing this commit, the cause was something else.

## Commit
sc-saas-frontend `ef1bf2497` on `ai_native_setup_aman`. Not deployed.
