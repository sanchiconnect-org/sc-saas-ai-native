---
id: SAN-977
title: "Meeting Scheduled" email — missing padding fix (workspace-wide sweep attempted, reverted)
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-977
repos: [backend]
created: 2026-09-24
updated: 2026-09-24
---

# SAN-977 — Join Meeting button padding + explaining the live "from...from `<b>`" bug

## Request

A received "Meeting Scheduled" email showed two visible defects: (1) "Join Meeting" button sitting flush
against its cell's left edge, no gap like Date/Time values have; (2) the sentence "You have scheduled a
meeting with QA Tester from   from `<b>`Book Store pvt ltd`</b>`, the details..." — "from" twice, and
`<b>`/`</b>` rendering as literal text instead of bold.

## Investigation finding

- **Padding bug: confirmed real, in the repo seed.** The Link row's value `<td>` in
  `meeting-scheduled-to-sender` (`spa_email_templates.repository.ts`) was styled
  `padding-top: 10px; padding-right: 10px; padding-bottom: 10px;` — missing `padding-left`, unlike every
  other cell (Date/Time use full `padding: 10px`). The template's own venue-text branch
  (`{{#if meeting_venue}}`) has spacing around its value; the Join Meeting button branch (`{{else}}`)
  only had a trailing `&nbsp;`, no leading spacing.
- **"from...from `<b>`" bug: NOT a code/repo bug.** Read the actual current repo seed template's static
  markup directly: `You have scheduled a meeting with <strong>{{ receiver_name }}</strong>{{{
  organization_name }}}, the details...` — no hardcoded "from" anywhere, and `{{{ organization_name }}}`
  already uses triple-stash (unescaped). `meetings.service.ts`'s `sendScheduledMeetingEmail()` builds one
  combined field: `organization_name: orgName ? \` from <b>${orgName}</b>\` : ''` (receiver-email variant
  at lines 285/319, sender-email variant at 436/477) — "from" and the `<b>` HTML are both baked into that
  single value by design; there's no second "from" placeholder anywhere for a template to duplicate.
  Given the repo code already produces one "from" and real bold (triple-stash doesn't escape), the live
  tenant's actual stored template has diverged from this seed — most likely hand-edited at some point in
  the admin's Email Management screen, either gaining a redundant static "from" in its own text, or
  regressing `{{{ organization_name }}}` to double-stash `{{ organization_name }}` (which would
  HTML-escape the baked-in `<b>` tags into literal text — exactly what was reported).

## Fix

`spa_email_templates.repository.ts`'s `meeting-scheduled-to-sender` seed: Link-row `<td>` changed from
three separate `padding-*` properties to a single `padding: 10px;` (matching every other cell), and added
a leading `&nbsp;` before the Join Meeting `<a>` tag (matching the trailing `&nbsp;` already there).

No code change for the "from...from `<b>`" half — nothing to fix in this repo for it. The live tenant
needs its stored template content re-pasted to match the (already correct) repo version, same category
of fix as SAN-970's `event-speaker-registration` live-template drift.

## Design decisions taken (not asked, judgment calls)

- **Used a single `padding: 10px` shorthand instead of adding just `padding-left: 10px`** to the existing
  three properties — simpler, and matches how every other cell in this same table already expresses full
  padding (a single `padding: 10px`, not four longhand properties), rather than introducing a second way
  of writing the same thing.
- **Did not audit or touch the other 40+ email send methods** that reuse the same
  `organization_name`-with-baked-in-`<b>` pattern for the same class of live-template-drift risk — flagged
  in the Linear issue and module spec as a known blast-radius note, explicitly out of scope here (would
  require checking each live tenant's actual stored template content, not just the repo seed).

## Verified

- `npx tsc --noEmit` clean; `git status --short` — only `spa_email_templates.repository.ts` (fix) +
  `meetings/module.spec.md` (docs) touched.
- Read the actual current repo seed template content directly (not from memory/assumption) before
  concluding the "from...from `<b>`" half needed no code change — same discipline as SAN-970's
  investigation, which caught a wrong assumption about a since-nonexistent CSS class earlier in this
  session.

## Follow-up: broader sweep attempted, verified working, then reverted per explicit request

Per request, extended the fix beyond `meeting-scheduled-to-sender` to the whole
`installDefaultEmailTemplates()` seed: grepped for every other double-stash `{{ organization_name }}`
occurrence (the same field, built the same pre-formatted-HTML way by multiple backend call sites), and
fixed each one to triple-stash. Found 19 raw substring matches; 2 were false positives (substrings
inside the already-correct triple-stash instances, since `{{{ x }}}` contains `{{ x }}` literally) — 17
genuine bugs, across 15 templates (`team-account-created`, `reject-connection` x2, `accept-connection`,
`connection-request`, `startup-investor-connection-request`, `investor-to-startup-auto-connection`,
`cron-incomplete-profile`, `partner-startup-account-created`, `partner-invite-startup-to-join`,
`meeting-requested`, `meeting-request-rejected`, `chat-message`, `reject-meeting` x2,
`startup-clarification-requested`, `program-round-clarification-requested`).

Each fix applied individually by exact byte-offset context (not a blind global replace), verified via
`tsc`/`eslint`/`git diff --stat` spot-check (32 changed lines, every one confirmed to contain only the
intended `{{ }}` → `{{{ }}}` change, nothing else touched).

**Reverted immediately after, per explicit request to narrow scope back to just the one template.** The
file was restored to its exact pre-sweep state via `git checkout`, then only the
`meeting-scheduled-to-sender` padding fix was re-applied fresh from a clean baseline (not by manually
un-doing 17 edits in place) — the safer way to guarantee no partial/mixed state, given this file's
templates live on a handful of extremely long lines where a mistargeted manual revert could easily
corrupt an unrelated template.

The 17-double-stash analysis itself remains valid and re-usable if this sweep is wanted again later —
recorded in the module spec rather than discarded, since the investigation work (which occurrences are
genuine, which are false-positive substrings) doesn't need to be redone from scratch next time.

## Verified (this follow-up)

- `npx tsc --noEmit` clean.
- `npx eslint` — same 2 pre-existing warnings + 2 pre-existing prettier errors (lines 391, 3712)
  confirmed identical before/after via `git stash` comparison — nothing new introduced.
- After the revert: `git diff --stat` back down to 1 file, 1 line changed — confirmed this matches
  exactly the original `meeting-scheduled-to-sender`-only fix, nothing from the sweep remains.

## Not verified — genuinely outstanding

No live test of the padding fix (no admin login in this sandbox). The live tenant's actual template
content that caused the "from...from `<b>`" bug was never read (no DB/admin access) — the diagnosis that
it has drifted from the repo seed is a strong inference from the repo code being internally consistent
and already correct, not a direct comparison against the live row's actual HTML.

## Rollout

Not committed. Awaiting review. Live template needs manual re-paste via Developer → Email Management for
the currently-affected tenant — a corrected full HTML snippet (matching the repo fix) should be handed to
the user the same way SAN-970's was.

## Open questions

None blocking.
