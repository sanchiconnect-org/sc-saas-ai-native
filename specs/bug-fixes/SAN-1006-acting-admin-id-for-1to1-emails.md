---
id: SAN-1006
title: 1:1 admin-action emails go to the Developer (role 1) account instead of the admin who clicked
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1006
repos: [backend, admin]
created: 2026-09-25
updated: 2026-09-25
---

# SAN-1006 — the admin who does the action receives the admin copy

## Request

QA (logged in as Super Admin, "Send Communication Emails? = Yes") received no admin copy after doing 1:1
event actions. Decision (user): **the admin who does the action on the event receives it.**

## Root cause

Every sc-saas-admin → backend admin call authenticates with `generatePartnerRandomStringForBackdoor()`
(`sc-saas-admin/includes/partners_functions.php:491`). It always writes the one-time token onto the first
`spa_admin_users` row with **`role = 1` (Developer**, seeded as `dev@sanchiconnect.com`), whoever is logged
in. The backend's `checkIsValidAdmin()` resolves the admin from that token, so SAN-998's "acting admin" CC,
and the pre-existing approve email (`meeting-created-cc-admin`), always went to the Developer account.
Super Admin is role 2 (`installDefaultAdminRoles`), so a Super Admin never received them.

## Fix

- **sc-saas-admin:** the 9 1:1 event call sites append
  `actingAdminId=(int) $_SESSION["admin_user_id"]` (`0` when there's no admin session, e.g. a partner
  login):
  - `details.php`: approve, reject, event-live, cancel event, remove attendee (`cancel_attendee_meeting`)
  - `add_attendee.php`: manual-add approve
  - `reschedule_booking.php`: reschedule
  - `edit/speakers.php`: speaker email
  - `edit/publish.php`: event-live
- **sc-saas-backend:** the existing `checkIsValidAdmin(adminMd5)` in `events.service.ts` and
  `admin-actions.service.ts` gets an optional `actingAdminId`. **The token is still validated first**
  (auth model unchanged). Only then, if `actingAdminId` matches a real admin user, is that admin returned;
  otherwise the token admin is returned, as before. The 5 events routes (`approve_request`,
  `reschedule_request`, `reject_request`, `cancel_event`, `cancel_attendee_meeting`) and the 2
  admin-actions routes (`speaker-event-registration`, `event-live`) take an optional `?actingAdminId`
  query param. Reschedule passes it through to its internal approve.
- Effect: the admin who clicked gets the CC on speaker-chosen / event-live / reject / reversal /
  reschedule / cancel-event emails and the approve `meeting-created-cc-admin` email. Their id is also
  recorded in `approvedBy` / `rejectedBy` / `reversedBy`.

## Contract impact

The query param is additive and optional. The only consumer is sc-saas-admin. An older admin build that
doesn't send it keeps the old behaviour (Developer account), and nothing errors. Every other
`checkIsValidAdmin()` caller passes no id and is unchanged.

## Verified

- `npx tsc --noEmit` clean; existing ses-email + admin-actions suites pass (5 suites, 40 tests).
- `php -l` clean on all 5 admin files.
- Not exercised against a live tenant.

## Rollout

Deploy the backend first, then admin. Admin first is also safe: the backend ignores an unknown query param
until it's updated.

## Open questions

None.
