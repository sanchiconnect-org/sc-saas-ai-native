---
id: SAN-1482
title: "Notifications Phase 3 — EX-09 Weekly profile views by persona"
type: feature
status: done                    # approved 2026-10-08 (OQs resolved by Mahima); implemented 2026-10-08; browser check pending
linear: https://linear.app/sanchiconnect/issue/SAN-1482/notifications-p3-ex-09-weekly-profile-views-by-persona
owner: Mahima Sharma
source: "BRD v1.1, EX-09, Phase 3 (not wireframed)"
repos: [backend, frontend]
contracts:
  api:
    - "GET api/v1/notifications/counters (EXISTING) — ADDITIVE field `profileViewsWeekly` per OQ-1/OQ-3"
    - "PATCH api/v1/users/profile/notification-settings (EXISTING) — ADDITIVE optional `privacy: {privateProfileBrowsing}`"
    - "GET api/v1/users/profile-views/:type/:id (EXISTING) — shape unchanged; private browsers left out"
  flags: [notification_centre_enabled]
  events: []
tenant_scoped: true
depends_on: [SAN-1381, SAN-1469]
created: 2026-10-08
---

# EX-09 Weekly profile views by persona

## Reference
- **BRD (from Linear):**
  > A weekly count of profile views by persona, subject to a privacy setting. Useful for startups gauging investor and corporate interest.

## Current state (checked 2026-10-08)
- **Recording views:** `profile_views` (`user_id` = the viewer, `profile_type`, `profile_id`, `created_at`) [EV `user/entities/profile-views.entity.ts`]. Rows are written by `POST users/profile-views/increment`, which **has no auth guard**, so `userId` is client-supplied [EV `user.controller.ts:516`; backend `user/module.spec.md` security note].
- **Existing reads:**
  - `totalProfileViews` = all-time distinct viewers (`getProfileViewsCount2`), shown as a badge in the user menu [EV `notifications.service.ts:240`, `user-profile-menu.component.html:33`].
  - `GET users/profile-views/:type/:id` = the last 30 days of viewers, **by name**, opened as the "who viewed your profile" modal (`ProfileViewersComponent`) [EV `user.repository.ts` `getProfileViewers`].
- **The viewer's persona** is `users.account_type`.
- **There is no privacy setting** anywhere for profile views.

## Proposed design (recommended defaults; every [DDP] needs a decision)
- **P-1 Where [DDP OQ-1]:** a "Profile views this week" card in **dashboard-v2**, under the "Why complete your profile" card. It shows one row per viewer persona (e.g. Investors 4, Corporates 2, Mentors 1), the total, and "▲ +N vs last week". A link opens the existing viewers modal. Flag-gated; hidden when there were no views in either week.
- **P-2 Privacy [DDP OQ-2]:** a per-user **"Browse profiles privately"** toggle, off by default.
  - When it's on, that user's views still count in the anonymous persona totals, but they're left out of the named viewers list.
  - The weekly card only ever shows counts, never names.
  - *As built:* stored as `notification_settings.privacy.privateProfileBrowsing` and saved through the existing `PATCH profile/notification-settings` (merged, additive). The toggle is in a new "Privacy" section on the notification-settings page. There is no new column and no new endpoint.
- **P-3 Counting [DDP OQ-3]:**
  - Distinct viewers per persona over the rolling last 7 days, compared with the 7 days before.
  - Views by the profile's own team (owner and team members) and anonymous rows (`user_id` NULL) are excluded.
  - Returned as an additive `profileViewsWeekly: {thisWeek: {[persona]: n}, lastWeek: {[persona]: n}}` on `GET notifications/counters`.
- **P-4 Who sees it [DDP OQ-4]:** every persona sees its own profile's views. Copy is tuned for startups ("investor and corporate interest"); other personas get the same card.

## Acceptance criteria
- [ ] Two investors and one corporate view a startup this week, and one investor last week → the card shows Investors 2, Corporates 1, total 3, "▲ +2 vs last week".
- [ ] The same investor viewing three times counts once.
- [ ] Views by the startup's own team members don't count.
- [ ] A viewer with private browsing on is counted in the totals but isn't in the named viewers list.
- [ ] No views in either week → no card. Flag off → no card, and no new field is read.

## Open questions

None. All four were resolved by Mahima on 2026-10-08, by accepting the recommended defaults: a dashboard-v2 card; viewer-side private browsing; distinct viewers over 7 days vs the prior 7; all personas.

## Known gap (not in scope)
- `POST users/profile-views/increment` is unauthenticated with a client-supplied `userId`, so view counts can be inflated. This predates EX-09; registered as Gap Register G-017, together with the missing `profile_views` index.

## Implementation notes (2026-10-08)

Backend and frontend, uncommitted on `ai_native_setup_mahima`.

- **Backend:**
  - `NotificationCountersRepository.getProfileViewsWeekly()`: distinct viewers per viewer `account_type`, last 7 days vs the 7 before. It excludes the profile's own team, anonymous rows and deleted viewers.
  - `profileViewsWeekly` is additive on `GET notifications/counters` (null with no profile).
  - `PrivacySettingsDto` and `PrivacySettingsType` are added.
  - `getProfileViewers` filters with `PUBLIC_VIEWER_SQL`.
- **Frontend:**
  - `profile-views-weekly.util.ts` (`buildProfileViewsSummary`).
  - The `DashboardProfileViewsComponent` card in dashboard-v2, under "Why complete your profile". It is flag-gated, hidden when empty, and "See who viewed" opens the existing viewers modal.
  - A "Privacy" section with the "Browse profiles privately" toggle on the notification-settings page. It is flag-gated, and its payload is sent only with the flag on.
- **Verification:**
  - Backend: `tsc` is clean.
  - Jest: the notifications and user suites pass 217 (18 opt-in MySQL tests skipped), including 2 new counter tests.
  - Real-MySQL: `profile-views-weekly.integration.spec.ts` passes 3/3 (persona split, distinct, own-team and anonymous excluded, last week, a private browser counted but not named). The badge-equals-list suite still passes 14/14.
  - Frontend: Karma 27/27 (new util spec 4, card spec 4, settings spec +3, next-actions unchanged). The AOT build passes. The "full page reload" warning in the settings spec was already there.
  - Not run: a browser check on a dev tenant.
