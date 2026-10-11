# SAN-1003 — Same-title custom-form tabs share missing fields

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1003
- **Repo:** sc-saas-frontend · **Type:** Bug · **Priority:** Medium · **Assignee:** Mahima Sharma
- **Related:** SAN-1000 · **Classification:** CODE_ERROR

## Problem
A startup profile had two custom forms both titled "testing form". The first was fully filled but
its tab still showed a red ⓘ. The "Missing fields" popup listed "location - Country/State/City is
required" under "testing form", but those fields belong to the *other* same-title form.

## Root cause
`getMissingFieldsMap()` (`shared/utils/common-methods.ts`) grouped missing fields by form title,
and every profile nav-links component matched tabs with `group.key === link.title`. Custom forms
with the same title merged into one group. The backend message already carries the form uuid
(`--*--<uuid>(<title>)`), but it wasn't used for matching.

## Fix
- `shared/utils/common-methods.ts`:
  - `getMissingFieldsMap()` groups by a new `groupId`: the form uuid for custom forms, the title otherwise. `key` stays as the title for display.
  - New `findMissingFieldsGroupForLink(missingFields, link, titleOverride?)`: matches custom-form tabs by uuid (`link.uuid`, else `/custom-forms/<uuid>` in the route) and standard tabs by title. Falls back to `key` for groups built without `groupId`, e.g. hand-built groups in specs.
- Swapped the title lookup for the helper in:
  - `shared/guards/incomplete-step-forward.guard.ts`
  - nav-links: startup, corporate, partners, individual, service provider, mentor, program office, investor, and individual investor (keeps its "Investment Thesis" → "Investment Details" override)
  - `programs/.../program-details-edit-page-links`

## Known leftover
In the guard, `LiveCompletionOverrideService.isConfirmedComplete(prefix, link.title)` is still keyed
by title. It's only a "just saved" fallback.

## Verification
- `npx tsc --noEmit -p tsconfig.app.json`: clean
- node check of the matching logic: filled same-title form → no group; empty one → its group; standard and legacy groups unchanged
- Not verified in a browser; no new automated test added

## Commit
sc-saas-frontend@7871102d (branch ai_native_setup_mahima)
