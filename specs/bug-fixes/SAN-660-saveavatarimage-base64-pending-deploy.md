---
id: SAN-660
title: "TypeError: Cannot read properties of undefined (reading 'base64') in saveAvatarImage — already fixed today, pending deploy"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-660
sentry:
  - SC-SAAS-FRONTEND-3K
repos: [frontend]
commit: "sc-saas-frontend@a66b15af (SAN-618), pending deploy"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-660 — saveAvatarImage crash, same root cause as SAN-618

## Root cause
Same root cause as SAN-618 (`PreviewAvatarComponent.saveAvatarImage()` called with
`imageCroppedEvent` still undefined — Save clicked before any crop event fired), just surfacing as a
different property-read message (`.base64` instead of the destructure) because the unused
`{width, height}` destructure got optimized away in the production bundle, leaving the `.base64` read
as the first thing to actually throw.

## Fix
Already fixed in commit `a66b15af` (SAN-618) — the `if (!this.imageCroppedEvent) { return; }` guard
precedes both the destructure and the `.base64` read, covering this variant too. Landed the same day —
squarely pending deploy.

## Verification
Confirmed the guard's placement precedes both crash variants.
