---
id: SAN-829
title: "slugify crashes with \"string argument expected\" at unguarded call sites (our-partner, program-office-team, complete-profile)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-829
sentry:
  - SC-SAAS-FRONTEND-CQ
  - SC-SAAS-FRONTEND-CR
repos: [frontend]
commit: sc-saas-frontend@aa941ba1 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-829 — slugify unguarded call sites

## Root cause
`src/app/shared/utils/common-methods.ts`'s `createSlug()` helper already guards `!name || typeof name !== 'string'` (added under SAN-697 for SC-SAAS-FRONTEND-CK, a different call site — correctly resolved). But 3 call sites bypass the guarded helper and call the raw `slugify()` library function directly, with no guard:
- `our-partner.component.ts:72` — `slugify(partner.name)`
- `program-office-team.component.ts:62` — `slugify(e.name)`
- `complete-profile.component.ts:278` — `slugify(topic.topicName)`

Any null/undefined/non-string name (partner, team member, or pitch-deck topic) throws `Error: slugify: string argument expected` uncaught.

## Fix
Replaced the raw `slugify(...)` calls at all 3 sites with the existing `createSlug(...)` helper (same options: `replacement: '-', lower: true, strict: true, locale: 'vi', trim: true`), removing the now-unused direct `slugify` import from each file. No change in output for valid string inputs — only the null/type guard is added.

No API/DTO/flag/tenant-scoping impact — frontend-only, three call sites reusing an existing helper.

## Blast radius
`sc-saas-frontend` only: `our-partner.component.ts` (used on startup/partner listing pages), `program-office-team.component.ts` (program office team page), `complete-profile.component.ts` (startup pitch-deck topic routing).

## Verification
`npx tsc --noEmit` — 0 new errors (only pre-existing unrelated errors in vendor `cometchat-pro-angular-ui-kit` spec files). Full `ng build --configuration development` (AOT) — exit code 0, no errors or warnings referencing any of the 3 changed files. No automated test suite exists for this repo yet (workspace-wide test blocker per CLAUDE.md) — manual repro (render each component with a null/undefined name field) is the substitute verification, still to be done by hand before commit.

## Related
Same root pattern as SAN-697 (SC-SAAS-FRONTEND-CK) — that fix guarded the helper itself but didn't audit for other direct `slugify()` callers, which is what this ticket closes out.
