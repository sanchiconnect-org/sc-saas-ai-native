---
id: SAN-1983
title: "loginFault( Internal Server Error ) on corporates/edit/corporate-intro is the corporate-info save, mislabeled (SC-SAAS-FRONTEND-AW)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1983
sentry: [SC-SAAS-FRONTEND-AW]
repos: [frontend]
related: [SAN-684, SAN-693, SAN-1025, SAN-1019]
commit: frontend@e2ce74be1 (branch ai_native_setup_vishali, pushed 2026-10-22)
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1983: corporate-intro "loginFault"

## Root cause
* Events: 5 events, one user, `thub.sanchidev.in` (dev, environment tag `local`), release `83f512778` (2026-10-15, on `ai_native_setup_vishali`), `level: warning`, `logger: console`.
* Source: `CorporateService.patchCorporateInfo()` (`core/service/corporate.service.ts:58`) logs `console.warn("loginFault( … )")`. The label is a copy-paste from the login service; the call is `PATCH api/v1/corporates/corporate-information`.
* The only caller is `CorporateIntroComponent.onSubmit()` (`modules/corporate/pages/edit/corporate-intro/corporate-intro.component.ts:354`). It runs on "Next Step" and on the 20 s auto-save, which explains 5 events in a short time.
* The frontend already handles it:
  * the service toasts "Error while saving corporate info!" (or the backend message);
  * the caller's error callback resets `savingCorporateInfo`.
  * Nothing is thrown unhandled. The Sentry issue is the console.warn echo of a backend 500.

## Backend side (read-only, for the backend agent)
* `PATCH api/v1/corporates/corporate-information` → `CorporateController.editCorporateInformation()` (`sc-saas-backend/src/modules/corporate/corporate.controller.ts:114`) → `CorporateService.editCorporateInformation()` (`corporate.service.ts:138`).
* Guards: `JwtAuthGuard`, `RolesGuard` (`Role.CORPORATE`), `Feature.CORPORATES`.
* The 500 is thrown inside the service. No matching backend Sentry issue was found by searching "corporate-information".

## Fix
* Relabeled the warn to `corporateInfoFault( … )` with a comment.
* Same relabel as SAN-1019 (investors `organizationInfoFault`) and SC-SAAS-FRONTEND-G4 (mentors `patchMentorInfoFault`).
* Future events group under an accurate name instead of a "login" issue.
* No behaviour change.

## Blast radius / existing-flow impact
* String change in one `console.warn`.
* Toasts, the request and the error flow are unchanged.
* No test references the string (`grep -rn loginFault src/app --include=*.spec.ts` → none).

## Verification
* `npx tsc -p tsconfig.app.json --noEmit` → exit 0.
* `npx tsc -p tsconfig.spec.json --noEmit` → exit 0.
* No unit test added: a log-label change, and `corporate.service` has no spec for this method.
* ESLint: no config in the repo.

## Open
* The backend 500 on `editCorporateInformation()` (the backend agent).
