---
id: SAN-967
title: "Grant release letter formatting doesn't match the official Tripura reference letter"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-967
repos: [admin]
commit: sc-saas-admin@683caf00
created: 2026-09-23
updated: 2026-09-23
---

# SAN-967 — Grant release letter formatting mismatch

## Request

The downloaded Grant Release Letter PDF's visual formatting didn't match the real government reference
letter: no bordered box around the body paragraph or signature block, no bold labels ("Sub:", "Yours
faithfully", "Organization", "Applied Date"), no disclaimer line, and — once boxes were added — every single
line rendered with a spurious blank line beneath it.

## Root cause

`.letter-header`/`.letter-box` had `white-space: pre-wrap` set, while the PHP code also uses `nl2br()` to
build the HTML. `nl2br()` inserts `<br />` before each `\n` but does not remove the original `\n` — so with
`pre-wrap` also preserving that leftover `\n` as an independent line break, every line break was rendered
TWICE (once via the `<br>`, once via the preserved newline under `pre-wrap`).

## Fix

Iterated visually using a side-by-side HTML mockup (built and matched against the real reference letter
before touching the PDF code) rather than the previous cycle of blind PHP edits + re-downloading the PDF to
check. Once confirmed:
- Split the letter into header / boxed body / boxed signature sections (same graceful marker-based splitting
  already used for the signature block).
- Only "To" is bold in the address block (not the whole block); "Sub:" keeps a bold prefix with a plain
  rest-of-line; the signature block's own labels are bold while their values stay plain.
- Signature box widened to `min-width: 55%` to match the reference's proportions.
- Removed `white-space: pre-wrap` from `.letter-header`/`.letter-box` — the handler already creates explicit
  `<br>` tags everywhere a break is needed, so `pre-wrap` was only ever doubling them.
- Added the fixed disclaimer line: "**This application is printed electronically, so no signature is
  required**".

## Verification

`php -l` clean at every step. Visually confirmed against a published HTML comparison artifact, then against
the real downloaded PDF, by the user directly.

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-admin@683caf00`.

## Open questions

None blocking.
