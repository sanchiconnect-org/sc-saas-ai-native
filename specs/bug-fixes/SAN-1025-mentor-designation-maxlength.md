---
id: SAN-1025
title: "Mentor designation >120 chars only rejected by backend; mislabeled loginFault"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1025
sentry: [SC-SAAS-FRONTEND-G4]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1025

## Root cause (CODE_ERROR)
designation FormControl had no validators (backend MentorInformationDto @MaxLength(120)); mentors.service save faults logged as `loginFault`.

## Fix
Validators.maxLength(120) + inline error in mentor-intro; labels renamed patchMentorInfoFault / patchEngagementInfoFault.

## Existing-flow check
Mirrors backend exactly; nothing previously accepted is now blocked.

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
