# Sentry sweep — 2026-10-26

* **Scope:** every Sentry project, `is:unresolved`, last 14 days: 34 issues.
* **Filed:** SAN-2019 to SAN-2022 and SAN-2024 to SAN-2035 in the Linear **Production Defects** project, milestone M5, all assigned to Vishali.
* **Code changes:** pushed to `ai_native_setup_vishali` after Vishali verified them, one commit per ticket:
  * tenants `01625da` (SAN-2022);
  * backend `238c53e7` (SAN-2021) and `1ff837bb` (SAN-2026);
  * frontend `08db8e130` (SAN-2030), `c2c995137` (SAN-2031), `865618f41` (SAN-2032), `e1aa558cd` (SAN-2033) and `8ba8388d7` (SAN-2034).

  None of this is on main yet, so none of it is deployed.

## Tickets

| Ticket | Repo | Sentry | Outcome |
|---|---|---|---|
| [SAN-2019](SAN-2019-dev-gateway-enforce-without-internal-key.md) | 3rdparty, backend | BACKEND-60..64, FRONTEND-HX | The dev gateway is in `enforce` mode with no key, so every email fails (login OTP, jury NDA). Ops fix; no code change. |
| [SAN-2020](SAN-2020-powerpitch-dev-redirect-loop.md) | backend | 5W, 59 | `dev-api.videopitchrecorder.com` redirects to itself (Cloudflare Flexible SSL). Ops fix; no code change. |
| [SAN-2021](SAN-2021-aws-sdk-drift-node16-getrandomvalues.md) | backend | 5Z, 5Y, 5X | The dev image pulled a Node-20-only AWS SDK onto Node 16. Pinned the 3 caret-ranged AWS SDK packages. |
| [SAN-2022](SAN-2022-tenants-health-interceptor-res-handler.md) | tenants | TENANTS-8, 9 | The interceptor and the exception filter broke on `@Res()` handlers. Added `headersSent` guards and 2 new specs. |
| [SAN-2024](SAN-2024-pending-connection-reminder-unrepairable-row.md) | backend | 5N | One tenant's template row can't be repaired. Data fix (ops); design decision pending. |
| [SAN-2025](SAN-2025-profile-views-nan-still-deploy-lag.md) | backend | 3M | Deploy lag: SAN-1872 is on `development` but not on `main`. No code change. |
| [SAN-2026](SAN-2026-create-membership-unhandled-rejection.md) | backend | 4F | A fire-and-forget `createMembership()` call had no catch. Now logged with the order; 2 new tests. Design decision pending. |
| [SAN-2027](SAN-2027-ses-throttle-quota-still-pending.md) | backend | 5R | The SES quota decision from SAN-1979 is still pending. No code change. |
| [SAN-2028](SAN-2028-analyzer-connection-lost-daily.md) | ai-analyzer | ANALYZER-7 | The SAN-1980 plan was never applied, and the bursts are now daily. Blocked: the repo isn't cloned. |
| [SAN-2029](SAN-2029-pdo-2002-laptop-and-redeploy-window.md) | admin, tenants-admin | ADMIN-F, TENANTS-ADMIN-4 | A developer laptop, plus one connection refused during a redeploy. No code change. |
| [SAN-2030](SAN-2030-accept-connection-409-unhandled.md) | frontend | 2J | An accept that returned 409 escaped to ErrorHandler. Now handled, with a status refresh. |
| [SAN-2031](SAN-2031-dashboard-v2-user-data-no-error-callback.md) | frontend | 1 | dashboard-v2 user data had no error callback. Added one. |
| [SAN-2032](SAN-2032-network-fault-echoes-call-sites.md) | frontend | HP, HV, HW, HS, 2W | Normalised the fault logging at the call sites and kept the email out of the HW log. The `beforeSend` filter is still pending a decision. |
| [SAN-2033](SAN-2033-disabled-attr-reactive-form-industry-technology.md) | frontend | Z | Removed 5 redundant `[disabled]` bindings. |
| [SAN-2034](SAN-2034-install-app-prompt-unhandled-rejection.md) | frontend | HT | `installApp()` now handles the rejection from `prompt()`. |
| [SAN-2035](SAN-2035-ngx-loader-master-dup-deploy-lag.md) | frontend | EP | Deploy lag: SAN-1993 isn't in prod. No code change. |

## Not ticketed
* **ADMIN-16** (`programs.application_target`): already fixed by SAN-2009 (`936cdbdd`), 10 minutes after the last event. I linked it in a comment on SAN-2009. It still needs promoting.
* **ANALYZER-4:** still open as SAN-1927 (In Review).
* **FRONTEND-17 (lightGallery) and FRONTEND-14 (moment):** noise, per board policy.

## Gates
* **sc-saas-backend:** lint, test, test-floors, openapi-floors, build and unguarded-routes all returned 0, so the run **passed**. 1704 tests (floor 1702).
* **sc-saas-frontend:** openapi-types, loader-floor, build, unit-tests and test-floors all returned 0, so the run **passed**. 1304 tests (floor 1295).
* **sanchiconnect-saas-tenants:** lint 0, test 1, test-floors 0, build 0, unguarded-routes 0.
  * The test failure is 3 generated-contract "is up to date" checks. They fail because this Windows checkout has `core.autocrlf=true`, so `contracts/generated/*.ts` have CRLF line endings. The failure is unrelated to SAN-2022.

## Decisions pending
* **SAN-2024 (product):** when a tenant's customised template fails to compile, should we fall back to the default template?
* **SAN-2024 (dev lead):** add an `app_domain` tag and `SENTRY_RELEASE` to backend Sentry events.
* **SAN-2026 (dev lead / Nirmal):** a membership order with no resolvable profile type: reject it at checkout, or derive the type on the server?
* **SAN-2027 (infra):** SES quota, staggered cron, or smaller batches.
* **SAN-2032 (dev lead):** should `beforeSend` drop HTTP 0 and 502/503/504 echoes, and also the thrown ones?
* **SAN-2019 (dev lead):** make the gateway key required at boot when the mode is `enforce`?

## Cross-cutting
* **Deploy lag is still the biggest lever.**
  * Backend `main` is from 2026-10-11, and frontend prod runs `218edca78`.
  * Several tenants (startupchhattisgarh, trise, firstwings, isba, ciicies, acicvgu, sineedge) run builds from July to September.
* **Dev hosts and laptops report into production Sentry projects.** That accounts for 4F, 5R, ADMIN-F, and all of HS and HV. Setting `SENTRY_ENVIRONMENT` per host would separate them.
* **PII:** the prod HW event has an applicant email in `extra.arguments`. Consider deleting that event.
