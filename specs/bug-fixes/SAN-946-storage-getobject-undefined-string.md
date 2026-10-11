---
id: SAN-946
title: SyntaxError "undefined" is not valid JSON in StorageService.getObject
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-946
sentry:
  - SC-SAAS-FRONTEND-EM
repos: [frontend]
commit: sc-saas-frontend@6c9802be (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-946 — StorageService.getObject() poisoned-key bug

## Root cause
`localStorage.setItem(key, undefinedVar)` (somewhere upstream) silently stores the literal string
`"undefined"` — truthy, so `getObject()`'s `(item) ? JSON.parse(item) : null` guard doesn't catch it,
but not valid JSON, so `JSON.parse` throws on every subsequent read of that key (1 user, 2 events).
This permanently poisons the key until it's cleared.

## Fix
`storage.service.ts`'s `getObject()` now treats the literal string `"undefined"` the same as a missing
key: `if (!item || item === 'undefined') return null;`.

## Related
Hypothesized (and confirmed plausible) to be the same root cause as SAN-948
(SC-SAAS-FRONTEND-2V, an uncaught promise on an `application-programs-management` code lookup that
reads from localStorage via this same service). Fixed once here rather than duplicating a guard at
the call site — see SAN-948's doc for the cross-reference.

## Blast radius
Low — this changes read behavior for any existing poisoned key (previously: hard crash on every read;
now: treated as absent). No legitimate stored value is ever the literal string `"undefined"`, so this
can't mask a real value.

## Verification
Re-read the file after editing. No automated test added — step 6 (tests-first) is blocked
workspace-wide (no `guardian` skill); substituted a direct code read. Whether SAN-948 is fully resolved
by this fix (vs. needing its own guard) was not independently confirmed with a live repro — genuinely
outstanding.
