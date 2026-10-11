# SAN-1675 — investor "Investment details" auto-save sends empty Instruments/Stages

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1675 (Sentry SC-SAAS-FRONTEND-AS 21 events / 7 users, AT 15 / 4, GN 2 events)
- **Repo:** sc-saas-frontend (backend contract noted, not changed) · **Priority:** Medium · **Assignee:** Aman kabra · **Classification:** CODE_ERROR

## Evidence — a repeat offender on the Saturday build
GN (`investmentInfoFault( Mechanism type not found )`) fired on release `bcf88383d` (the 2 Oct build, PR #1902) on sineedge.sineiitb.org on 5 Oct. AS (hub.startupsingam.com
`/investors/edit/individual-investments-details`, last seen 6 days ago) and AT (sineedge.sineiitb.org `/investors/edit/investments-details`, 12 days ago) are the earlier groups of the same
cause. No earlier fix targeted it: SAN-1036 fixed only the ticket-size pair.

## Problem
Saving investment details answers 404 `Mechanism type not found` or `Stage type not found`, nothing is persisted, and the failure is logged to Sentry (as `loginFault(...)` on one path, `investmentInfoFault(...)` on another).

## Root cause
`InvestmentsDetailsComponent.persistInvestmentInfo()` (one persist path for the 20 s auto-save tick, beforeunload and Next Step; the component serves both the organisation and the individual-investor routes) sent
`investmentMechanismIds` / `investmentStageIds` as `[]` for a half-filled form. The backend `InvestmentDto` declares both required ("Investment instruments are required", "should not be empty") but uses
`@IsNotEmpty`, which accepts `[]`. `InvestorService` then calls `getInvestmentMechanismsByIds([])` / `getInvestmentStagesByIds([])`, whose `find({ id: In([]) })` returns nothing and which throw
`NotFoundException('Mechanism type not found')` / `('Stage type not found')`. Validation runs before anything is saved, so the whole request is rejected.
(`InvestabilityMetricsRepository.getInvestmentMetricsByIds` has the same shape and a copy-pasted "Mechanism type not found" message, but nothing calls it.)

## Fix
New `required-selections.ts` with a pure `missingRequiredInvestmentSelections(info)` returning the labels of an empty Instruments / Stages selection. `persistInvestmentInfo()` calls it right after the existing
ticket-size guard: when something is missing it returns without sending the request, with a toast naming the missing selections only on the non-silent (Next Step) path. The form stays dirty, so the next auto-save tick
saves once the selections exist. Nothing is lost: those requests were already rejected before persisting.

## Not changed (contract owner decision)
Adding `@ArrayNotEmpty` to `InvestmentDto` would return the DTO's own 400 message instead of the confusing 404 for any API consumer, but changes the status for every client, so it needs `/audit-contract` and the
backend owner. Likewise correcting the unused metrics repository message.

## Contract impact
None. Frontend skips a request the backend always rejected; no API, flag, tenancy or auth change. Module spec updated: `src/app/modules/investors/module.spec.md` (InvestmentsDetailsComponent).

## Verification
- A node script transpiled the real `required-selections.ts` and ran 8 cases (both empty, each one empty, both chosen, `{}`, null/undefined fields, undefined and null object): all pass.
- Jasmine spec `required-selections.spec.ts` (5 tests) added; Karma cannot run in this repo at the moment (SAN-1653), so it is compile-checked only: `tsc -p tsconfig.spec.json` reports 0 errors in it.
- `tsc --noEmit -p tsconfig.app.json` and `ngc` exit 0. Not exercised in a browser.

## Commit
sc-saas-frontend `6fbffc17c` on `ai_native_setup_aman`. Not deployed.
