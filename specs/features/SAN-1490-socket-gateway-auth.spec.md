---
id: SAN-1490
title: Authenticate the socket gateway and restrict room joins to the caller's own rooms
type: feature
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1490
owner: vishali.k@sanchiconnect.com
repos: [backend, frontend]
contracts:
  api: []
  flags: []
  events: ["socket handshake auth (new)", "joinRoom (now authorised)", "start_typing / end_typing (now authorised)", "online_users (user id derived server-side)"]
tenant_scoped: true
depends_on: []
created: 2026-10-13
---

# Authenticate the socket gateway and restrict room joins

## Problem
`FetchCountGateway` (`sc-saas-backend/src/core/sockets/gateways/sockets.gateway.ts`) accepts any socket.io client with no authentication:
- **`joinRoom`** joins any room the client names. A personal room is the numeric **user id** (the backend emits to `userId` / `toUser.id` / `receiverUser.id` in chat, connections, conversations, job and notifications). So anyone can join `"42"` and receive user 42's `fetch-count` and `emitNotification` payloads: connection requests, message notifications and so on. That breaks BRD NFR-05.
- Anyone can join any **`conversation_<uuid>`** room and read live chat messages, replies and deletions (`chat.service.ts` → `emitToRoom`).
- **`start_typing` / `end_typing`** relay to any conversation room the client names.
- **`online_users`** trusts a client-supplied `userUUID` and broadcasts the full `socketId → userUUID` map to every connected client.

The issue must land before SAN-1470 (Phase 2 EX-03 personal-activity pushes), which adds more payload-bearing emits. Decision record: SAN-1398 (2026-10-01).

## Evidence (verified 2026-10-13)
- **REST auth** (`core/strategy/jwt.strategy.ts`): the JWT comes from the **httpOnly `accessToken` cookie** first, then from a Bearer header. The payload carries `userId`. `isBackDoorLogin` tokens skip the session check. When `single_session_login_enabled` is set, the token must equal the decrypted `users_login_session` token.
- **The cookie** (`auth.controller.ts:130/172/378`) is `httpOnly`, `secure`, `SameSite=None`, and scoped to the backend **apiUrl host**, the same host the socket connects to. That means it can ride the socket handshake without ever being exposed to JS.
- **The frontend** (`core/service/socket.service.ts`) connects with `new Socket({ url: apiUrl })` (ngx-socket-io 4.2.0) and **no `withCredentials`**, so today the cookie is *not* sent cross-origin.
  - The personal room is `profileData.id` (`app.component.ts:366`, user id).
  - The chat room is `conversation_<selectedConversation.uuid>` (`sc-conversations.component.ts:185`).
- **Only the frontend** uses the socket. No socket.io client exists in admin, tenants or tenants-admin, even though their origins are in `corsUrls`.
- **Membership data:** `chat_conversation_members (user_id, conversation_id)` joined to `chat_conversations.uuid`.

## Acceptance criteria
- [ ] A handshake with no valid JWT (no cookie, auth token or Bearer) is rejected with `connect_error` once enforcement is on.
- [ ] `joinRoom("<id>")` succeeds only when `<id>` equals the authenticated `userId`.
- [ ] `joinRoom("conversation_<uuid>")` succeeds only when the authenticated user is a member of that conversation.
- [ ] `start_typing` / `end_typing` are relayed only for conversations the sender is a member of.
- [ ] A refused join emits a `joinRoomRefused` event (or equivalent) and is logged without the token.
- [ ] `online_users` uses the **server-derived** user identity, not the client-supplied `userUUID` (see OQ-2 for who receives it).
- [ ] The legitimate flows still work end to end: live fetch-count badge, toast notifications, chat send/reply/delete, typing indicator, online dot.
- [ ] Hub→spoke login (SAN-384) still connects, using the cookie on the apiUrl host.

## Per-repo plan

### backend (sc-saas-backend), lands first
- `sockets.gateway.ts`:
  - Add `cors.credentials: true`. Keep the same `corsUrls` origins.
  - Implement `handleConnection(client)`. Extract the JWT from `client.handshake.headers.cookie` (`accessToken`), then `client.handshake.auth.token`, then the `authorization` header. Verify it with `JwtService` using the same secret as `JwtStrategy`. Apply the same single-session check (reuse the strategy's logic; don't fork it). Store `client.data.userId` and `client.data.userUUID`.
    - Missing or invalid token, when enforcing: `client.disconnect(true)`.
    - Missing or invalid token, in soft mode: allow the connection, mark it unauthenticated and log once.
  - `handleJoinRoom`: allow `String(client.data.userId)`. Allow `conversation_<uuid>` only after a membership lookup (new `ChatConversationMembersRepository.isMember(userId, uuid)`). Otherwise refuse.
  - `start_typing` / `end_typing`: check membership before relaying.
  - `online_users`: set `onlineUserIds[client.id]` from `client.data.userUUID`.
  - Add an env toggle `SOCKET_AUTH_ENFORCE` (default `false`) to the Joi `validation-schema.ts` and `AppConfigService`.
