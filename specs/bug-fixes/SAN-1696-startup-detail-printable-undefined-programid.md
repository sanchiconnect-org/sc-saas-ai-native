# SAN-1696 — Undefined variable $programId in startup-detail.php printable view

**Repo:** sc-saas-admin

## Problem
PHP warning `Undefined variable $programId in modules/startup-detail.php on line 2115`, reported from `https://sc-saas-admin-local-nirmal/startup-detail/914?printable=1`.

## Evidence
`modules/startup-detail.php:1929` opens the `printable=1` branch. `$programId` is only assigned inside a nested `if (isset($conditions[3]) && str_contains($conditions[3], "programId"))` at line 1957. A bare `?printable=1` visit has no `programId=` segment in the query string, so `$conditions[3]` is unset, that inner branch never runs, and `$programId` is never defined — but it's read directly (not via `$tpl->programId`, which the paired `else` at line 2090 does null out) at line 2114-2115 for a `program_startup_rounds_view` completed-rounds lookup.

## Root cause
CODE_ERROR — a variable used outside the only branch that defines it.

## Fix
Initialize `$programId = null;` at the top of the outer `printable=1` block (`modules/startup-detail.php`, right after line 1930), so it's defined on every path through the block regardless of which inner branch runs. With `null`, the Medoo lookup matches nothing — the correct, harmless outcome when no program context is present in the URL.

## Verification
`php -l modules/startup-detail.php` — clean. No automated test suite exists for this repo (PHP, no test framework) — noted per standing convention rather than bootstrapping one for this fix.

## Commit
`23a0ff03` on `sc-saas-admin`'s `ai_native_setup`.
