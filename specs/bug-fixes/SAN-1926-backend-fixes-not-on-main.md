---
id: SAN-1926
title: "Backend fixes SAN-1872/1895/1874/1873 are not on main — prod (deployed 2026-10-11) still throws them (SC-SAAS-BACKEND-3M, 5Q, 9, X)"
type: bug-fix
status: todo
linear: https://linear.app/sanchiconnect/issue/SAN-1926
sentry: [SC-SAAS-BACKEND-3M, SC-SAAS-BACKEND-5Q, SC-SAAS-BACKEND-9, SC-SAAS-BACKEND-X]
repos: [backend]
related: [SAN-1872, SAN-1895, SAN-1874, SAN-1873, SAN-1754]
commit: none — deploy/release action, no code change
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1926: backend deploy lag

## Investigation
Prod backend containers started 2026-10-11 (Sentry `app_start_time`). That matches `origin/main` HEAD `6e7ca5c8` (merge of PR #2027 from stagingdemo, 2026-10-11 20:47 IST).

These fixes are on `ai_native_setup_vishali` but are **not** ancestors of `origin/main`:

| Sentry | Events (14d) | Fix | Commit |
|---|---|---|---|
| 3M `Unknown column 'NaN'` on `profile_views` INSERT | 96 | SAN-1872 | `acfeb44a` (2026-10-12) |
| 5Q `meeting.user.id` of null in `MeetingsRepository.getMeetings` | 2 | SAN-1895 | `60a20f65` (PR #2038, 2026-10-13) |
| 9 S3 `SignatureDoesNotMatch` (diagnostic tagging) | 11 | SAN-1874 | `1ad29b33` (2026-10-12) |
| X AxiosError 500 unhandled (ConvertAPI) | 4 | SAN-1873 | `aaad005e` (2026-10-13) |

The 5Q stack frame (`if (userIds.includes(meeting.user.id))`, `meetings.repository.js:363`) is the pre-fix code, which confirms the deployed build lacks the fix.

For 3M, the earlier fix SAN-1754 (`6b3f8945`) is on main but covers a different write site.

## Fix
No code change. Promote `ai_native_setup_vishali` → `development` → `stagingdemo` → `main` and redeploy.

## Verification
After the deploy, the four groups should stop. For BACKEND-9, the SAN-1874 tags (region/host/status) will then show the real misconfiguration; follow up on that separately.
