# SAN-2005 — Startup profile: pitch-deck Connect button stays "Connect" after a request is sent from the header

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-2005
- **Repo:** sc-saas-frontend (branch `ai_native_setup_vishali`)
- **Classification:** CODE_ERROR · **Priority:** Medium · **Assignee:** vishali kashyap

## Problem
On a startup public profile (`/startups/profile/:uuid/:slug`), sending a connection request from the header button switches that button to **Pending Request**. The pitch-deck overlay ("Accessible only to connections.") keeps showing **CONNECT** until the page is reloaded.

## Root cause
`startup-public-profile-v2.component.html` renders several independent `<app-connect-button>` instances for the same user (header, hero, pitch-deck overlay). Each `ConnectButtonComponent` holds its own `connectionRequestStatus`. A successful send, accept, reject or remove only called `checkConnectionRequest()` on the instance that was clicked, so the other instances never refreshed.

## Fix (files changed)
- `src/app/core/service/connections.service.ts`: adds a shared `connectionStatusChanged$` stream and `notifyConnectionStatusChanged(otherUserUUID)`.
- `src/app/shared/common-components/connect-button/connect-button.component.ts`: every successful send (normal and investor), accept, reject and remove now calls `refreshConnectionStatus()`, which broadcasts the target user's uuid. Each instance subscribes (`listenForConnectionStatusChanges()`) and re-runs `checkConnectionRequest()` when the uuid matches its own target. The target is `usersDetails[0].uuid`, or `pendingOtherUserUUID` on the reduced DTO. When there is no uuid, it falls back to the old local re-check.

The fix is generic: any page that shows more than one connect button for the same user stays in sync.

## Contract impact
None. Frontend only, with no API, DTO, flag or tenant-scoping change.

## Verification
- `npx tsc -p tsconfig.app.json --noEmit` passed with no errors.
- `npm run gates` in sc-saas-frontend: openapi-types 0, loader-floor 0, build 0, unit-tests 0, test-floors 0 (1125 passing, floor 1116) → passed.
- Not yet checked in a browser; that needs a deploy. No new automated test (the guardian skill isn't available yet).

## Open
- One screenshot showed the pitch-deck overlay with **no button at all** under "Accessible only to connections." This fix doesn't explain that. If it reproduces after a reload, track it separately.
- Needs a merge to `ai_native_setup` / `development` and a redeploy, then a browser check.

## Commit
`c42cc7cf0` on `ai_native_setup_vishali` (sc-saas-frontend), pushed 2026-10-23. Linear: Done.
