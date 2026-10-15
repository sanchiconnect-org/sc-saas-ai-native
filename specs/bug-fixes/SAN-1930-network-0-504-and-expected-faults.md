---
id: SAN-1930
title: "Network-level 0/504 and expected-condition faults still reaching Sentry (SC-SAAS-FRONTEND-1, H3, HE, HF, 49, EX, 9A, 4A)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1930
sentry: [SC-SAAS-FRONTEND-1, SC-SAAS-FRONTEND-H3, SC-SAAS-FRONTEND-HE, SC-SAAS-FRONTEND-HF, SC-SAAS-FRONTEND-49, SC-SAAS-FRONTEND-EX, SC-SAAS-FRONTEND-9A, SC-SAAS-FRONTEND-4A]
repos: [frontend]
related: [SAN-804, SAN-567, SAN-1899, SAN-926, SAN-599, SAN-600, SAN-471, SAN-1669, SAN-1573, SAN-1928]
commit: sc-saas-frontend@0a09edb32 (branch ai_native_setup_vishali, pushed) — public-events component (ts+html) + 3 uploadLogo callers
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1930: status-0 / 504 / expected-condition fault cluster

## Investigation

| Sentry | Current code | Evidence |
|---|---|---|
| FRONTEND-1 `GET /v2/public/events/<uuid>` status 0 | **Unhandled. Fixed.** | `public-events.component.ts:190` subscribed without an error callback. The error reached Angular's ErrorHandler and the page stayed blank (template is `*ngIf="event"`). `global.service.ts:192` only rethrows. |
| HF `saveStartUplogo( HTTP 504 )` | **Unhandled. Fixed.** | `uploadLogo()` (`startup.service.ts:44-60`) toasts and rethrows. `startup-information.component.ts:1144` had `finalize` but no error callback. |
| H3 / HE `FINANCIALS save error` | Handled. The events are `console.warn` echoes. | `startup.service.ts:216-229` toasts. Caller `financials-details.component.ts:421` has `finalize` + an error callback (SAN-926). |
| 49 `startupDashboard( profile_completeness: 0 )` | Already fixed: SAN-567 `3cf4994d8` (2026-10-05). | `startup-dashboard.service.ts:64-70` only warns when `status && status < 500`. |
| EX `applicationProgramManagementApplicationDetails failed: 0` | Already fixed: SAN-1899 `ebde31ce4` (2026-10-14). | `program-public-apply.component.ts:399-419` try/catch skips 404/0. |
| 9A `loginFault( 0 Unknown Error )` | Handled in the UI; the warning still reaches Sentry. | `auth.service.ts:66` warns. `login.component.ts:102-111` and `login-modal.component.ts:115-121` have `finalize` + a toast. |
| 4A `loginFault( OTP expired )` | Already filtered. | The `HANDLED_HTTP_FAULT` regex in `src/main.ts` (SAN-599/600, `4e4bd3cb4`) has this exact string. |

## Fix
* **`public-events.component.ts`:**
  * added an `eventLoadError` flag, reset at the start of `fetchEventDetails`;
  * added an error callback that sets it.
* **`public-events.component.html`:** when `!event && eventLoadError`, shows "We couldn't load this event. Please check your connection and refresh the page."
* **`uploadLogo` callers:** added a no-op error callback with a comment, since the service already toasts and `finalize` stops the loader. Same one-line fix at all 3 callers with the same bug:
  * `startup-information.component.ts:1144`
  * `startup-all-required-details-form.component.ts:813`
  * `step-two-product.component.ts:224`

## Blast radius
* Success paths are unchanged.
* The only visible change is an error message where there used to be a blank event page.
* No backend or contract impact.

## Verification
* `npx tsc --noEmit` (app + spec): exit 0.
* `npm run gates`: exit 0.
  * openapi-types, loader-floor, build: pass.
  * unit-tests: 1103/1103 pass.
  * test-floors: pass.
* Not tested in a real browser.

## Recommended Sentry filter (not implemented, needs a decision)
* **Where:** `src/main.ts` `beforeSend`, next to the `HANDLED_HTTP_FAULT` block.
* **Rule:** drop an event only when all of these hold:
  * it has no exception;
  * `level === 'warning'`;
  * the message ends with `\(\s*(?:Http failure response for \S+: )?0 Unknown Error\s*\)$` or `\(\s*HTTP 0\s*\)$`.
* **Optional:** also 502/504. That would hide real outage signal, so it's a product call.
* Thrown `HttpErrorResponse` events are still reported, so missing handlers stay visible.

## Open (out of scope)
* `login-modal.component.ts:120` shows `err.error.message`, which is empty on a status-0 failure. Add fallback text.
* `public-events` `saveEventparticipation` stops the spinner on error but shows no message.
