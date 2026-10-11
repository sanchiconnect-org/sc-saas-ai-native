# SAN-1145 — Startup Basic Information: mandatory geography fields bypassable + green tick with pending fields

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1145
- **Repo:** sc-saas-frontend · **Type:** Bug · **Priority:** High · **Assignee:** Mahima
- **Classification:** CODE_ERROR
- **Related:** SAN-1147 (backend half: nulls not persisted)

## Problem
On `/startups/edit/startup-information`:
1. The *Basic Information* tab showed a green tick while the footer said "2 field(s) are not complete
   yet" (City and Elevator Pitch empty).
2. After changing Country/State and refreshing, State/City/District/Sub-District rendered blank but
   were not treated as required, so Next Step unlocked. Sub-District still showed "Sabroom" while
   District looked empty.

## Evidence
- The tab icon came only from the backend `profileCompleteness` report. For Basic Information the
  backend criteria are `companyName`, `companyLogo`, `registeredCountryId` and
  `startupBusinessModels` only (`sc-saas-backend/src/modules/startup/repositories/startup.repository.ts`
  ~L1812). Elevator Pitch is counted under `pitch_deck`.
- Dev geography data (thub.sanchidev.in) is not empty: Iran has 31 states, and Arunachal Pradesh has
  26 cities and 25 districts. So the missing `Validators.required` was not because the lists were empty.

## Root cause
1. The nav tab never considered the page's live form validity.
2. The backend saved the geography IDs only when truthy (see SAN-1147), so stale child IDs from the old
   State survived in the DB. On reload the form patched those IDs. They aren't in the new parent's
   option list, so the ng-select rendered blank while the control held a value and passed
   `Validators.required`. The tenant default state was also applied even when it didn't belong to
   the selected country.

## Fix
- `startup-edit-page-nav-links.component.ts`: new `@Input() activeFormHasPendingFields`. When true,
  the active tab renders incomplete. Forward tab jumps are blocked, matching the disabled Next Step.
- `startup-information.component.html`, `financials-details.component.html`: bind
  `[activeFormHasPendingFields]="countInvalidFields > 0"`.
- `startup-information.component.ts`:
  - `getStates/getCities/getDistricts/getSubDistricts` ignore responses for a parent value that has
    since changed.
  - After a list loads, `clearValueNotInOptions()` clears a value that isn't among the options.
    It emits, so the parent cascade clears the children too.
  - `applyDefaultStateIfNeeded()` only applies the default state if it's in the loaded states.
  - Follow-up (with SAN-1147): `clearValueNotInOptions()` also calls `markAsDirty()` so auto-save
    persists the cleared value.

## Verification
- `tsc -p tsconfig.app.json --noEmit`: passes.
- Not yet tested in a browser. No regression spec added (see the proposal in the chat / Linear comment).

## Commit
sc-saas-frontend@c1ec4972 (branch ai_native_setup_mahima) — "feat: update startup edit navigation
links to reflect form validity state". The `markAsDirty()` follow-up is not yet committed.
