---
id: SAN-1902
title: "Uncaught 504 on application-programs-management/code — already fixed by SAN-562"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1902
sentry: [SC-SAAS-FRONTEND-99]
repos: [frontend]
commit: none — no code defect, see Investigation
created: 2026-10-14
updated: 2026-10-14
---

## Investigation
The event release is `dab63831` (2026-09-03). In it, `checkProgramStatus()` awaited `fetchApplicationProgramsManagement().toPromise()` with no try/catch. Fixed by `617779519` (SAN-562). The other caller, `fetchWebinars()`, has had an `error:` handler since `f0484689f` (SAN-481). Both are on `origin/main` and in prod release `218edca78`. The 10-12 event is a stale cached PWA client.

## Fix
None needed. Resolve in Sentry once no events arrive on releases ≥ `218edca78`.
