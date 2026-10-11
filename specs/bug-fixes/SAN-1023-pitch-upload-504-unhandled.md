---
id: SAN-1023
title: "pitch-file upload 504 unhandled — spinner stuck, failed file shown"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1023
sentry: [SC-SAAS-FRONTEND-2W, SC-SAAS-FRONTEND-F7]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1023

## Root cause
CODE_ERROR in elevator-pitch.component.ts pitchDeckFileDroppedHandler(): no error callback. The 504 itself is backend/gateway (ENV) — not addressed here.

## Fix
Error callback: `uploading = false`, `selectedPitchDeckFile = undefined`.

## Existing-flow check
Already-uploaded deck renders from pitchObj (template prefers it) — unaffected.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
