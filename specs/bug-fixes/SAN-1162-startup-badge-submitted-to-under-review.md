# SAN-1162 — Startup profile badge shows "Submitted" instead of "Under Review"

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1162
- **Repo:** sc-saas-frontend · **Type:** Bug · **Priority:** Low · **Assignee:** Mahima
- **Classification:** CODE_ERROR

## Problem
After a startup submits its profile for approval, the badge in the "Edit Startup / MSME Details"
header read "Submitted". It should read "Under Review".

## Evidence
- The badge is in `src/app/shared/common-components/startup-raise-fund-switch/startup-raise-fund-switch.component.html`
  (~L91), gated by `isUnderApproval`. Its popover already says "Profile under review by admin".
- The equivalent badges for individual, corporate, investor, mentor and program-office profiles
  already say "Under Review".

## Fix
Badge text `Submitted` → `Under Review`. The label is the only change.

## Verification
- Template text-only change. Not yet checked in a browser. No regression test (static label).

## Commit
Not yet committed. It goes on `ai_native_setup_mahima`.
