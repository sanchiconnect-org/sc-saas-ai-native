# SAN-1143 / SAN-1144 — beacon.min.js SyntaxError noise; unidentified promise rejection diagnostics

- **Linear:** SAN-1143 (SC-SAAS-FRONTEND-GA, -D1), SAN-1144 (SC-SAAS-FRONTEND-4B)
- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra · **Classification:** NOISE (1143), NEEDS_MORE_INFO (1144 — not fixed)

## SAN-1143
`SyntaxError` raised inside `beacon.min.js`, a third-party analytics script (the `beacon.min.js/v<hash>` form matches Cloudflare's web
analytics beacon, which is inferred). Every frame is that script, so nothing in this repo can fix it. `src/main.ts` `beforeSend` now drops the
event only when it is a `SyntaxError` AND a frame is `beacon.min.js` (narrow on purpose).

## SAN-1144
`UnhandledRejection: Object captured as promise rejection with keys: code, message, status` has no stack. The latest event's payload is
`{code: 400, message: "TOKEN_EXPIRED", status: "INVALID_ARGUMENT"}` on the public program-apply page, a Google-API-style error that nothing in this
repo creates. `beforeSend` now attaches the rejected object's status/code/message/url (from `hint.originalException`) as `extra.rejection` and a
`rejection_status` tag so the next occurrence names the failing request. Diagnostic only; the event is still sent. **The issue is not fixed.**

## Contract impact
None. Sentry filtering/metadata only.

## Verification
`tsc --noEmit` clean. No automated test added (none exists for main.ts). The release that last produced 4B (`9dde12280`, 25 Sep) predates this
commit, so the diagnostic needs a deploy before it can show anything.

## Commit
sc-saas-frontend `8dad09952` on `ai_native_setup_aman`. Not deployed.
