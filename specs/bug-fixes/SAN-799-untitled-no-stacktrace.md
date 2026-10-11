---
id: SAN-799
title: "Untitled Sentry issue, no stacktrace — non-actionable"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-799
sentry:
  - SC-SAAS-FRONTEND-A0
repos: [frontend]
commit: "none — no diagnosable signal"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-799 — empty-payload Sentry group

## Root cause
Not diagnosable — Sentry captured this group with no exception type, message, or stack frames, so
there's nothing in the payload to trace to a source file. This shape (empty title, no stacktrace) is
typically a swallowed/malformed error object, a bridge/SDK edge case, or a non-Error value thrown that
Sentry couldn't serialize.

## Fix
No code change — not enough signal to act on. Consider a Sentry inbound filter for empty-title/
no-stacktrace groups if this keeps recurring.

## Verification
Confirmed via `get_sentry_resource` that the issue payload has no stacktrace or message.
