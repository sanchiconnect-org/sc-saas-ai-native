---
id: SAN-1000
title: "Custom profile form tab shows green tick while geography picker's mandatory Country/State/City are empty"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1000
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup>
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1000 — geography picker mandatory sub-fields ignored by backend completeness

## Problem
The startup profile custom form tab "Program Office" showed a green tick, while the form's own badge said "3 field(s) are not complete yet" (the geography picker's Country*, State* and City* were empty).

## Root cause
The tab tick comes from the backend completeness `missingFields`, built by `findRequiredFields()` + `calculateCompleteness()` in `sc-saas-backend/src/core/utils/app.utils.ts`. `findRequiredFields()` only picks fields with `field.required == 1`. A geography picker's mandatory setting is stored per sub-field in `geography_settings` (`{country,state,city}_visible` / `_mandatory`), and the stored value is always an object (truthy). The frontend (`updateEmptyRequiredFieldsCustomForms` in `sc-saas-frontend/src/app/shared/utils/form.utils.ts`) checks each sub-field, so the two disagreed. Classification: CODE_ERROR.

## Fix (all profile completeness reports; applications / data-collection untouched)
- `sc-saas-backend/src/core/utils/app.utils.ts`: new `getGeographyRequiredCriteria(field, formData)`, one criterion per geography sub-field that is both visible and mandatory. The key is `["<field.key>"]?.registered_<part>_id`, evaluated by `calculateCompleteness` as `data?.["key"]?.registered_country_id`. The message is `<name> - Country|State|City is required --*--<uuid>(<title>)`, so the frontend's `getMissingFieldsMap` groups it under the form's tab.
- `findRequiredFields(forms, options = {})` takes an opt-in `options.checkGeographySubFields`, which is off by default.
- Opted in (`{ checkGeographySubFields: true }`) in every profile completeness report:
  - startup (`getStartupProfileCompletenessReport`)
  - mentor (`getMentorProfileCompleteness`)
  - investor (`getInvestorProfileCompletenessReport`, `getInvestorIndividualProfileCompleteness`)
  - corporate (`getCorporateProfileCompleteness`)
  - partner (`getPartnerProfileCompleteness`)
  - service provider (`getServiceProviderProfileCompleteness`)
  - program office member (`getProgramOfficeMemberProfileCompleteness`)
  - individual (`getIndividualProfileCompleteness`)

## Blast radius
- Unchanged (no option passed, identical code path): the program application "form submitted" flags (`application-program.service.ts`, `program-management.service.ts`), `vs-programs-management.service.ts`, and the data-collection trigger in `form-management.service.ts`.
- Changed (intended): every profile type's completeness report. An empty mandatory geography sub-field in a profile custom form now means a red tab and a lower %. Everything that reads the profile report follows it: the completeness widgets, approval-request / raise-funds / providing-funds eligibility, `incomplete-step-forward.guard`, and the program "required details" check. All profile-edit nav tabs share `getMissingFieldsMap`.

## Verification
- node check of the eval'd key: null or missing sub-field is falsy, a filled one returns the id.
- `tsc --noEmit`: clean. `eslint` on both files: 0 errors (warnings that were already there). `prettier --check`: clean.
- No automated test added. Not yet verified against a running app.
