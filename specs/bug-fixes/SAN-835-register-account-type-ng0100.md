---
id: SAN-835
title: "NG0100 on register Continue button — account-type emits @Output synchronously from ngOnInit"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-835
sentry:
  - SC-SAAS-FRONTEND-5J
repos: [frontend]
commit: sc-saas-frontend@fde5f034 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-835 — register account-type NG0100

## Root cause
`NG0100: ExpressionChangedAfterItHasBeenCheckedError` — "Previous value for 'disabled': 'false'. Current value: 'true'." on the register flow's Continue button (`register.component.html:154`, `[disabled]="disableContinueButton || loader"`). 88 occurrences / 8 users, still reproducing at investigation time.

`sign-up-forms/account-type/account-type.component.ts:123` called `this.emitIsAccountTypeFormValid.emit(this.isAccountTypeFormValid)` synchronously from the child's own `ngOnInit`. The parent's handler (`checkAccountFormValid()`) synchronously mutates `disableContinueButton`, which is bound on the Continue button already checked earlier in the same change-detection pass — the classic Angular NG0100 same-tick parent/child mutation pattern.

A different Sentry group, SC-SAAS-FRONTEND-AX, was initially suspected to be the same bug but investigation found it's a different component (`MentorIntroComponent`, mentor-information edit page) captured from a local dev build with no sourcemap — not enough evidence to action, no ticket opened for it (see Related).

## Fix
Deferred the initial emit by one macrotask in `account-type.component.ts`'s `ngOnInit`:
```ts
setTimeout(() => this.emitIsAccountTypeFormValid.emit(this.isAccountTypeFormValid));
```
Breaks the same-tick coupling without changing the emitted value or downstream logic. `register.component.ts` itself untouched — the button binding is a symptom, not the cause.

No API/DTO/flag/tenant-scoping impact — one line, defers an existing emit by a tick.

## Blast radius
`sc-saas-frontend`'s register flow (`/auth/register`), account-type step specifically.

## Verification
`npx tsc --noEmit` and full `ng build --configuration development` (AOT) both clean, no new errors. No automated test suite exists for this repo yet — manual repro (open register flow, select an account type, confirm no console NG0100 error and Continue button still enables/disables correctly) is the substitute verification, still to be done by hand before commit.

## Related
SC-SAAS-FRONTEND-AX (NG0100 in `MentorIntroComponent`) is a separate, unconfirmed defect — needs a fresh sourcemapped Sentry capture before it's actionable. Not tracked as a Linear issue yet; flag if it recurs in production with a mapped release.
