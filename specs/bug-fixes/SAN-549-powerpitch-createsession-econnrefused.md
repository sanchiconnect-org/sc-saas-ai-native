---
id: SAN-549
title: "PowerPitch createSession leaks raw axios error — external dev-api DB unreachable"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-549
sentry:
  - SC-SAAS-BACKEND-2C
  - SC-SAAS-BACKEND-2D
  - SC-SAAS-BACKEND-X
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-549 — PowerPitch createSession error handling

## Root cause

Two separate things bundled under one incident:

- **ENV_ERROR, not fixable here**: `PowerPitchExternalService.createSession()` calls the external
  `power-pitch-sanchiconnect-api` dev environment (`dev-api.videopitchrecorder.com`), which returned
  HTTP 500 because *its own* MySQL was unreachable (`ECONNREFUSED 127.0.0.1:3306`). Root cause lives
  in the sibling SanchiPowerpitch workspace, outside this repo.
- **CODE_ERROR, fixed**: `createSession()`'s catch block threw the raw axios `error` object via
  `InternalServerErrorException(error)` — inconsistent with the other methods in the same file
  (`createVideo`, `getVideo`, `getOrGenerateTranscript`, `getTranscriptStatus`), which all sanitize
  into a clean message first.

SC-SAAS-BACKEND-X (a generic `AxiosError` with no stacktrace) shares the exact same `trace_id` as
2C/2D — same incident, likely a duplicate capture via Sentry's unhandled-rejection integration, not
a separate defect.

## Fix

`power-pitch-external.service.ts`'s `createSession()` catch block now builds
`Powerpitch create-session failed (HTTP <status>): <remoteMsg>` before throwing, matching the
sanitization pattern already used by its sibling methods.

## Blast radius

None — only the error message shape changes; success path and every other method untouched.

## Verification

`tsc --noEmit` clean. A regression test was written and confirmed failing pre-fix / passing post-fix
during triage, then removed at the user's request to keep the diff to one file.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge. Root cause (the external outage) remains unresolved — needs the PowerPitch team.
