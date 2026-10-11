# SAN-1147 — Startup profile keeps old State/City/District/Sub-District after Country/State change

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1147
- **Repo:** sc-saas-backend · **Type:** Bug · **Priority:** High · **Assignee:** Mahima
- **Classification:** CODE_ERROR
- **Related:** SAN-1145 (frontend half)

## Problem
The startup changed its Country to Aland Islands (no states or cities). The edit form cleared
State/City, but the public profile still showed "Badarpur, Jerusalem District, Aland Islands".

## Evidence
- The frontend payload is `{ ...startupInfoForm.value }`, so cleared levels are sent as explicit `null`.
- `StartupInformationDto` geography IDs are `@IsOptional()`, and the entity columns are `nullable: true`.
- `editStartupInformation()` skips the ID-existence checks when the value is falsy.
- `AuditedUpdateService.update()` passes the patch straight to `repo.update()`, so `null` becomes `SET NULL`.

## Root cause
`StartupRepository.updateStartup()` copied `registeredStateId`, `registeredCityId`,
`registeredDistrictId` and `registeredSubDistrictId` onto the patch entity only when truthy. An
explicit `null` was dropped, so the old IDs stayed.

## Fix
`src/modules/startup/repositories/startup.repository.ts`: the 4 fields now use `!== undefined`, the
same pattern `trlLevel` already uses in this function. `null` clears the field; an omitted key
leaves it unchanged.

## Contract impact
No DTO shape change. The other caller, `ImportService.importStartup` (fed by sc-saas-admin
`modules/ajax/stakeholder_export.php`), may send `null` State/City IDs. On a newly imported startup
there's no change. On an existing startup, a `null` now clears State/City, so the target matches
the source.

## Verification
- `tsc -p tsconfig.json --noEmit`: passes.
- Not yet tested end to end. No regression spec added (no existing `startup.repository` spec; see
  the proposal in the Linear comment).

## Commit
Not yet committed. It goes on `ai_native_setup_mahima` together with the SAN-1145 `markAsDirty()`
follow-up.
