# SAN-348 — Auto-apply after register skips the approval-pending check

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-348
- **Repo:** sc-saas-frontend · **Priority:** High · **Assignee:** Nirmal Singh · **Classification:** CODE_ERROR

## Problem
With `approved_startups_can_apply_on_programs` on (SAN-337), an unapproved startup must not be able to apply.
Every apply surface blocks it, except one: a startup that registers straight into a program
(`?fromRegister=true&code=…`) has its apply request sent without any check. The backend rejects it
(ForbiddenException), but the frontend swallows that error, so the user sees nothing.

## Evidence
The August record of this issue says the guard was added, but it was never committed: no commit on any branch of
sc-saas-frontend ever contained it (`git log --all -S`), and `applyForProgram()` on both `ai_native_setup` and `main`
had no approval check.

## Root cause
`ProgramPublicApplyComponent.applyForProgram()` (`src/app/modules/programs/program-public-apply/program-public-apply.component.ts`)
has no approval check. Its only caller is `getAppliedPrograms()`'s post-register auto-apply branch, which has no
button whose disabled state could stop it. The other paths go through `checkApprovalEligibility()`:
the manual click (`handleApplyButton()`) and `?autoStatusCheck` (`fetchWebinars()`).

## Fix
`applyForProgram()` now calls `checkApprovalEligibility(true)` right after the "already applied" redirect, so an unapproved
startup is stopped and shown the same "Approval Pending" popup as the `?autoStatusCheck` path. Approved startups,
other account types and tenants without the flag are unchanged (`approvalPendingForApply` is false for them).

## Verification
- `tsc --noEmit -p tsconfig.app.json` clean.
- No automated test yet (proposed, waiting for go-ahead; karma can't currently run because unrelated specs fail to compile, see SAN-1653).
- Not checked in a browser.

## Commit
sc-saas-frontend `4de7bad2` (on `ai_native_setup`)
