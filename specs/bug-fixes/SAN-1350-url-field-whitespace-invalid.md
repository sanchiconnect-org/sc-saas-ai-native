---
id: SAN-1350
title: "Dynamic form URL field rejects valid link with leading/trailing whitespace (\"Please enter a valid URL\")"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1350/dynamic-form-url-field-rejects-valid-link-with-leadingtrailing
sentry: []
repos: [frontend]
commit: frontend@25e0d4a1 (branch ai_native_setup_vishali, pushed)
created: 2026-10-01
updated: 2026-10-01
---

## Root cause

On the public program-apply form (`/programs/apply/:code/:slug`), dynamic-form URL fields (e.g. "Website") are validated with `Validators.pattern(HTTPS_REQUIRED_URL)` (`sc-saas-frontend/src/app/shared/utils/form.utils.ts` → `addValidator`, regex in `src/CONSTS.ts`). The regex is anchored `^...$` and allows no whitespace, so a copy-pasted link with a leading or trailing space or newline fails:

| Input | Result |
|---|---|
| `https://adm.thub.sanchidev.in/table/application_programs` | valid |
| same + trailing space | **invalid** |
| leading space + same | **invalid** |
| same + trailing `\n` | **invalid** |

The URL field input (`form-field.component.html`, `url_field` template) never trimmed the value. Text fields already get sanitised through `valueChanges` (`sanitizeInput`), but URL fields got no equivalent.

## Fix

`sc-saas-frontend/src/app/modules/dynamic-forms/event-forms/form-field/form-field.component.ts`:
- In `ngOnInit`, for `DynamicFormFieldType.url_field`: trim the initial value once, which covers drafts saved earlier with a space. Then subscribe to `control.valueChanges` and patch in the trimmed value.
- New helper `trimUrlInput(value)` follows the same pattern as the existing `sanitizeInput` / `sanitizeScriptTagsInput`. It patches only when the value actually changed, so there is no loop.

The regex is unchanged, so every URL accepted before is still accepted. Spaces inside a URL and non-URL strings are still rejected.

## Blast radius

- Frontend only. `form-field.component.html` is the only `url_field` renderer, so the fix covers every dynamic form: program apply, event forms and custom forms.
- No API/DTO change, no flag, no query. `/audit-contract`, `/trace-flag` and `/check-isolation` don't apply. Tenant-agnostic.
- The submitted value is now trimmed, so the backend no longer receives URLs with surrounding whitespace.

## Verification

- `npx tsc -p tsconfig.app.json --noEmit` → clean.
- No automated test added (workspace guardian skill not yet available).
- Manual (verified by Vishali before push): paste `  https://adm.thub.sanchidev.in/table/application_programs  ` into Website. It should trim and show as valid. `https://exa mple.com` and `abc` should still show "Please enter a valid URL".
