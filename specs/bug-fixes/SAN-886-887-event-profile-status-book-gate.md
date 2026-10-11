---
id: SAN-886, SAN-887
title: Book button stays enabled when account's profile status doesn't qualify for an event
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-886, https://linear.app/sanchiconnect/issue/SAN-887
repos: [backend, frontend]
commit:
created: 2026-09-21
updated: 2026-09-21
---

# SAN-886 / SAN-887 — Book button not gated by event's profile-status restriction

## Problem
Investor dashboard "Book your slot" modal already showed the pink banner "This event is only open to accounts with a specific profile status" (a backend rejection message), but the Book button for open slots stayed clickable — a disqualified user could click Book and get a 403 instead of seeing a disabled button up front. A same-shape restriction (account type, `allowedUserTypesToBook`) had just been fixed the same day (commit `2f2f5e9f`); the profile-status axis (`allowedUsersProfileStatuses`) never got the equivalent treatment on either repo.

## Root cause (CODE_ERROR, two repos)
- **Backend**: `sc-saas-backend/src/modules/events/repositories/events.repository.ts` — the 4 explicit `.select()` column whitelists for event-list/calendar queries included `allowedUserTypesToBook` but not `allowedUsersProfileStatuses`. TypeORM silently drops unselected columns, so the frontend never received this field at all, even though the DB column and server-side enforcement (`events.service.ts` `attendEvent()`) already existed.
- **Frontend**: `event-details-one-on-one-modal.component.ts`/`.html` and `event-details-modal.component.ts`/`.html` only implemented the `isStakeholderTypeAllowed` (account-type) check — no equivalent `isProfileStatusAllowed` getter existed to gate the Book button / "Are you attending?" action.

## Fix
- Backend: added `allowedUsersProfileStatuses` to all 4 `.select()` lists in `events.repository.ts` (lines 87-88, 159-160, 217-218, 271-272).
- Frontend: added `get isProfileStatusAllowed()` to both modal components (reads `localStorage.getItem('profile-approval-status')`, set by `ProfileService` on every completeness update, against `event.allowedUsersProfileStatuses`). Folded into `event-details-one-on-one-modal`'s `getSlotView()` priority chain as a new `'not-eligible-status'` kind (disabled button + lock icon, mirrors the existing `'not-eligible'` pattern), and gated `event-details-modal`'s "Are you attending?" block on it, with a matching explanatory message in both.

## Verification
- Backend: `tsc --noEmit` and `eslint` clean (only pre-existing unrelated warnings).
- Frontend: `tsc --noEmit` clean on both touched `.ts` files.
- Not manually verified in the running app this session — no dev environment exercised with a real `allowedUsersProfileStatuses`-restricted event. Backend server-side enforcement (`attendEvent()`) already existed and is unaffected by this change, so this is a UX-completeness fix, not a security fix.
