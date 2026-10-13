---
id: SAN-1873
title: "AxiosError 500 unhandled rejection still firing after SAN-988 (SC-SAAS-BACKEND-X)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1873
sentry: [SC-SAAS-BACKEND-X]
repos: [backend]
commit: sc-saas-backend@aaad005e (branch ai_native_setup_vishali, pushed) — .catch on 6 fire-and-forget ConvertAPIService call sites
created: 2026-10-12
updated: 2026-10-13
---

# SAN-1873: AxiosError 500, call site still unknown

## Investigation
* 107 events, `onunhandledrejection`, no stack; the latest is 2026-10-07.
* The SAN-988 `runCronJob` wrapper (`ef9051b9`) has been in the running build since the 2026-10-02 main merge, so the cron callbacks are not the source.
* SAN-455 `attachAxiosRequest` (`fe33f96e`), which adds the axios_host/method/status tags, reached main only on 2026-10-11 (PR #2027) and is not deployed yet.
* Ruled out: `WhatsappService.sendMessages` catches its own error, and all direct axios calls are awaited.

## Plan
1. After deploy, read `axios_host` on the next event.
2. At the named call site, add `await` or `.catch()` with an attributed log line.

No code change now, because the call site is unknown.

## Re-triage 2026-10-13
* **Redeploy confirmed.** Production restarted on main @ `6e7ca5c8`, which includes the SAN-455 `axios_host` tags, at about 2026-10-11 16:47 UTC (see SAN-1875). No BACKEND-X event has fired since. At the post-SAN-988 rate of about one every 5 days (2 events: 10-02 and 10-07, both on the old build), that silence proves nothing yet.
* **The SAN-988 cron wrapper fixed the bulk.** 59 events from 09-25 to 09-28, then the rate dropped right after the 10-02 deploy.
* **Remaining candidate, found by a backend-wide fire-and-forget audit.** `ConvertAPIService` (`src/core/services/convertapi.service.ts`) is the only HTTP client whose errors escape as a **raw `AxiosError`**, which matches the event type exactly. Every other outbound client wraps its errors in a Nest exception, swallows them, or is always awaited.
  * `convertPPTtoPNGs()` has no try/catch. Lines 45–50 are a stray class *method* named `catch`, not a catch block.
  * `inHouseConvertToPNGs()` and `inHouseDeleteConversion()` have no try/catch either.
  * Six call sites drop the promise:
    * `pitch-deck.service.ts`: the `savePitchDocument` and `addStartupPitchInfo` uploads call `convertAndSaveFileToImages` without `await`; the in-house cleanup inside it isn't awaited either.
    * `form-management.service.ts`: `cfaUploadPitchDocument` does the same, plus its in-house cleanup.
    * `resources.service.ts`: the in-house cleanup.
  * A 500 from the converter therefore surfaces as exactly `AxiosError: Request failed with status code 500` / `onunhandledrejection` / no stack.
  * **Not proven to be the source.** The sc-saas-3rdparty-webservices gateway (whose global filter reports every error) logged nothing at the 10-07, 10-02 or 09-28 event times. If this path is the source, it is the in-house converter (`CONVERTER_SERVICE_BASE_URL`, which has no Sentry project).

## Fix (sc-saas-backend@aaad005e)
Add `.catch((error) => this.logger.error('<op>() failed for <entity> <uuid>', error))` at the six fire-and-forget sites. The Nest `Logger` routes to `SentryLoggerService.error`, which calls `captureException(error, { extra: { loggedMessage } })`.
* **Unchanged:**
  * the request and its response: the upload response is already sent before conversion runs
  * the conversion and cleanup calls themselves
  * `ConvertAPIService`. It was left untouched on purpose, because changing what it throws would change the 500 response of the callers that do await it (`admin-actions.service.ts`, `convertDocumentToImagesForaStartup`, the resources controller).
* **Changed:** a converter failure becomes an attributed Sentry error naming the operation and entity, instead of an anonymous unhandled rejection. If BACKEND-X stops while these named errors appear, the source is confirmed.

## Verification
* `tsc --noEmit` is clean.
* ESLint: same 19 non-CRLF findings before and after, all pre-existing. Every CRLF `␍` finding is checkout noise.
* `src/modules/form-management` suite: 8/8 pass.
* Pitch-deck and resources have no existing specs, and **no new automated test was added** (workspace step 6 is blocked). Promise `.catch` semantics guarantee the rejection is handled.

## Closed 2026-10-13
SAN-1873 was marked Done in Linear after `aaad005e` was pushed. Reopen it if SC-SAAS-BACKEND-X fires again once this is deployed. Its `axios_host` tag will then name the real call site.
