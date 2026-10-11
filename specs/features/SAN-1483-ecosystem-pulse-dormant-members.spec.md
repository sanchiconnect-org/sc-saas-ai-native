---
id: SAN-1483
title: "Notifications Phase 3 — EX-13 Ecosystem pulse and dormant members"
type: feature
status: done                    # approved 2026-10-08 (OQs resolved by Mahima); implemented 2026-10-08; browser check pending
linear: https://linear.app/sanchiconnect/issue/SAN-1483/notifications-p3-ex-13-ecosystem-pulse-and-dormant-members
owner: Mahima Sharma
source: "BRD v1.1, EX-13 (W-08 annotation 4), Phase 3"
repos: [admin]
contracts:
  api: ["None (the broadcast send path is unchanged: POST v1/admin-actions/broadcast-ceo-message)"]
  flags: [notification_centre_enabled]
  events: []
tenant_scoped: true
depends_on: [SAN-1381, SAN-1474]
created: 2026-10-08
---

# EX-13 Ecosystem pulse and dormant members

## Reference
- **BRD (from Linear):**
  > Registrations this week against last week, by persona, plus a list of members with no login in 30 days and a one-click re-engagement broadcast.

## Current state (checked 2026-10-08)
- **Persona tables and flags:** `notifCentrePersonas()` [EV `includes/notification_centre_functions.php`] maps every persona table to its tenant flag and its `profiles_access` key. The command centre already applies admin permissions per persona.
- **Login data:** `users.last_logged_in` is overwritten on each login; `users.previous_logged_in` holds the one before.
- **Broadcast composer:** `broadcast_messages/create` [EV `modules/broadcast_messages/create.php`] builds each persona's recipient SQL through `formatQuery()` (statuses, industries, technologies, geography). It sends via the backend `broadcast-ceo-message`, and to chat and the community wall. It's gated by `can_broadcast_messages`. **There is no "inactive since" filter.**

## Proposed design
- **P-1 Where [DDP OQ-1]:** a new "Ecosystem pulse" section on the **command centre**, below the queue cards. It's visible to admins who can see the ecosystem queue: `can_accept_reject_profiles` or super/dev, each persona narrowed by `profiles_access` and the tenant's persona flag, the same as the ecosystem counter.
- **P-2 Pulse:** one row per permitted persona showing:
  - registrations in the last 7 days, the 7 days before, and the change (▲/▼ with text)
  - total members
  - dormant members

  "Registrations" = rows in the persona table created in the window (soft-deletes excluded).
- **P-3 Dormant [DDP OQ-2]:** a user whose account belongs to that persona and has **no login in the last 30 days**. That is `last_logged_in` older than 30 days, or never logged in with the account created more than 30 days ago. The section shows the count per persona, and the 10 longest-dormant members (name, persona, last login).
- **P-4 One-click re-engagement [DDP OQ-3]:** a "Send re-engagement broadcast" button, shown only with `can_broadcast_messages`. It opens the **existing composer prefilled**: `broadcast_messages/create?dormant_days=30`. That gives a pre-selected "No login in the last 30 days" filter, a suggested subject and message, and every persona selected. The admin reviews and presses Send. The composer gains a `dormant_days` filter, applied in `formatQuery()` as `(users.last_logged_in < NOW() − N days OR (users.last_logged_in IS NULL AND users.created_at < NOW() − N days))`. It applies to the recipient count, the send, and the test send.

## Acceptance criteria
- [ ] With 5 startups registered this week and 2 last week, the Startups row shows 5, 2 and "▲ +3".
- [ ] A persona the admin can't access, or whose flag is off, isn't listed.
- [ ] A user last logged in 40 days ago is dormant. One who logged in 10 days ago isn't. One who never logged in and registered 40 days ago is; one who never logged in and registered 5 days ago isn't.
- [ ] The re-engagement button opens the composer with the dormant filter pre-selected. The dry-run count equals the dormant total for the selected personas. Nothing is sent without the admin pressing Send.
- [ ] Without `can_broadcast_messages`, no button is shown.
- [ ] Flag off → the command centre is unreachable (unchanged). The composer works as today when no `dormant_days` filter is set.

## Open questions

None. All three were resolved by Mahima on 2026-10-08, by accepting the recommended defaults: a command centre section; no login in 30 days; a prefilled composer.

## Implementation notes (2026-10-08)

Admin only, uncommitted on `ai_native_setup_mahima`.

- **`notifCentreEcosystemPulse()`** in `includes/notification_centre_functions.php`. It uses the permission rules of the ecosystem counter and returns, per persona:
  - registrations this week and last week
  - members
  - dormant members

  It also returns the 10 longest-dormant members across personas, ordered by `COALESCE(last_logged_in, created_at)`.
- **Command centre:** an "Ecosystem pulse" table below the cards. The change is shown with ▲/▼ plus text. Below it, a "Longest dormant members" list, plus a **Send re-engagement broadcast** button for admins with `can_broadcast_messages`. The button opens `broadcast_messages/create?dormant_days=30`.
- **Broadcast composer:**
  - The new filter is read from `dormant_days` (count), `data[dormant_days]` (send) or `?dormant_days` (prefill), clamped to 0–365.
  - `formatQuery()` appends the dormant condition to every persona query, so the count, the send and the per-persona queries all agree.
  - The prefill only happens with the notification centre on. It adds a hidden field, an info banner, and a suggested subject and message. The admin still reviews and sends.
  - Without the filter, the composer is unchanged.
- **Verification:**
  - `php -l` is clean on 5 files.
  - A real-MySQL harness ran the real pulse function and the composer's real `formatQuery()` (extracted verbatim). 7/7 checks pass:
    - this week 3 / last week 1 / members 5
    - dormant 3: 40-day login, 35-day login, and never logged in at 40 days; not 10 days, not a 5-day-old account
    - ordering
    - composer recipients with the filter, and everyone without it
  - Not run: a browser check and a real send.
