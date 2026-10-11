# SAN-1046 — dashboard-v2 search crashes reading 'type' of undefined userType

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1046
- **Repo:** sc-saas-frontend · **Type:** Bug · **Priority:** High · **Assignee:** Sandeep
- **Classification:** ENV_ERROR (deploy gap) — not a code defect

## Problem (as reported)
Sentry `SC-SAAS-FRONTEND-9G` — `TypeError: Cannot read properties of undefined (reading 'type')`
in the global-search Enter-key handler, `dashboard-v2.component.ts`. 30 events / 12 users, first
seen 2026-08-20, flagged by Sentry as "regressed."

## Investigation
The ticket's own proposed fix was to guard `this.userType` before reading `.type` at line 460.
Before writing that guard, checked the current tree first: `dashboard-v2.component.ts:448`
**already has it**:

```ts
if (e.code === 'Enter' && this.userType) {
```

This makes lines 460-464 unreachable whenever `this.userType` is falsy — the exact crash Sentry
reports cannot occur with this line present.

`git blame` traces the guard to commit `18eb14037b` ("fix(SAN-206, SAN-208, SAN-205, SAN-213): 4
null/undefined crashes across guards, forms, and search," Nirmal Singh, 2026-08-03) — which is
**SAN-205** (Done), the original fix for this exact defect. `git branch --contains 18eb14037b`
shows it on `ai_native_setup` and `ai_native_setup_sandeep`, but **not on `main`**;
`git show origin/main:.../dashboard-v2.component.ts` confirms `main`'s copy of line 448 has no
guard.

The Sentry issue's first-seen date (2026-08-20) is after the fix commit (2026-08-03), and its
"regressed" substatus is consistent with production still running a pre-fix `main` build, not a
reintroduced or uncovered defect in the current codebase — matching the workspace's known deploy-lag
pattern (`main` was measured 419 commits behind `ai_native_setup_sandeep` earlier this session).

## Fix
None. Writing another guard would duplicate SAN-205's existing fix. No files changed.

## Verification
N/A — no code change made.

## Next step
Not a bug-fix task: `ai_native_setup`/`ai_native_setup_sandeep` needs to be deployed to `main` for
this fix (and the other 418 commits) to reach production. Outside this ticket's scope.

## Commit
None — no code changed, nothing to commit.
