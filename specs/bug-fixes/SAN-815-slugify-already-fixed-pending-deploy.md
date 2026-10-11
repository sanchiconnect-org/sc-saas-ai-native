---
id: SAN-815
title: "slugify: string argument expected (main bundle) — already fixed via SAN-697, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-815
sentry:
  - SC-SAAS-FRONTEND-CQ
repos: [frontend]
commit: "none — already fixed via sc-saas-frontend@b0beac84 (SAN-697), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-815 — slugify string-argument crash, already fixed globally

## Root cause
Already fixed at `sc-saas-frontend/src/app/shared/utils/common-methods.ts:13-16` in commit `b0beac84`
(SAN-697, merged 2026-09-08, confirmed an ancestor of `origin/main`) — `createSlug()` now guards
`if (!name || typeof name !== 'string') return '';` before calling `slugify(name, ...)`. The guard
sits at the shared function definition, so it covers every `createSlug(...)` call site app-wide, not
just SAN-697's original one.

This issue's first/last-seen (~10 days ago, single-day burst of 70 events, no events since) lines up
with when the fix landed (2026-09-08) and shows no activity after — consistent with a stale,
already-resolved capture.

## Fix
No new code needed — the global guard at the shared function definition already covers this
fingerprint.

## Verification
Confirmed `b0beac84` is an ancestor of `origin/main` and reviewed the guard's placement relative to
all `createSlug()` call sites. No automated test added — step 6 (tests-first) is blocked
workspace-wide (no `guardian` skill).
