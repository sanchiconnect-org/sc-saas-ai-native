---
id: SAN-619
title: "ng-select 'reading keys' on /startups/dashboard (SC-SAAS-FRONTEND-C1) — cascade of SC-SAAS-FRONTEND-30, already fixed"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-619
sentry: [SC-SAAS-FRONTEND-C1, SC-SAAS-FRONTEND-30]
repos: [frontend]
duplicates: [SAN-698]
commit: none. Fixed earlier by sc-saas-frontend@4d22a03c (2026-08-24), which is in main and prod release 90bde7be
created: 2026-10-13
updated: 2026-10-13
---

# SAN-619: C1 is a side effect of SC-SAAS-FRONTEND-30

## Investigation
* The C1 stack is entirely inside `@ng-select/ng-select@8.3.0`. `ItemsList.filter()` reads `this._groups.keys()`, and `_groups` is only assigned in `setItems()`.
* `setItems()` runs from `ngOnChanges` when `[items]` is bound, or from `ngAfterViewInit` when `ng-option` children are used. No code in the frontend sets `NgSelectComponent.items` directly, so `_groups` can only be undefined if the first update pass of the ng-select's host view was **aborted** after its DOM was created.
* A Sentry search by the C1 user's IP (2026-09-01) shows about 45 events of **SC-SAAS-FRONTEND-30** on the same page between 11:12 and 11:20 UTC, from the same user and release `51eb6706`. The four C1 events at 11:20:11–12 fall inside that run.
* SC-SAAS-FRONTEND-30 (1046 events, 118 users) threw at `dashboard-v2.component.html` in the search-input `[placeholder]` binding (`userType.type` while `userType` was undefined). That binding comes **before** the Account-type `<ng-select [items]="userTypesArr">` in the same view. Each change-detection pass threw before Angular set `[items]`, so the select's `ngOnChanges`/`setItems()` never ran. When the user typed into the visible but uninitialised dropdown, C1 fired.

## Fix status
* `4d22a03c` (2026-08-24) defaulted `userType = { type: 'all', label: 'All' }` and made the placeholder null-safe (`userType?.type`, `userType?.label`). That removes the change-detection abort, which removes C1 too.
* `4d22a03c` is an ancestor of `origin/main`, `origin/ai_native_setup` and prod release `90bde7be`. The crash release `51eb6706` did not include it.
* Neither Sentry group has recorded an event since 2026-09-01. Both groups are now `resolved` in Sentry.

## Why no code change
Patching ng-select (guarding `_groups`, or reworking every `[items]` binding) would target a symptom that no longer occurs and could change dropdown behaviour across the 67 templates that use ng-select. Contract checks do not apply: the change is template-only, with no flag, API/DTO or tenant-scoped query involved.

## Side note (not a C1 cause)
`fetchData()` calls `this.userTypesArr.unshift(...)` on the array it has just reassigned. That is safe, because a new reference is bound before ng-select sees it. No change is needed.
