---
id: SAN-1988
title: "S3 SignatureDoesNotMatch events are from a pre-fix process; quiet since the 10-14 deploy (SC-SAAS-BACKEND-9)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1988
sentry: [SC-SAAS-BACKEND-9]
repos: [backend]
related: [SAN-1874, SAN-454, SAN-1926]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1988: S3 SignatureDoesNotMatch

## Investigation
* **Last event:** 2026-10-11 11:57 UTC, production, host `ip-10-0-21-177`, `app_start_time` **2026-10-03**. That process predates the root-cause fix.
* **The event carries none of the SAN-1874 diagnostic tags** (`aws_region`, `aws_hostname`, `aws_status`, `app_domain`). That diagnostic, `1ad29b33`, is not on `origin/main` (`merge-base --is-ancestor` → no), so production never ran it.
* **The root-cause fix is in production.** `6b3f8945` (SAN-454, an ASCII-only `ContentDisposition` via `attachmentDisposition()`) has been on `origin/main` since 2026-10-07 (ancestor check → yes). The production backend processes restarted on 2026-10-14 (`app_start_time` on the 3M, 5R and 3P events). There has been no BACKEND-9 event since: last seen is 10-11, so the fixed build has been quiet for 8 days.

## Root cause
As the SAN-1874 re-triage found, a non-ASCII upload filename broke the signed `ContentDisposition` header. `6b3f8945` fixed that, and the remaining events were deploy lag.

## Fix
None in code.

## Blast radius / existing-flow impact
None (no change).

## Verification
* The branch checks and the Sentry event are quoted above.
* `npm run gates` for the slice: lint 0, test 0, test-floors 0, openapi-floors 0, build 1, unguarded-routes 0. The build failure is pre-existing and unrelated (see SAN-1976).

## Ops follow-ups
* Resolve SC-SAAS-BACKEND-9. It meets SAN-1874's criterion of 7 quiet days on a build from after 10-07.
* If it recurs, the `1ad29b33` tags only help once the backend branch is merged to main (SAN-1926).

## Related
SAN-1874, SAN-454, SAN-1926.
