---
id: SAN-944
title: EventFormsComponent.ngOnInit crashes reading 'valueChanges' off undefined dynamicFormGroup
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-944
sentry:
  - SC-SAAS-FRONTEND-EK
repos: [frontend]
commit: sc-saas-frontend@13882d0c (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-944 — event-forms.component.ts unguarded valueChanges read

## Root cause
`event-forms.component.ts:129`'s `ngOnInit()` read `this.dynamicFormGroup.valueChanges` when
registering with `autoSaveService`. `dynamicFormGroup` can still be undefined at this point — the
sibling `isDirty: () => !!this.dynamicFormGroup?.dirty` two lines above already guards against exactly
this (1 user, 4 events).

## Fix
Changed to `this.dynamicFormGroup?.valueChanges`, matching the sibling guard.

## Blast radius
None — `changes$` simply becomes undefined until the form group is set, same as the already-guarded
`isDirty` check right above it.

## Verification
Re-read the file after editing to confirm the guard matches the sibling `?.dirty` check. No automated
test added — step 6 (tests-first) is blocked workspace-wide (no `guardian` skill); substituted a
direct code read.
