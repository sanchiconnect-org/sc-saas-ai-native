---
id: SAN-646
title: "TypeError: Cannot read properties of null (reading 'message') in login.component — already fixed, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-646
sentry:
  - SC-SAAS-FRONTEND-BK
repos: [frontend]
commit: "sc-saas-frontend@3791f938 (SAN-576), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-646 — null error-body crash on login, already fixed

## Root cause
`login.component.ts`'s `sendLoginRequest()` error callback did `err.error.message` unguarded — throws
when `err.error` is null (network/CORS error, no JSON body).

## Fix
Already fixed in commit `3791f938` (SAN-576, 2026-09-03) — changed to
`err?.error?.message || err.message || 'Something went wrong'` at `login.component.ts:110`. This
issue's last-seen (2026-08-29) predates the fix; given the frontend's known 17+ day prod deploy lag,
likely just not deployed yet rather than a live regression.

## Verification
Confirmed the guarded fallback chain covers this exact call site.
