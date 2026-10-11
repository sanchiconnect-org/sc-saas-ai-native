---
id: SAN-1484
title: "Notifications Phase 3 — EX-14 Program health alerts"
type: feature
status: done                    # approved 2026-10-08 (OQs resolved by Mahima); implemented 2026-10-08; dev-tenant run pending
linear: https://linear.app/sanchiconnect/issue/SAN-1484/notifications-p3-ex-14-program-health-alerts
owner: Mahima Sharma
source: "BRD v1.1, EX-14 (W-08 annotation 3), Phase 3"
repos: [backend, admin]
contracts:
  api: ["None (cron + email only)"]
  flags: [notification_centre_enabled, cron_enabled]
  events:
    - "cron_jobs — new CronJobName PROGRAM_HEALTH_ALERTS (09:00 IST, seeded INACTIVE)"
    - "spa_email_templates — new `program-health-alert`"
    - "columns: application_programs.application_target, challenges.application_target (nullable int), + *.health_alert_sent_for (claim)"
    - "spa_settings — program_health_default_target, program_health_days_before_close"
tenant_scoped: true
depends_on: [SAN-1381, SAN-1475]
created: 2026-10-08
---

# EX-14 Program health alerts

## Reference
- **BRD (from Linear):**
  > Applications against target for each live challenge or program. If traction is low five days before closing, admins are alerted while there is still time to push outreach.

## Current state (checked 2026-10-08)
- **No application target exists.** `application_programs` and `challenges` have no target column; `challenges.business_goal` is free text.
- **Recipients:** `application_programs.program_managers` is a JSON list of admin ids [EV entity :48], the natural recipients. Challenges have no managers; internal ones link to their CFA program via `cfa_id`.
- **Applications are countable:**
  - programs: `forms_submissions` by `form_id`
  - challenges: `challenge_participants` per challenge
- **Live definitions** already exist in the SAN-1381 counters:
  - programs: status, test mode, not closed, close date
  - challenges: active, approved, `dead_line`

## Proposed design
- **P-1 Target [DDP OQ-1]:** a new nullable `application_target` (int) on both tables, set by the admin on the program or challenge edit form. When it's empty, the tenant default `spa_settings.program_health_default_target` (10) applies.
- **P-2 "Low traction" [DDP OQ-2]:** fewer applications than the target, **5 days** before the close date (`program_health_days_before_close`). An item is checked once it is within 5 days of closing.
- **P-3 Alert [DDP OQ-3]:**
  - A backend cron `PROGRAM_HEALTH_ALERTS` runs at 09:00 IST, seeded inactive, gated on `notification_centre_enabled`.
  - Each item at risk gets **one** email (claim column `health_alert_sent_for` = the close date, so a moved deadline re-arms it). It is sent to the program's `program_managers`, or to all super admins when there are none or for an external challenge.
  - Content: title, applications vs target, days left, and a link to the item in admin.
- **P-4 Command centre:** a "Programs at risk" list. Live items within the window, below target, with applications / target and days left.

## Acceptance criteria
- [ ] A live program closing in 5 days with 3 applications against a target of 10 → one email to its program managers. Rerunning the next day → no second email.
- [ ] Target met → no alert. Not yet within 5 days → no alert. Closed or test-mode → no alert.
- [ ] Deadline moved later → it re-arms, and alerts again when it's within 5 days of the new date.
- [ ] No program managers → super admins.
- [ ] The command centre lists at-risk items. Flag off → nothing.

## Open questions

None. All three were resolved by Mahima on 2026-10-08, by accepting the recommended defaults: a per-item `application_target` with tenant default 10; below target within 5 days of closing; an email once per close date to the program managers (else super admins), plus a command-centre list.

## Implementation notes (2026-10-08)

Backend and admin, uncommitted on `ai_native_setup_mahima`.

- **Backend:**
  - Entities: `application_programs` and `challenges` gain `application_target` (int, nullable) and `health_alert_sent_for` (date, nullable), via `synchronize`.
  - `CronJobName.PROGRAM_HEALTH_ALERTS = 'programHealthAlerts'`, 09:00 IST, seeded **inactive**.
  - `repository/program-health.repository.ts`: `getSettings` / `getDue` / `claim`.
  - `program-health-alerts.service.ts`: flag gate, claim, recipients via `EscalationRulesRepository.getRecipients` (managers, else super admins), one email per recipient.
  - New `program-health-alert` template, seeded on install. `sendEscalationDigestEmail` accepts the new code.
- **Admin:**
  - Settings `program_health_default_target` (10) and `program_health_days_before_close` (5), seeded by `notifCentreSettingDefaults`.
  - `notifCentreProgramsAtRisk()` and a "Programs at risk" table on the command centre. Program managers see only their own programs; challenges are shown to super/dev only.
  - An "Application target" field on the program create/edit and challenge create/edit forms. It saves only once the column exists.
- **Verification:**
  - `tsc` is clean.
  - Jest: 9/9 new unit tests (gate, claim, managers vs super admins, grouping, isolation, template, seed, registration). The cron and template suites pass 298/298.
  - The real-MySQL integration suite `program-health.integration.spec.ts` passes 5/5: settings and junk values, the window, met / far / past / closed / test-mode / off, per-item target, challenge with CFA managers, claim once, and re-arm on a moved deadline.
  - The admin real-MySQL harness for `notifCentreProgramsAtRisk` passes 5/5: order, counts, link, manager scope, window setting.
  - `php -l` is clean.
  - The 3 failing backend suites (`application-programs.repository`, `programs.repository`, `global-onboarding-design`) were already failing and aren't touched by this change.
  - Not run: a dev-tenant send (Gap Register G-016).
