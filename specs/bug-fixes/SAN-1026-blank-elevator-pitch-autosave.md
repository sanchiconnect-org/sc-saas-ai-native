---
id: SAN-1026
title: "Blank elevator pitch sent on auto-save / Next Step"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1026
sentry: [SC-SAAS-FRONTEND-CP]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1026

## Root cause (CODE_ERROR)
startup-information saveElevatorPitchSection() called by SAN-497 auto-save and onSubmit even when blank; backend @IsNotEmpty rejects.

## Fix
Early return when elevatorPitch is blank.

## Existing-flow check
pitchForm holds only elevatorPitch → no other field's save dropped; callers don't chain on it; error path never toasted → UX identical.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
