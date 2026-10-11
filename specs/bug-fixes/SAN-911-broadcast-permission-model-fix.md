---
id: SAN-911
title: "Shared broadcast-ceo-message endpoint gates targeted profile/applicant messaging behind the wrong permission"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-911
repos: [backend, admin]
commit: sc-saas-backend@bfb12e95, sc-saas-admin@934bf3bc
created: 2026-09-22
updated: 2026-09-22
---

# SAN-911 — Broadcast permission model fix

## Request

`sc-saas-backend`'s single shared `POST v1/admin-actions/broadcast-ceo-message/:adminMd5` endpoint is called
from ~20 different `sc-saas-admin` pages for two genuinely different kinds of send: a handful of true
platform-wide broadcast composers (`broadcast_messages/create.php`, `broadcast_messages/approvals.php`,
`partners/broadcast/create.php`) and everything else, which is really "message a specific
profile/applicant/attendee" (every `*-detail.php` page — startup/partner/mentor/corporate/investor/
individual/service-provider/program-office — plus every application-management variant,
`growth_metrics/list.php`, `form_builder/submissions.php`, and the `events` module).

## Root cause

All ~20 callers were gated identically by a single `admin.canBroadcastMessages` check in
`AdminActionsService.broadCastCEOMessage()`. But the admin panel has a SEPARATE, narrower permission
specifically for this — `can_message_profiles` (surfaced in the admin UI as "Can Message Applicants?") —
which an admin can be granted without also being granted "Can Broadcast Messages?". A real production case:
an admin with "Can Message Applicants? = Yes" but "Can Broadcast Messages? = No" could not use "Email
applications" (or any of the other ~19 targeted-send pages) at all, even though that specific narrower
permission is exactly what should have gated it. The endpoint was conflating two distinct permission scopes
under one flag, with no way for a caller to signal which scope it actually needed.

## Fix

### Backend (`sc-saas-backend`)

- `dto/broadcast-ceo-message.dto.ts` — added an optional `requiresBroadcastPermission: boolean` field
  (defaults falsy).
- `admin-actions.service.ts`'s `broadCastCEOMessage()` — the permission check now branches:
  `requiresBroadcastPermission === true` requires `admin.canBroadcastMessages` (unchanged, original
  behavior); otherwise (the default) requires `admin.canMessageProfiles` instead.
- This means EVERY existing caller keeps working with zero admin-panel code changes needed, EXCEPT the 3
  true broadcast composers, which were updated (admin repo, below) to explicitly pass
  `requiresBroadcastPermission: true` to preserve their original stricter gate.

### Admin (`sc-saas-admin`)

Added `requiresBroadcastPermission: true` to exactly the 3 true broadcast composers (5 call sites total), so
they keep their original stricter gate unchanged; every other caller needs NO code change at all — it just
starts correctly accepting the narrower permission:

- `modules/broadcast_messages/create.php` — both its test-email send and its main send.
- `modules/broadcast_messages/approvals.php` — the Hub-approved Spoke broadcast send.
- `modules/partners/broadcast/create.php` — both its test-email send and its main send.

## Verification

- Backend: `npx tsc --noEmit -p tsconfig.json` clean. `npx eslint` on both touched files: 0 errors after
  `--fix` corrected one real formatting issue (a missing line break the initial edit introduced); remaining
  warnings are this repo's known pre-existing unused-import noise from single-file lint invocation. No
  automated regression test added — proposed but pending user go-ahead per the bug-fix process (this repo
  has a working Jest suite).
- Admin: `php -l` clean on all 3 touched files. This repo has no test suite/CI (per its own CLAUDE.md).

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-backend@bfb12e95`, `sc-saas-admin@934bf3bc`. Deploying the
backend alone is safe/backward-compatible since the new field defaults to requiring the narrower permission;
deploying admin alone without the backend change would send a field the old backend simply ignores — also safe
either order.

Discovered while investigating [[SAN-910-broadcast-email-applications-false-success]] — an admin with "Can
Message Applicants? = Yes" but "Can Broadcast Messages? = No" (`arushi.c@sanchiconnect.com`) couldn't send
"Email applications" at all, which traced back to this endpoint-wide permission conflation.

## Open questions

None blocking. Companion Linear issues: backend (SAN-911) and admin (SAN-912), cross-linked via `relatedTo`.
