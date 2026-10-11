---
id: SAN-959
title: "getStartupProfileCompletenessReport() forEach crash — unguarded supportingDocuments relation on multi-collection join (root cause of SAN-942)"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-959
related: SAN-942
sentry:
  - SC-SAAS-FRONTEND-EW
repos: [backend]
commit: pending (uncommitted on ai_native_setup_vishali — user verifying locally first)
created: 2026-09-23
updated: 2026-09-23
---

# SAN-959 — unguarded supportingDocuments relation array (root cause of SAN-942)

## Root cause
`StartupRepository.getStartupProfileCompletenessReport()`
(`sc-saas-backend/src/modules/startup/repositories/startup.repository.ts:2057`, prior to fix) read
`startupInformation.supportingDocuments.forEach(...)` / `.some(...)` with no null guard, inside the
`Feature.STARTUP_SUPPORTING_DOCUMENTS` branch. The feeding query (~line 1821) does
`leftJoinAndSelect` on two one-to-many relations at once (`founders` + `supportingDocuments`) with
`.getOne()` — a known TypeORM footgun where multi-collection joins can leave a relation array
`undefined` instead of `[]` for some result rows. This function has no try/catch, so the raw
`TypeError: Cannot read properties of undefined (reading 'forEach')` propagated straight to NestJS's
default exception filter and leaked verbatim to the client via `GET /api/v1/startups/profile_completeness`
— the frontend symptom tracked as SAN-942 (`startupDashboard(...)` console.warn on the `/reports`
page, 48 users, 136 events).

## Fix
```ts
const supportingDocuments = startupInformation.supportingDocuments || [];
```
and use that local wherever the relation array was read (the `forEach` and the `some` inside it).
Purely additive/defensive — no behavior change when the relation does hydrate normally.

File changed:
- `src/modules/startup/repositories/startup.repository.ts:2056-2071`

## Blast radius
None — same completeness-percentage output for the normal case; only changes behavior for the
previously-crashing undefined case (now treated as "no supporting documents").

## Verification
`npx eslint src/modules/startup/repositories/startup.repository.ts --no-fix`: only pre-existing
repo-wide CRLF/prettier noise and pre-existing unused-var warnings, nothing attributable to this
change. No automated test added — Jest is available in this repo, deferred given the size of the
Urgent/High queue worked through in this session; noted as a gap.
