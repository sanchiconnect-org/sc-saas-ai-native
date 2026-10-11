# SAN-668 — ngModel used on the same field as formControlName in book-facilitys

- **Linear:** SAN-668 (SC-SAAS-FRONTEND-V)
- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra (taken over from vishali kashyap) · **Classification:** CODE_ERROR

## Problem
Angular warns when `[(ngModel)]` is combined with `formControlName` on one element. Both the Start Date and End Date inputs in
`book-facilitys.component.html` did, and the warning reaches Sentry via the console.

## Fix
Removed both `[(ngModel)]` bindings. The End Date `[minDate]` now reads `meetingForm.get('date')?.value`, and the `endDate` `valueChanges`
handler reads the start date from the same control instead of `this.model`, because `this.model` is no longer updated by user picks.
`model` / `endDateModel` are still assigned elsewhere and are harmless.

## Contract impact
None. Frontend-only.

## Verification
- `tsc --noEmit` and `ngc` clean (ngc compiles the templates). No automated test added. Not checked in a browser, so the date-picker
  min-date behaviour on a real booking flow is unconfirmed.

## Commit
sc-saas-frontend `fcbfd1e50` on `ai_native_setup_aman`. Not deployed.
