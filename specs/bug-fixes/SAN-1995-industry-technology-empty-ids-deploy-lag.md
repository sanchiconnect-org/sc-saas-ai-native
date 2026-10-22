---
id: SAN-1995
title: "Industry/Technology domain ids should not be empty (SC-SAAS-FRONTEND-D4, CN) — auto-save guard SAN-705 not in the release"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1995
sentry: [SC-SAAS-FRONTEND-D4, SC-SAAS-FRONTEND-CN]
repos: [frontend]
related: [SAN-1037, SAN-705, SAN-508, SAN-498]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1995: empty industry/technology ids

## Investigation
* **The events:** D4 and CN are one event each, same user, firstwings `/startups/edit/industry-technology`, 2026-10-19 08:45, release `90bde7be0` (merge of 2026-09-14). They are the `console.warn` in `StartUpService.saveIndustriedAndTechs()` (`core/service/startup.service.ts:136`) echoing the backend 400.
* **Every path that saves from this page** (`modules/startups/pages/edit/industry-technology/industry-technology.component.ts`):
  * **"Next Step":** `handleNext()` → `handleSave(false)`. It is gated by `app-form-next-step-button [disableNavigation]="saveButtonDisabled"`, and `saveButtonDisabled = loader || !isFormDataValid`. `isFormDataValid` needs at least one industry, at least one technology, valid forms, and a primary industry when `primary_industry` is on. The button only emits `next` when `!disableNavigation` (`form-next-step-button.component.ts:93`). This is the SAN-1037 client-side required check, and it is present.
  * **Auto-save** (`autoSaveService.register({ save: () => this.handleSave(true) })`, SAN-508). This was the path that bypassed the check: it fired on `isDirty` alone. SAN-705 (`608d37732`, 2026-09-14 12:27) added `if (silent && !this.isFormDataValid) return;` (current line ~259).
  * There are no other `handleSave` callers, no `ngSubmit`, and no submit-type button on this page.
* **Ancestry:**
  * `git merge-base --is-ancestor 608d37732 90bde7be0` → **no**. The release was cut the same day, just before the fix.
  * `608d37732` on `origin/main` → yes.
* **Conclusion:** the two events are the auto-save tick on a build without SAN-705. The user got no toast (silent), and their next valid edit saved normally.

## Fix
None needed.

## Blast radius / existing-flow impact
None (no change).

## Verification
Ancestry checks above. Code read of every save trigger: `grep -n "handleSave\|handleNext\|ngSubmit\|type=\"submit\""` on the component's ts and html shows only the two paths listed.

## Recommended close
Close as deploy lag. Firstwings needs a build containing `608d37732`.