- Unit tests (jest) for the gateway: token extraction order, own-room allow, foreign-room refuse, conversation membership allow/refuse, soft vs enforce mode.

### frontend (sc-saas-frontend), lands second
- `socket.service.ts` `setUrl()`: `new Socket({ url, options: { withCredentials: true } })`. The cookie then rides the handshake, and no token is exposed to JS.
  - Optionally also pass `auth: { token }` from the store, for the case where the cookie isn't present (OQ-4).
- Handle `connect_error` / `joinRoomRefused` quietly: no toast, keep REST working.
- No change to room names.

## Contracts & invariants
- **Flags:** none.
- **API:** no REST route or DTO change.
- **Events:** the socket handshake now requires auth. `joinRoom`, `start_typing`, `end_typing` and `online_users` semantics are narrowed as above. Server-emitted event names and payloads are **unchanged**.
- **Invariants at risk:**
  - **#4 Auth:** this changes the socket auth model. It reuses the same JWT and cookie, and the same single-session rule as REST. Run `/cross-repo-review` before merging.
  - **#5 Tenant scoping:** one deployment per tenant, so the socket server is already per-tenant. The fix closes intra-tenant user-to-user exposure. No cross-tenant reference is added.
  - The CORS origins are unchanged. `credentials: true` is safe only with this explicit origin list, never with `*`.

## Test plan
- **backend:** jest gateway spec (above); `tsc --noEmit`; eslint.
- **frontend:** `ng build`; unit test that `setUrl` passes `withCredentials`.
- **cross-repo (staging or local):**
  - Two users A and B: A cannot `joinRoom(B.id)` or B's conversation.
  - A's badge, toasts and chat still update live.
  - Typing indicator and online dot work.
  - Hub→spoke login works.
  - A raw socket.io client with no cookie is refused in enforce mode.

## Rollout
Two repos deploy independently, so enforcement must come last:
1. **Backend, soft mode** (`SOCKET_AUTH_ENFORCE=false`): authenticates when a token is present and enforces room ownership for authenticated sockets. Unauthenticated sockets still connect, so old frontends keep working. Log the unauthenticated-connection rate.
2. **Frontend** with `withCredentials: true`. Watch the unauthenticated-connection log fall to roughly zero. Allow for PWA cache lag (SAN-1140).
3. **Flip `SOCKET_AUTH_ENFORCE=true`** per tenant deployment. Unauthenticated handshakes are then rejected and the foreign-room bypass is closed for everyone.

Rollback: set `SOCKET_AUTH_ENFORCE=false`. No data or schema change is involved.

**Hard ordering rule: the backend must be deployed before the frontend.** engine.io 6.2.1 applies `cors` with `credentials` only when the server sets it. The new frontend opens a credentialed (`withCredentials`) polling request. Against the *old* backend, that request has no `Access-Control-Allow-Credentials`, so the browser blocks it and realtime stops (badges, toasts, chat, presence). Backend alone, and backend then frontend, are both safe. Never deploy the frontend change first.

## Out of scope
- Moving socket.io to its own service or adding a Redis adapter.
- The `message` event handler (broadcasts the literal `'data'`; dead) is left as is, and can be removed separately.
- Admin, tenants and tenants-admin. None of them use the socket.

## Rollout status (2026-10-13)
**SAN-1490 and SAN-1892 were closed as Done by owner decision on 2026-10-13. SAN-45 is marked a duplicate of SAN-1490.** The unticked items below are post-closure **ops steps**, still required. In particular, the finding is fully closed only once `SOCKET_AUTH_ENFORCE=true` is set. Under PRA-24, a second-person review is still outstanding.

- [x] **Step 1 code: backend (soft mode)** pushed to `sc-saas-backend` `ai_native_setup_vishali`: `f6f1a152` (gateway auth, tests) and `4d743f33` (sockets module.spec). It is safe to deploy alone: the current frontend is unaffected (verified, real socket.io e2e 24/24).
- [x] Step 1 **deploy**: the backend is deployed. On 2026-10-13 dev (`api.thub.sanchidev.in`) was verified live: the `/socket.io/` polling response carries `Access-Control-Allow-Credentials: true`, and a cookie-less handshake still joins any room, confirming soft mode. Deploy remaining tenant backends the same way, with `SOCKET_AUTH_ENFORCE` unset.
- [x] Step 2 code: frontend (`withCredentials` + `reconnect()`) pushed to `sc-saas-frontend` `ai_native_setup_vishali` as `b9691380a`. It contains only `socket.service.ts` and `app.component.ts`.
- [ ] Step 2 **deploy**: deploy the frontend **only to tenants whose backend is already on step 1**. Then check that the `/socket.io/` request carries the `accessToken` cookie, and that badges, toasts, chat, typing and presence still work.
- [ ] Two-user smoke test on staging.
- [ ] Step 3: set `SOCKET_AUTH_ENFORCE=true` per tenant deployment.

