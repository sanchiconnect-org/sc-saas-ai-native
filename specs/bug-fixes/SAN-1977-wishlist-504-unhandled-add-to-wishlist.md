---
id: SAN-1977
title: "wishlist/:id/startup 504 reported as unhandled; failed Save/Remove left the spinner on (SC-SAAS-FRONTEND-2W)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1977
sentry: [SC-SAAS-FRONTEND-2W]
repos: [frontend]
related: [SAN-487, SAN-805, SAN-1760, SAN-1923, SAN-1930]
commit: frontend@f569f6c8a (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1977: wishlist 504 unhandled in add-to-wishlist

## Root cause
* Latest event: release `218edca78` (current `origin/main` tip, 2026-10-11), sineedge, `/mentors/profile/<uuid>/sanjay-mehta`, `handled: no`, mechanism `angular`. So this is current code, not deploy lag.
* The URL `wishlist/436/startup` is `GlobalService.getWhishlist()` (`global.service.ts:543`), which toasts and re-throws.
* Its only caller, `AddToWishlistComponent.fetchWishList()` (`shared/common-components/add-to-wishlist/add-to-wishlist.component.ts:44`), subscribed with no error callback. The 504 reached Angular's ErrorHandler and was reported as unhandled.
* Same file: `handleAddToWishlist()` and `handleRemoveFromWishlist()` set `loader = true` and only reset it on success. On a failure the spinner stayed on and both Save/Saved buttons stayed hidden (`*ngIf="... && !loader"`) until reload.
* The page itself does not break: the widget is a small bookmark button on profile pages.

## Backend side (read-only, for the backend agent)
* Route: `GET api/v1/wishlist/:userId/:userAccountType` → `ConnectionsWishlistController.getWishlist()` (`sc-saas-backend/src/modules/connections-wishlist/connections-wishlist.controller.ts:69`) → `ConnectionsWishlistService.getWishlist()` (`connections-wishlist.service.ts:33`) → `ConnectionsWishlistRepository.getWishlist()` (`repositories/connections-wishlist.repository.ts:70`).
* The query does 18 `leftJoinAndSelect`s (user + otherUser, each with all 8 profile relations: startup, investor, corporate, mentor, service_provider, program_office, partner, individual) and selects every column of every joined entity, then maps only a few fields. Likely cause of the gateway timeout for users with many wishlist rows. Not verified against the DB.
* Side note: the handler takes `userId` from the path and does not compare it with `req.user`. Any logged-in user can read another user's wishlist. Worth checking under `/check-isolation`.

## Fix
`add-to-wishlist.component.ts`:
* `fetchWishList()`: added a no-op error callback (the service already toasts), same as `partner-search-page` (SAN-487).
* `handleAddToWishlist()` / `handleRemoveFromWishlist()`: error callback sets `loader = false`.

## Blast radius / existing-flow impact
* Success paths are unchanged (same `next` bodies, moved into `{ next, error }`).
* On failure the user sees the existing toast and the button comes back instead of a permanent spinner.
* No API, flag, tenancy or auth change.

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → `tsc app exit 0`
* `npx tsc -p tsconfig.spec.json --noEmit` → `tsc spec exit 0`
* `npx ng test --watch=false --browsers=ChromeHeadless --include=<add-to-wishlist spec> --include=<program-code-details spec>` → `TOTAL: 15 SUCCESS` (3 new here: 504 fetch does not throw; success still sets `connectionItem`; add/remove failure clears `loader`).
* ESLint: not run. The repo has no ESLint config (`ESLint couldn't find an eslint.config.* file`), per its CLAUDE.md "lint: none configured".
* Not tested in a browser.

## Related
SAN-487 (same pattern, partner search), SAN-805 / SAN-1760 / SAN-1923 (other endpoints in the 2W group).
