---
id: SAN-910
title: "Email applications broadcast shows false success + phantom recipient count on backend failure"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-910
repos: [admin]
commit: sc-saas-admin@ec5ae05d
created: 2026-09-22
updated: 2026-09-22
---

# SAN-910 — Broadcast email (Application Management) false success + phantom recipient count

## Request

User reported (via screenshots of `adm.sineedge.sineiitb.org`): using "Email applications" on an Application
Management submission page shows a broadcast in the Broadcast Messages list with a nonzero "Total Recipients"
count (e.g. 1, 2, 80, 89), but clicking into that broadcast's Details page shows 0 Total Recipients / 0 In
Progress / 0 Bounced / 0 Delivered / 0 Opened and "No recipients found for this broadcast."

## Context

Two compounding defects in `sc-saas-admin/modules/application_management/submission-application-management.php`:

1. The list page's "Total Recipients" column is a raw `broadcast_messages.total_receivers` column, written
   from the LOCALLY-filtered recipient count BEFORE the backend send call even happens (line ~1074). The
   Details page instead runs a live query against `ses_email_queue` filtered by `broadcast_message_id` — real
   rows that only get created if the backend's `v1/admin-actions/broadcast-ceo-message/:adminToken` call
   actually succeeds end-to-end.
2. The code that was supposed to detect whether that backend call succeeded (`$apiOk`, ~line 1136) checked
   for `success`/`status` response keys that neither a real success body (`{message}`) nor a real error body
   (`{statusCode, message, error}`) ever contains — so it was always `false`, AND (more importantly) it was
   never actually used to gate the JSON response sent back to the browser. The admin always saw "Message
   queued for N recipients" regardless of whether the backend call actually succeeded, failed on a permission
   check, or threw for any other reason. When it does fail, zero `ses_email_queue` rows are ever created, and
   the already-inserted `broadcast_messages` row is left behind with a `total_receivers` count that was never
   really sent — exactly the list-vs-details mismatch reported.

Confirmed via comparison with the codebase's own correctly-implemented sibling, `broadcast_messages/create.php`
(lines 1088-1091), which correctly detects failure via `json_last_error()` + `statusCode >= 400` — proving the
fix pattern already exists elsewhere in this repo, this call site just never adopted it.

## Fix

`submission-application-management.php`:
- Rewrote the `$apiOk` computation to mirror `broadcast_messages/create.php`'s correct check: decode the
  response, and treat `statusCode >= 400` (or a JSON decode failure, or no response at all) as a real failure
  with a real `$apiErrorMessage`.
- Added a new gating block: when `$apiOk` is false, delete the already-inserted `broadcast_messages` row (so
  it doesn't sit forever in the list looking like a real send that never happened) and return a real error
  (`"Broadcast failed: " . $apiErrorMessage`) to the admin instead of a false success toast.

Two-part fix was a deliberate product decision (confirmed with the user via AskUserQuestion): on a genuine
failure, delete the phantom `broadcast_messages` row rather than leaving it as a permanent stub record.

## Verification

`php -l` clean. This repo has no test suite/CI (per its own CLAUDE.md) — verified by reading the exact
response shapes on both the success path (`admin-actions.controller.ts` `broadCastCEOMessage()`) and the
error path (NestJS's default `{statusCode, message, error}` exception body) to confirm the new check is
unambiguous, and by comparing against the working sibling file's already-correct pattern. Root cause was
independently traced end-to-end (admin PHP send handler → cURL helper → backend controller/service/DTO →
`SesEmailQueueEntity` persistence) across two research passes before implementing, to rule out a systemic
backend issue vs. a call-site-local one — confirmed local to this one file.

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-admin@ec5ae05d`.

## Postscript — the real-world failure this fix surfaced

Once this fix was live in principle (verified against a real production case before pushing), the user traced a
genuine failing broadcast to its actual cause: the admin sending it (`arushi.c@sanchiconnect.com`) had "Can
Broadcast Messages?" = No. Investigating why an admin with the seemingly-relevant "Can Message Applicants?" = Yes
permission still couldn't send "Email applications" led to a second, deeper bug — the shared backend endpoint was
gating ~20 different targeted-send admin pages behind the wrong permission entirely. See
[[SAN-911-broadcast-permission-model-fix]] for that fix.

## Open questions

None blocking — the one design decision (delete the phantom `broadcast_messages` row on failure vs. leave it
as a stub) was resolved via `AskUserQuestion` during implementation; see Fix above.