## Decisions (resolved 2026-10-13 by owner, Vishali)
- **OQ-1 Rollout:** staged soft → enforce with `SOCKET_AUTH_ENFORCE`, accepted. Step 3 (enforce) should follow within a week of the frontend deploy.
- **OQ-2 `online_users`:** (a) tenant-wide presence, with the identity derived from the token. Once enforcement is on, only authenticated sockets exist, so presence reaches logged-in users only.
- **OQ-3 Single-session rule:** applied to sockets with the same rule as REST.
- **OQ-4 Token source:** the server accepts the cookie, then `handshake.auth.token`, then Bearer (same as REST). The frontend sends the cookie only (`withCredentials: true`), which covers every case including hub→spoke, so no token is exposed to JS.
- **OQ-5 Back-door tokens:** skip the session check, as in REST. They can only join the impersonated user's own room, since the room check uses the token's `userId`.
- **OQ-6 Frontend owner:** Vishali (one owner for both repos).

## Open questions
None.

## Implementation
**backend** (sc-saas-backend, `ai_native_setup_vishali`). **Pushed: `f6f1a152` (code + tests), `4d743f33` (module.spec).**
- `core/sockets/gateways/sockets.gateway.ts`
  - `cors.credentials: true`.
  - `extractHandshakeToken()`: cookie, then auth token, then Bearer.
  - `authenticate()`: `JwtService.verifyAsync`, the single-session check via `UserLoginSessionRepository` + `EncryptDecryptService`, the back-door skip, and the user uuid lookup.
  - Handshake **middleware** in `afterInit`, so auth completes before the client's first `joinRoom` is handled.
  - `joinRoom` is authorised via `canJoinRoom()`; a refused join emits `joinRoomRefused`.
  - **Typing relays** use `canRelayToRoom()`: an authenticated socket may relay only into a conversation room it has **already joined** (`client.rooms`), so no DB query runs per keystroke.
  - `online_users` uses the token identity.
  - The soft-mode connection log uses `logger.log`, not `warn`, to avoid flooding Sentry.
  - A second `JwtStrategy` is deliberately not constructed, because Passport strategies are global.
- `core/sockets/gateways/gateway.module.ts`: a verify-only `JwtModule` (same secret), plus `UserLoginSessionRepository`, `EncryptDecryptService` and `ChatConversationRepository` provided directly. Importing `AuthModule` would be circular.
- `modules/chat/repositories/chat-conversations.repository.ts`: **`isUserParticipantOfConversation(userId, uuid)`** uses the same participant rule as the chat REST queries:
  - `uuid` matches, and the conversation is not soft-deleted;
  - **and** the user is `creator_id`, **or** `to_user_id`, **or** `JSON_CONTAINS(members, :userId)`, **or** has a non-deleted `chat_conversation_members` row (CometChat imports).
- `core/config/{configuration,validation-schema,app-config.service}.ts`: `SOCKET_AUTH_ENFORCE`, optional and **lenient**. Only `true` (case-insensitive, trimmed) enforces; blank, absent or any other value means soft mode, and **never fails boot**. This follows the schema's existing boot-safety pattern; a strict `.valid()` would have crashed startup on a typo such as `TRUE`.
- `core/sockets/gateways/sockets.gateway.spec.ts`: 18 tests.

**frontend** (sc-saas-frontend, `ai_native_setup_vishali`). **Pushed: `b9691380a`.**
- `core/service/socket.service.ts`:
  - `setUrl()` opens the socket with `withCredentials: true`.
  - New `reconnect()` (disconnect + connect) re-handshakes with the current cookie.
- `app.component.ts`: when the logged-in user's id appears or changes (`socketUserId`), call `socketService.reconnect()` before `setSocketListners()` re-joins the room.
  - This covers every login path (OTP, signup, back-door): an in-app login doesn't reload the page, so the anonymous socket opened on page load must re-handshake to become authenticated.
  - Required before enforce, because socket.io-client does not auto-retry after a middleware rejection.
  - The cost is at most one extra handshake per page load.

