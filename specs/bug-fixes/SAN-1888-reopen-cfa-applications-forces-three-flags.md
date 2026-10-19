# SAN-1888 — Re-opening CFA applications silently forces re-application, auto-communication and editable jury ratings ON

Linear: https://linear.app/sanchiconnect/issue/SAN-1888 · Repo: `sc-saas-admin` · Priority: High · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
`submitAction=reopenProgramApplications` (`modules/application_management/program.php`) cleared the closed state but also hard-set `editable_jury_ratings`, `allow_re_application` and `auto_communication` to `1`, overriding the admin's settings (automatic emails switched back on; rejected applicants allowed to re-apply).

## Evidence
- Ticket (dev, via backend `GET application-programs-management/code/{code}`): all three false before; unchanged after Close; all true after Re-open. Found by the sc-saas-e2e FT-006 P2 tests.
- Code: the three values were added in commit `26eaddf3` ("reopen application for program", Nirmal Singh, 2025-05-07) together with `program_closed => 0`, with no explanation. The legacy `create-program.php` reopen only clears `applications_closed`. The CFA Close Applications handler does not touch the three flags, so there is no round trip that needs them restored. The confirm dialog text only says new applicants can submit.

## Root cause
Unexplained forced values in the CFA reopen handler's `UPDATE`.

## Fix (`sc-saas-admin` only)
- `modules/application_management/program.php`: the reopen `UPDATE` now sets only `program_closed = 0` and `applications_closed = 0`.
- `modules/application_management/module.spec.md`: note that reopen must not touch the three settings.

## Not changed
- Programs already re-opened under the old code keep the three flags at 1 (no data migration; the previous values were never stored). An admin has to reset them in program settings.
- Legacy `create-program.php` close/reopen untouched (its close zeroes the three flags, its reopen does not restore them; out of scope).
- `themes/.../program copy.php` is an old template copy, not changed.

## Verification
- `php -l modules/application_management/program.php`: clean. `php tests/auth-gates.php`: 941/941.
- NOT done: live close/re-open on a program with the three flags off, and the FT-006 P2 e2e assertion (sc-saas-e2e is not in this workspace). No automated test (the handler is inline module code with no harness in this repo).

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
