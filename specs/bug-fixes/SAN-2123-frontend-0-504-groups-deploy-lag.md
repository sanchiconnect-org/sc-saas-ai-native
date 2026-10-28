---
id: SAN-2123
title: "FRONTEND-1 / 2W / HV / EX still firing from prod release 218edca78 — SAN-2031 / SAN-2032 not on main"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2123
sentry: [SC-SAAS-FRONTEND-1, SC-SAAS-FRONTEND-2W, SC-SAAS-FRONTEND-HV, SC-SAAS-FRONTEND-EX]
repos: [frontend]
related: [SAN-2031, SAN-2032, SAN-1930, SAN-1899, SAN-1977]
commit: none — deploy lag
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2123: deploy lag

## Investigation
Prod frontend is on `218edca78` (2026-10-11, still the tip of origin/main).

| Fix | Commit | development | stagingdemo | main |
|---|---|---|---|---|
| SAN-2031 | `c2c995137` | yes | yes | no |
| SAN-2032 | `865618f41` | yes | yes | no |
| SAN-1930 | `0a09edb32` | yes | yes | no |
| SAN-1899 | `ebde31ce4` | yes | yes | no |
| SAN-1977 | `f569f6c8a` | yes | yes | no |

* Prod events on `218edca78`: 2W ×8, 1 ×6, HV ×3, EX ×2.
* Releases that contain the fixes (`313e52bc5`, `d1dbe8d92`) appear only in the FRONTEND-1 catch-all (3 local events and 1 dev event).
* Not checked: which endpoints those 4 events hit.

## Open (ops)
Promote stagingdemo → main and redeploy prod.
