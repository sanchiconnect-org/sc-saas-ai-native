---
id: SAN-689
title: "loginFault( Mechanism type not found ) — mislabeled warn, genuine backend investment-mechanism rejection"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-689
sentry:
  - SC-SAAS-FRONTEND-AS
repos: [frontend]
commit: "none — mislabeling tracked at class level via SAN-448/471"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-689 — mislabeled console.warn, worth watching

## Root cause
`investments-details.component.ts` → `investors.service.ts:84-96` (`patchInvestorOrgInvestmentInfo()`)
— console.warn label is `loginFault(` despite having nothing to do with login; same copy-paste
mislabeling class already documented in `specs/bug-fixes/SAN-472-loginfault-user-not-found-pitch-deck.md`
(tracked at class level via SAN-448/SAN-471). "Mechanism type not found" is a genuine backend
validation rejection of an investment-mechanism id sent from the form — dropdown options are fetched
live via `globalService.getInvesmentTypes()` on page load, so this most plausibly means a stale page
held open across a mechanism-type change/removal, or a load/save race.

## Fix
No code fix needed for the mislabeling (tracked at class level elsewhere). If recurrence increases,
consider re-fetching/re-validating investment-type ids immediately before submit.

## Related
SC-SAAS-FRONTEND-AT — same call site, same mislabeling, same page (see SAN-693).

## Verification
Confirmed call site and cross-referenced the existing `loginFault(` mislabeling class documented in
SAN-472/448/471.
