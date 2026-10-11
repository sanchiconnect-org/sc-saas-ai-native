---
id: SAN-693
title: "loginFault( Stage type not found ) — mislabeled warn, same call site as SC-SAAS-FRONTEND-AS"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-693
sentry:
  - SC-SAAS-FRONTEND-AT
repos: [frontend]
commit: "none — mislabeling tracked at class level via SAN-448/471"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-693 — mislabeled console.warn, genuine backend rejection

## Root cause
`investors.service.ts:84-96` (`patchInvestorOrgInvestmentInfo()`) — same call site as
SC-SAAS-FRONTEND-AS, mislabeled `loginFault(` warn on the investments-details page. "Stage type not
found" is the backend rejecting an investment-stage id — same root-cause class as the mechanism-type
rejection in AS.

## Fix
No code fix needed for the mislabeling (tracked at class level via SAN-448/SAN-471/SAN-472 — a
workspace-wide `loginFault(` mislabeling pattern already documented as not worth piecemeal fixing).

## Related
SC-SAAS-FRONTEND-AS (identical call site/root cause, same page) — see SAN-689.

## Verification
Confirmed same call site as SAN-689/SC-SAAS-FRONTEND-AS via code read.
