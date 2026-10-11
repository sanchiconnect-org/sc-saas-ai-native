---
id: SAN-855
title: "Fix malformed shortCodes JSON in default email-template seed data"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-855
repos: [backend]
commit: sc-saas-backend@4c715927
created: 2026-09-18
updated: 2026-09-18
---

# SAN-855 — backend seed-data typo behind SAN-851

## Request / context

Root cause of [[SAN-851]] (`sc-saas-admin` — malformed `shortcodes` JSON fatals the Email Templates admin page on
PHP 8), traced back here after the user pointed out email templates are actually created by the backend, not
hand-typed in the admin UI.

## Root cause (CODE_ERROR)

`src/modules/global/admin/spa_email_templates.repository.ts`'s `installDefaultEmailTemplates()` — a hardcoded
`defaultData` array (~89 entries use a hand-typed JSON string literal for `shortCodes`; 34 others use
`JSON.stringify([...])`, which can never produce invalid JSON, so those were never at risk). This method runs on
**every backend boot** (`GlobalService`'s constructor → `installMasterDefault()`, `global.service.ts:169`),
inserting any `templateCode` missing for that tenant straight from this array — this is why the "demo2" tenant's
`meeting-requested-moderation` row appeared with a timestamp matching a recent backend restart: that
templateCode simply hadn't existed for that tenant before, and got seeded fresh, with the bug already baked in.

Two entries had a missing closing `"` before the array's `]`:
- `meeting-requested-moderation` (was line ~3251): `..."brand_logo]` — the one that actually broke demo2.
- The `partner_name`-shortcode template under `EmailTemplateModuleType.PROGRAM_MANAGEMENT` (was line ~1322):
  `..."partner_name]` — same typo, not yet triggered on any known tenant.

## Fix

Closed both missing quotes. Verified programmatically: extracted every hand-typed `shortCodes` string in the
file and ran `JSON.parse()` on each — found exactly these 2 invalid, 0 invalid after the fix.

## Blast radius

Any tenant whose backend hasn't yet seeded these two templateCodes gets the corrected data on next restart.
Tenants that already got the broken row (e.g. demo2) are **not** retroactively fixed — `installDefaultEmailTemplates()`
only inserts missing rows, never corrects existing ones. Those still need the manual `UPDATE` documented in
[[SAN-851]].

## Verification

`npx tsc --noEmit -p tsconfig.json` clean. No regression test proposed — plain string-literal typo fix, not new
logic; `sc-saas-backend` has a working Jest setup but this doesn't warrant bootstrapping a repository-level test
for a one-character seed-data correction (would gladly write one if asked).

## Rollout

Committed and pushed to `ai_native_setup`: `4c715927`.

## Open questions

None blocking.
