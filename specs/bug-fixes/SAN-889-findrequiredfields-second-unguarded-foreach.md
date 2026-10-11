---
id: SAN-889
title: "findRequiredFields still crashing after the 2026-09-22 fix — a second, unguarded sibling forEach"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-889/sentry-sc-saas-backend-36-findrequiredfields-crashes-on-multi-value
sentry: [SC-SAAS-BACKEND-36]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-889 (follow-up) — findRequiredFields' second unguarded forEach

## Root cause
The 2026-09-22 fix (`sc-saas-backend@5bc7a77e`) added a `sectionData.fields && sectionData.fields.length` guard to one `sectionData.fields.forEach(...)` call site in `app.utils.ts`'s `findRequiredFields` — the one inside the `multi_value_minimum` branch. Re-checked this issue today because it was still showing 1564 events with a "23 hours ago" last-seen despite that fix being live. Found a second, structurally identical `sectionData.fields.forEach(...)` call site in the function's sibling `else` branch (~line 470, reached when `sectionData.visiblity.field`/`condition` is `none`/`null`/unset) — this one was never guarded. Same crash (`Cannot read properties of undefined (reading 'forEach')`), same function, just a different code path through it, so the original fix only stopped half the crashes.

## Fix
Added the identical `sectionData.fields && sectionData.fields.length` guard to the second call site's `if` condition. Verified via grep that no other unguarded `.fields.forEach(` calls remain in this file — `formData.fields.forEach` (the outer loop) already had its own guard from before.

## Blast radius
Single function, single file (`app.utils.ts`). No behavior change for sections that already have a `fields` array — only the previously-crashing branch (a section with no fields array reached via the `else`/visibility-none path) now skips gracefully instead of throwing.

## Verification
`npx tsc --noEmit` clean. No test suite exists for `app.utils.ts` (per this repo's own established convention this session).

## Rollout
This should fully resolve SC-SAAS-BACKEND-36, unlike the first fix which only addressed one of the two code paths that could hit this crash.

## Open questions
None.
