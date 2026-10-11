---
id: SAN-960
title: Tripura Recognition Number edit doesn't sync to Certificates list
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-960
repos: [admin]
created: 2026-09-23
updated: 2026-09-23
---

# SAN-960 — sync an edited Tripura Recognition Number into the already-generated certificate row

## Request

Startup detail page → "Tripura Recognition Number" field → Save updates fine on that page, but the
Certificates list page (`/certificates/list`) keeps showing the old/stale number in its
"Certificate Name/Number" column for the same startup.

## Investigation finding

Confirmed by code, not assumption: this is a snapshot-vs-live-value mismatch across two separate
tables, not a caching or timing issue.

- **Write side:** `modules/startup-detail.php`'s `updateTripuraRecognitionNo` handler (~lines 354-424)
  wrote only to `startups.tripura_recognition_no`.
- **Read side:** `modules/certificates/list.php` renders `certificates.number` — a different column on a
  different table — and never reads `startups.tripura_recognition_no` live.
- **How `certificates.number` gets its value:** once, on the first "Generate Certificate" click, via
  `tripuraRecognitionNoGenerateIfMissing()` (`includes/tripura_recognition_no_functions.php`), which
  copies the then-current `startups.tripura_recognition_no` into `certificates.number` on insert. Every
  later "Generate" click for that startup only refreshes `issued_on`/`valid_till` on the existing row —
  `number` is never touched again by that path either.

## Root cause

`certificates.number` is a snapshot taken once at first issuance, with no code path that ever re-syncs
it from `startups.tripura_recognition_no` afterward.

## Fix

`modules/startup-detail.php`'s `updateTripuraRecognitionNo` handler, right after writing
`startups.tripura_recognition_no`: look up that startup's latest `certificates` row (same
`account_type = "startup"`, `account_profile_id = <id>`, `ORDER BY id DESC` lookup
`certificates/list.php`'s own upsert logic already uses) and, if one exists, update its `number` to the
new value. If no certificate row exists yet, nothing to do — the first "Generate Certificate" click will
read the live `startups` value already.

## Design decisions taken (not asked, judgment calls)

- **Update-on-save over live-join.** Two ways to fix this were on the table: (a) push the new value into
  any existing certificate row on save (chosen), or (b) make the Certificates list page look up the
  number live via a join instead of trusting its own stored column. (a) was confirmed with the user as
  the preferred direction — it's a smaller, more localized change (one write-side handler) and matches
  the existing precedent of `certificates.number` being a deliberately-stored, admin-correctable value
  elsewhere in this same module (the generic non-Tripura themes also store a snapshot, by design, per
  the module spec's own "Certificate issuance updates only issued_on/valid_till on re-issue" invariant).
- **Reused the exact "latest row" lookup convention** already established by
  `certificates/list.php`'s own upsert logic, rather than inventing a different one — keeps this change
  in sync with whichever row Generate would treat as canonical for that startup.

## Verified

- `php -l modules/startup-detail.php` clean.
- `git status --short` — only `modules/startup-detail.php` (this fix) and `modules/certificates/module.spec.md`
  (documentation) touched.
- Confirmed the "latest by id" lookup matches `certificates/list.php:44-52`'s own convention exactly.

## Not verified — genuinely outstanding

No live end-to-end test: this environment has no admin-panel login. Needs a real save-and-check on a
Tripura-themed startup that already has a generated certificate, confirming the Certificates list page's
"Certificate Name/Number" column updates immediately after the Recognition Number is saved.

## Rollout

Not committed. Awaiting review and a real test from the user.

## Open questions

None blocking.
