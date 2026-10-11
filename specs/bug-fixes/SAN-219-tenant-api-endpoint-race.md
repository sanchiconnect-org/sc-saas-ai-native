---
id: SAN-219
title: "Recurring 404 on /users/profile-types across multiple tenants — apiUrl/store-dispatch ordering race"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-219
sentry: [SC-SAAS-FRONTEND-H, SC-SAAS-FRONTEND-2J]
repos: [frontend]
commit: sc-saas-frontend@<pending, branch ai_native_setup_aman>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-219 — tenant apiUrl / brand-details dispatch ordering race

## Root cause
`ApiEndpointService.DOMAIN` (`src/app/core/service/api-endpoint.service.ts:12`) initializes to `environment.apiEndpoints.baseUrl` — the shared **cockpit** host (`https://api.tenants.sanchiconnect.com/` in production) — and is only repointed at the tenant's real backend once `ApiEndpointService.setApiEndPoint(apiUrl)` runs.

`TenantService.getTenantDetails()` (`core/service/tenant.service.ts`) previously called `setApiEndPoint()` nowhere itself — that call lived in `AppComponent.getTenantDetails()`'s own `.subscribe()` callback, which necessarily runs *after* the `tap()` operator inside `TenantService.getTenantDetails()`'s pipe, since `tap()` executes as part of the observable chain before the value reaches any external subscriber. That `tap()` is what dispatches `GlobalActions.SetBrandDetails(res.data)` to the NgRx store — the same store update that every other component in the app (correctly) treats as "tenant verified, brand details and `apiUrl` are known, safe to call the business API."

So there was a real window, one RxJS tick wide, where `getBrandDetails()` was already truthy in the store while `ApiEndpointService.DOMAIN` still pointed at the cockpit. `AppComponent` itself papered over this for its own `GetProfileTypes` dispatch with an ad-hoc `setTimeout(..., 2000)` (visible in `app.component.ts`, added for this exact reason per an existing comment referencing SAN-369) — but that buffer only protects that one call site. Any other component/service anywhere in the ~82-module app that reacts to brand details becoming available without the same defensive delay races the endpoint switch and hits `https://api.tenants.sanchiconnect.com/api/v1/users/profile-types` (the cockpit, which has no such route — that endpoint only exists on `sc-saas-backend`) instead of the tenant's real backend, producing exactly SC-SAAS-FRONTEND-H's 404. This can hit any tenant, which matches the ticket's "recurring across multiple tenants, escalating" pattern.

## Fix
Moved the `ApiEndpointService.setApiEndPoint(res.data.apiUrl)` call from `AppComponent`'s subscriber into `TenantService.getTenantDetails()`'s own `tap()`, immediately before the `SetBrandDetails` dispatch. This guarantees `DOMAIN` is always correct by the time *any* subscriber anywhere observes brand details as available, closing the race at its source rather than at one call site. Removed the now-redundant call (and the now-unused `ApiEndpointService` import) from `app.component.ts`; `socketService.setUrl()` there is untouched since it isn't implicated in this bug.

## Blast radius
`sc-saas-frontend`: `tenant.service.ts` (moved logic in) and `app.component.ts` (removed duplicate call + unused import). No behavior change for the correct/common case — `DOMAIN` ends up set to the same value either way. Only changes *when* it's set relative to the store dispatch, closing the race window entirely rather than narrowing it.

## Verification
`npx tsc --noEmit -p tsconfig.app.json` clean. No test suite covers this path; the ad-hoc `setTimeout` workaround already in `app.component.ts` for its own call site is left in place (harmless now that it's redundant, not worth touching in this pass).

## Rollout
Not resolving SC-SAAS-FRONTEND-H/2J outright — recommend watching both for recurrence for a few days post-deploy, since the race is timing-dependent and couldn't be reproduced deterministically in this session.

## Open questions
None.
