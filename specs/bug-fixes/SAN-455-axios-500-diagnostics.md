# SAN-455 — AxiosError 500 with no first-party frame (diagnostics only)

- **Linear:** SAN-455 (SC-SAAS-BACKEND-X, 13 events)
- **Repo:** sc-saas-backend · **Assignee:** Aman kabra · **Classification:** NEEDS_MORE_INFO — NOT fixed

## Problem
`AxiosError: Request failed with status code 500`. Every axios call already uses `await` (SAN-988 audit) and cron jobs are wrapped in
`runCronJob`, yet the event carries no first-party frame, so which downstream (3rd-party gateway, PowerPitch, Zoho, CometChat) returned 500
cannot be determined from code.

## Change
`src/instrument.ts`: new `attachAxiosRequest()`, called from `scrubEvent`. For an AxiosError it adds tags `axios_host`, `axios_method`,
`axios_status` and `extra.axiosRequest {host, path}`. The query string and request/response bodies are not attached. The event is still sent
and grouping is unchanged.

## Still needed
Deploy, then read the tags on the next event and fix the downstream 500 it points to. The issue stays open until then.

## Contract impact
None. Sentry metadata only; no API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` clean. No automated test added.

## Commit
sc-saas-backend `fe33f96e` on `ai_native_setup_aman`. Not deployed.