## Cross-repo review (2026-10-13), and fixes
- **BLOCKER, fixed: wrong membership source.**
  - The first draft checked only `chat_conversation_members`. That table is written **only** by the CometChat import (`chat.service.ts:1186`). Natively created conversations record participants in `chat_conversations.creator_id`, `to_user_id` and `members`.
  - With the frontend sending the cookie, every authenticated user would have been refused their own chat rooms, losing live messages, replies, deletes and typing, even in soft mode.
  - Fixed by `isUserParticipantOfConversation` above.
- **WARN, fixed:** the frontend now re-handshakes after an in-app login (see above). Without it, enforce mode would cost a newly logged-in user badges, toasts, chat and presence until a reload.
- **WARN, fixed:** typing relays used to run a membership query per keystroke. They now check `client.rooms`.
- **NIT, fixed:** moved the `SOCKET_AUTH_ENFORCE` schema entry so it no longer splits the `QA_FIXED_OTP_*` pair.
- **NIT, accepted and documented:** typing payloads still carry the client-sent display name, so a *member* of a conversation could show a different name in the typing indicator. This is cosmetic and limited to people already in that chat.
- **NIT, pre-existing, follow-up:** the socket CORS list lacks the SAN-384 dynamic spoke origins that REST allows (`partnerCorsRegistryService`). Polling from a spoke subdomain already failed CORS before this change. Track it separately.
- Confirmed by the review:
  - every personal-room emit uses the user id the frontend joins;
  - the JWT checks match `JwtStrategy`, and REST auth is untouched;
  - there is no circular import;
  - credentials CORS is combined only with the explicit origin list;
  - **soft mode leaves an unchanged frontend working exactly as today**;
  - tenant scoping is intact.

## Verification
- backend:
  - `tsc --noEmit` is clean.
  - The gateway spec passes **18/18**.
  - Neighbouring suites (chat, connections, conversations, notifications, config) pass: 222 tests.
  - ESLint shows no new non-CRLF findings.
- **Real-SQL check of the membership query.** The SQL generated by TypeORM for `isUserParticipantOfConversation` was run against MariaDB 10.4 (XAMPP, a scratch DB dropped afterwards), with fixtures for each case:

  | Fixture | Result |
  | -- | -- |
  | native 1:1 as creator | allowed |
  | native 1:1 as to-user | allowed |
  | native group via `members` JSON | allowed |
  | CometChat import via the members table | allowed |
  | not a member (`members` `[420, 4]` must not match 42) | refused |
  | soft-deleted conversation | refused |
  | soft-deleted membership row | refused |

- frontend: `tsc -p tsconfig.app.json --noEmit` is clean.
- **Old-flow safety (2026-10-13):**
  - **DI:** a new `gateway.module.di.spec.ts` compiles the real `GatewayModule` graph (only the global `DataSource` is stubbed), so the app boots with the new gateway dependencies.
  - **Real socket.io e2e:** the real `FetchCountGateway` ran on a real socket.io 4.5.1 server, with the frontend's real socket.io-client 4.7.2. **24/24 checks passed.**
    - Soft mode, **old frontend (no cookie)**: connects, `joinRoom` works as today, and it receives fetch-count, notifications and presence with the client uuid. This proves the backend-only deploy changes nothing for current users.
    - Soft and enforce modes, **new frontend (cookie)**: connects, joins its own room, receives fetch-count, joins its own conversation, receives live messages and typing; another user's room and another conversation are refused; presence can't be spoofed.
    - Enforce mode: an anonymous socket is rejected.
  - **Frontend `reconnect()` (in-app login):** with the real socket.io-client, an anonymous pre-login socket is rejected in enforce mode; after the cookie is set, `disconnect()` + `connect()` on the **same** instance authenticates it. A `joinRoom` emitted during the reconnect is buffered and delivered, and listeners attached before login still fire. **4/4 checks passed.**
  - **Full backend jest suite:** no regression.
    - 71 suites and 1,183 tests pass.
    - 3 suites fail **identically without these changes** (pre-existing: `programs.repository`, `application-programs.repository`, `global-onboarding-design`).
    - `partner-domain-access` "expires the token in ~5 minutes" is a pre-existing 1 ms timing flake (TTL 300001 vs ≤ 300000). It passes 2 of 3 runs either way and doesn't touch sockets.
- **Boot safety:** the real Joi field and config loader, checked for `undefined`, `''`, `true`, `false`, `TRUE`, `' True '`, `yes` and `1`. Every value boots. Only the `true` variants enforce.
- **Builds:**
  - backend `nest build`: exit 0.
  - frontend production AOT `ng build --configuration production`: exit 0. It was run directly, not via `npm run build`, whose `postbuild` uploads source maps to Sentry.
- **Still to do before enforce:** the manual two-user smoke test on staging (see Test plan).
