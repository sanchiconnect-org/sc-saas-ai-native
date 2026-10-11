# SAN-1729 — Logged-out visitor on public program apply page redirected to login

**Linear:** https://linear.app/sanchiconnect/issue/SAN-1729 · **Repo:** sc-saas-frontend · **Type:** Bug (CODE_ERROR) · **Priority:** High · **Assignee:** Mahima Sharma

## Problem
Opening a public call-for-applications page (e.g. `https://thub.sanchidev.in/programs/apply/lau2124/launch-program`) while logged out: the page loads, then ~3 s later the visitor is kicked to `/auth/login` with an "Invalid access token" toast. Public apply must work without login.

## Evidence
- `POST api/v1/notifications/item-views` `{"itemType":"program","itemUuid":"805e8c3f-…"}` → `401 {"message":"Invalid access token"}`
- `GET api/v1/users/logout` → `401`

## Root cause
- `ProgramPublicApplyComponent` (route `programs/apply/:code/:slug`, no `AuthGuard`) starts `QualifyingVisitService.trackItemView(PROGRAM, …)` (SAN-1437). After 3 s it posts `notifications/item-views`.
- `QualifyingVisitService.enabled` only checked `notification_centre_enabled`, not whether a user is logged in.
- The backend endpoint is behind `JwtAuthGuard`, so an anonymous request returns 401.
- `AddTokenHeaderHttpRequestInterceptor` treats every 401 as session expiry: it clears storage, calls `authService.logout()` and navigates to `/auth/login`. `logout` is also JWT-guarded, hence the second 401.

## Fix
- `src/app/core/service/qualifying-visit.service.ts`: `enabled` now also requires a logged-in user (`StorageService` `user` key), so section and item trackers are no-ops for anonymous visitors.
- `src/app/core/http-interceptor/http-context-tokens.ts`: new `SKIP_UNAUTHORIZED_REDIRECT` context token.
- `src/app/core/http-interceptor/add-token-header.http-request-interceptor.ts`: a 401 on a request carrying that token is re-thrown, with no storage clear, logout or redirect.
- `src/app/core/service/notifications.service.ts`: `recordItemView` / `recordSectionVisit` use a new `silentTracking()` context (skips both the 403 and the 401 redirect). This is the backup for a stale localStorage `user` with a dead cookie.
- `src/app/core/service/qualifying-visit.service.spec.ts`: setup stubs `StorageService` as logged in, so the existing cases keep their meaning.

## Verification
- `tsc --noEmit -p tsconfig.app.json`: clean. The spec tsconfig shows no errors in the touched files.
- No lint config exists in the repo (no ESLint/TSLint config).
- Karma could not run: the test bundle fails to compile because of existing errors in unrelated spec files (investors/startups dashboards, search pages, certificate renderers, etc.). No automated regression test was added (pending go-ahead).
- Manual check to do: open the URL above logged out, wait more than 3 s, and confirm there is no item-views request and no redirect. Logged in: the item-view is still recorded.

## Commit
sc-saas-frontend `cdc2c0e3` on `ai_native_setup_mahima` (pushed 2026-10-06).
