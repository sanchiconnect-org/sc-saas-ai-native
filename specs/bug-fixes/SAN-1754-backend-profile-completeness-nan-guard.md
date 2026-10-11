# SAN-1754 — saved profile-completeness percentage can become NaN (0/0) and reach SQL as `Unknown column 'NaN'`

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1754 (Sentry SC-SAAS-BACKEND-3M)
- **Repo:** sc-saas-backend · **Priority:** High · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (unguarded division), root cause INFERRED

## Evidence
SC-SAAS-BACKEND-3M `Unknown column 'NaN'`: 188 events. An earlier commit `d254dc94` already added a 0/0 guard in `calculateCompleteness` plus `failedQuery` / `failed_table` diagnostics in `instrument.ts`.
A grep of the backend then found the same unguarded expression `Math.ceil((100 * completed) / total)` in nine more places (below), and `calculateQuantitativeMilestonePercent` divided by `targetValue` unguarded.

## Root cause (inferred, not proven)
When `total` is 0, `(100 * 0) / 0` is `NaN`. That value is written to the saved profile-completeness percentage; a bare `NaN` bound into an UPDATE is the inferred source of `Unknown column 'NaN'`.
The exact failing table was not observed (`failed_table` was not read from a live event), so which of these sites produced the Sentry events is unconfirmed.

## Fix
Each site now writes `0` when `total` is 0, otherwise the same `Math.ceil(...)` as before (no behaviour change for `total > 0`):
- `corporate.repository.ts` `getCorporateProfileCompleteness`
- `individual.repository.ts` `getIndividualProfileCompleteness`
- `investor.repository.ts` `getInvestorProfileCompletenessReport` and `getInvestorIndividualProfileCompleteness` (2 sites)
- `mentor.repository.ts` `getMentorProfileCompleteness`
- `partner.repository.ts` `getPartnerProfileCompleteness`
- `program-office-member.repository.ts` `getProgramOfficeMemberProfileCompleteness`
- `service-provider.repository.ts` `getServiceProviderProfileCompleteness`
- `startup.repository.ts` `getStartupProfileCompletenessReport`
- `src/core/utils/app.utils.ts` `calculateQuantitativeMilestonePercent`: `targetValue > 0 ? (100 * completedValue) / targetValue : 0`.

## Not fixed
- The root cause is not proven; this is hardening of every known 0/0 site. Whether a profile can legitimately have `total == 0` (for example no form fields configured for a tenant) was not investigated.
- Module specs updated with a dated bullet each (corporate, individual, investor, mentors, partner, program-office-members, service-providers, startup); no behavioural change beyond the guard.

## Contract impact
None. No controller or DTO change; the percentage field keeps its type and now simply never holds `NaN`. No flag, auth or tenant-scoping change.

## Verification
- `npx tsc --noEmit -p tsconfig.json`: exit 0.
- No automated test added (guardian skill blocked; strongest available check was the type-check). Not run against a database.

## Commit
sc-saas-backend `6b3f8945` on `ai_native_setup_aman`, pushed. NOT deployed.

## Sentry
SC-SAAS-BACKEND-3M resolved 2026-10-07 under the "fix in code => resolve" policy. Reopen on recurrence, then read the `failed_table` diagnostic to find the real table and check whether `total` is 0 there or the NaN comes from another source.
