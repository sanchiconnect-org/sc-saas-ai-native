---
id: SAN-1471
title: "Notifications Phase 2 — EX-04 Application status updates (in-app notifications when an application moves)"
type: feature
status: done                    # approved by Mahima 2026-10-06; implemented 2026-10-08; SAN-1726/1727/1728 + SAN-1471 Done; manual dev-tenant run still pending
linear: https://linear.app/sanchiconnect/issue/SAN-1471/notifications-p2-ex-04-application-status-updates   # parent issue (project "Enhancement"); sub-issues SAN-1726 (backend), SAN-1727 (frontend), SAN-1728 (admin)
owner: Mahima Sharma
source: "BRD — Notifications and an Action-Driven Dashboard for SanchiAPP, v1.1 (1 Oct 2026), EX-04 (W-02 'Shortlisted'), Phase 2"
repos: [backend, frontend, admin]   # dependency order
contracts:
  api:
    - "GET   api/v1/notifications/counters                                              (backend, EXISTING — gains the additive field `statusUpdates`; `bell` now includes it (D-4))"
    - "GET   api/v1/notifications                                                       (backend, EXISTING — 5 new `type` values; items of these types gain the additive field `cta: { label, url } | null` (D-3))"
    - "PATCH api/v1/notifications/mark-all-read                                         (backend, EXISTING — UNCHANGED: already clears NEW and leaves ACTION_REQUIRED alone)"
    - "POST  api/v1/application-programs-management/:programUUID/update-round/:adminMd5 (EXISTING — side effect added: in-app notification; request/response UNCHANGED)"
    - "POST  api/v1/application-programs-management/:programUUID/reject-round/:adminMd5 (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/programs-management/:programUUID/update-round/:adminMd5            (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/programs-management/:programUUID/reject-round/:adminMd5            (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/programs-management/:programUUID/tentative-round/:adminMd5         (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/vs-programs-management/:programUUID/update-round/:adminMd5         (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/vs-programs-management/:programUUID/reject-round/:adminMd5         (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/vs-programs-management/:programUUID/tentative-round/:adminMd5      (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/mentor-application-management/update-round/:adminMd5               (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/mentor-application-management/reject-round/:adminMd5               (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/mentor-application-management/tentative-round/:adminMd5            (EXISTING — side effect added; UNCHANGED)"
    - "PATCH api/v1/jobs/:jobUUID/application/:applicationUUID/actions                 (EXISTING — side effect added; UNCHANGED)"
    - "POST  api/v1/jobs/application/:applicationUUID/schedule-interview               (EXISTING — side effect added; UNCHANGED)"
    - "No NEW routes (D-2: admin writes its own rows; no admin→backend notification endpoint)"
  flags:
    - notification_centre_enabled   # EXISTING (SAN-1401). Reused, no sub-flag (D-11)
  events:
    - "notifications.type — FIVE new enum values: cfa_application_status, program_application_status, vs_program_application_status, mentor_application_status, job_application_status (D-12)"
    - "notifications rows written directly by sc-saas-admin (Medoo) for admin's direct-DB status writes — row shape in §Notification row contract (D-2)"
    - "socket 'fetch-count' (EXISTING, reused, payload-free) — the backend emits it to each recipient after its own writes; admin-written rows are picked up by the 30 s poll"
tenant_scoped: true
depends_on: [SAN-1381]           # Mahima 2026-10-06: needs SAN-1381 Phase 1 CODE merged (bell, counters, centre — present in all repos), not SAN-1381 status=done; proceed while Phase 1 Linear items close out
created: 2026-10-06
updated: 2026-10-06              # all OQs resolved by Mahima 2026-10-06; OQ-3 revised (CTA → ACTION_REQUIRED). Awaiting her explicit approval
---

# Notifications Phase 2 — EX-04 Application status updates

## Reference and evidence tags

- **BRD:** "Notifications and an Action-Driven Dashboard for SanchiAPP" v1.1, item EX-04 (wireframe W-02, the "Shortlisted" bell item), Phase 2.
  - The BRD document itself is not in the workspace.
  - The only source text is Linear issue SAN-1471 (a placeholder, no comments).
- **Extends:** `specs/features/SAN-1381-notifications-action-driven-dashboard.spec.md` (Phase 1, approved). SAN-1381 lists EX-04 under *Out of scope* (line 518).
- **Evidence tags** follow `specs/spec-authoring-practices.md`:
  - **[EV]** = evidenced, with a `file:line` reference.
  - **[INFERRED]** = a conclusion drawn from the code, not stated in it.
  - **[NOT SPECIFIED]** = the code does not say.
- **Owner decisions** are cited **(Mahima, 2026-10-06)**.

SAN-1471 text, verbatim:
> Startups hear when a challenge or program application is shortlisted, rejected or selected.
> Job applicants hear when their application moves.
> Grant milestones and disbursement steps follow the same pattern.

## Problem

Applicants get no in-app signal when their application changes status:
- **CFA, program, VS-program and mentor applicants** get email, and some get WhatsApp, but nothing in the app.
- **Job applicants** get nothing at all when they are shortlisted or rejected.

The Phase 1 bell (FR-U5) can list notifications, but nothing writes one when an application moves.

EX-04 adds that signal, in-app only, in two places:
- **The bell panel**, counted in the bell number. Items that need the applicant to do something get a call-to-action button and stay under "Needs action" until it is done.
- **The `/notifications` page.**

## Current state (checked against code, 2026-10-06)

### What Phase 1 already gives us (reuse, don't reinvent)

**`notifications` table** [EV `sc-saas-backend/src/modules/notifications/entities/notification.entity.ts`]
- Columns:
  - `from_user_id`, `to_user_id`, `startups`, `investors`
  - `title` (NOT NULL), `message`, `object_uuid`, `url`
  - `privacy` (enum `public|private`), `send_to` (enum `all|user`)
  - `type` (MySQL enum, NOT NULL, :47–52)
  - `has_read`
- Phase 1 columns (:60–77): `read_at`, `actioned_at`, `category` (enum `action_required|new|system`), `source_type` (varchar 50), `source_id` (int).
- `AbstractEntity` adds `id`, `uuid`, `status`, `created_at`, `modified_at`, `deleted_at` [EV `sc-saas-backend/src/core/entities/abstract.entity.ts:14–47`].
  - TypeORM generates `uuid` in the app (`@Generated('uuid')`), so any non-TypeORM writer must supply it.

**`NotificationType` enum** has 5 values [EV `sc-saas-backend/src/core/constants/enum.ts:347–353`].

**`NotificationCategory` enum** has `action_required | new | system` [EV `enum.ts:361–365`].

**Action-required handling (Phase 1)** [EV `repositories/notification-centre.repository.ts:17`]
- `IS_ACTION_REQUIRED_SQL` = `category = 'action_required'` OR (`category IS NULL AND type = 'connection_request'`).
- **Mark all as read** [EV :136–154]: sets `has_read = 1` and `read_at` on every personal row that is **not** action-required. Action-required rows are left untouched.
- **Single read** [EV :80–99]: sets `has_read = 1` and `read_at`.
- **Bell-panel fields** come from `centreFieldsFor()` [EV `notification-centre.service.ts:28–64`]:
  - `isActionRequired` = (`category = action_required`).
  - `isActioned` = `actioned_at IS NOT NULL`. Connection requests are the exception: they are resolved at read time against live source data, using `getPendingConnectionUUIDs` [EV `notification-centre.repository.ts:111`] passed in by `notifications.service.ts:104–113`.
  - **This is the precedent for working out "actioned" from source data at read time.**

**Write pattern:** each notification kind has its own `add…Notification()` builder [EV `repositories/notifications.repository.ts:72–213`].

**Counters** [EV `notification-counters.service.ts:43–68, 228–232`]
- `bell = connections + communityWall + jobs.total + (mode B ? opportunities.total : 0)`.
- Every term is derived from source data (SAN-1381 Decision #3).

**Socket:** `emitFetchCountToRoom(userId)` carries no payload. Precedent for using it: `JobService.refreshJobTeamCounters()` [EV `job.service.ts:778–790`].

**Flag gate**
- Backend: `NotificationCentreService.isEnabled()` [EV `notification-centre.service.ts:78–80`].
- Admin constant [EV `sc-saas-admin/config/config.php:306–307`].
- Admin helper `notifCentreEnabledForAdmin()` excludes partner sessions [EV `sc-saas-admin/includes/notification_centre_functions.php:40–49`].
- Admin schema guards: `notifCentreHasTable()` / `notifCentreHasColumn()` (:51, :64).

**Schema sync:** the backend runs with `synchronize: true` [EV `sc-saas-backend/src/core/database/database.module.ts:32`].

**Team resolution** [EV `user/repositories/user.repository.ts`]
- `getParentUserByProfileType()` (:796) finds the profile's parent user.
- `getAllMembersIds()` (:996–1055) returns everyone on that profile. Job seekers are a team of one.

### Frontend

- `NotificationTypes` has 5 values [EV `sc-saas-frontend/src/app/modules/notifications/notifications.enum.ts:1–7`].
- `NotificationCounters` interface [EV `src/app/core/state/notifications/notifications.model.ts:31–47`].
- **Bell** [EV `shared/common-components/notification-bell/notification-bell.component.ts`]:
  - The badge shows `max(0, counters.bell − bellBaseline)` (:75–77).
  - The localStorage baseline is set on "Mark all as read" and lowered whenever `bell` drops below it (:70, :167–181). [Per coordinator: the baseline logic is an uncommitted local change.]
  - The "Needs action" tab shows `isActionRequired && !isActioned` (:80–82).
  - The only inline buttons today are Accept/Decline on connection requests (:146–165).
- **`/notifications` page:** renders only the platform-message and connection templates [EV `modules/notifications/pages/notifications/notifications.component.html:29–46`].
- **Applicant landing routes:**

| Applicant type | Route | Evidence |
|---|---|---|
| CFA | `/call-for-applications/applied` | [EV `call-for-applications.module.ts:31`] |
| Program management | `/programs/applied` | [EV `programs.module.ts:44`] |
| Program details (with payment widget) | `/programs/details/:code/:slug` | [EV `programs.module.ts:89`; payment widget at `programs-details-page.component.html:134`] |
| Apply flow | `/programs/apply/:code/:slug` | [EV `programs.module.ts:103`] |
| VS programs | `/vs-programs/applied` | [EV `app-routing.module.ts:314`; `vs-programs.module.ts:37`] |
| Jobs | `/applied/jobs` | [EV `app-routing.module.ts:251`] |
| Mentor | none found | [NOT SPECIFIED] |

### Where application status changes today

**CFA** — type `cfa_application_status`
- **Status table:** `application_program_submission_rounds` (`current_round_id`, `application_status`, `rejection_message`) [EV `application-program-submission-rounds.entity.ts:33–61`].
- **Round requirements:** `application_program_rounds.is_payment_required`, `is_video_required`, `is_document_required`, `form_id` [EV `application-program-rounds.entity.ts:29–51, 137`].
- **Backend writers (admin calls these over cURL):**
  - `updateRound()` [EV `application-program.service.ts:691`], including the first-round create (:733–738).
  - `rejectRound()` [EV `application-program.service.ts:956`].
- **Admin direct-DB writers:**
  - Draft `moveToSubmitted` [EV `sc-saas-admin/modules/application_management/draft_applications.php:161–193`].
  - Re-submission request [EV `sc-saas-admin/modules/application-submission-detail.php:1205–1235`]:
    - sets `forms_submissions.submitted = 0` and `requested_for_re_submission = 1`;
    - deletes the round rows;
    - the payload carries `redirectUrl = $programUrl` (:1216).
- **Recipient:** `forms_submissions.user_id`. It is nullable [EV `form-submissions.entity.ts:30–31`].

**Program management** — type `program_application_status`
- **Status table:** `program_startup_rounds` [EV `program-startup-rounds.entity.ts:15–60`].
- **Round requirements:** `program_rounds.is_video_required`, `is_payment_required` [EV `program-rounds.entity.ts:28–43`].
- **Backend writers (admin calls these over cURL), in `program-management.service.ts`:**
  - `updateRound()` (:631)
  - `rejectRound()` (:911)
  - `tentativeRound()` (:1072)
- **Admin direct-DB writer:** draft `moveToSubmitted` [EV `sc-saas-admin/modules/startup-draft-application-management.php:173–194`].
- **Recipient:** the startup's parent user (:744–747).

**VS programs** — type `vs_program_application_status`
- **Status table:** `vs_program_individual_rounds` [EV `vs-program-individual-rounds.entity.ts:10`].
- **Round requirements:** `vs_program_rounds.is_video_required`, `is_payment_required` [EV `vs-program-rounds.entity.ts:24–37`].
- **Backend writers, in `vs-programs-management.service.ts`:**
  - `updateRound()` (:173)
  - `rejectRound()` (:310)
  - `tentativeRound()` (:420)
- **Recipient:** the individual's parent user (:222–225).

**Mentor** — type `mentor_application_status`
- **Status columns:** `mentors.application_current_round_id`, `mentors.application_status` [EV `mentor.service.ts:799–810, 927–929, 992–994`].
- **Round requirements:** none. `mentor_application_rounds` has no requirement flags [EV `mentors/entities/mentor-application-rounds.entity.ts:7–42`].
- **Backend writers, in `mentor.service.ts`:**
  - `updateApplicationRound()` (:778)
  - `rejectMentorApplicationRound()` (:901)
  - `tentativeMentorApplicationRound()` (:979)
- **Recipient:** the mentor's parent user (:817–821).

**Business challenge** — no type of its own
- `challenge_participants.participant_status` has **no writer anywhere**.
- Challenges notify only through their linked CFA (`challenges.cfa_id`) [EV `challenges.entity.ts:181`].

**Job** — type `job_application_status`
- **Status table:** `job_applications` (`application_status`, `scheduled_video_interview`, `meeting_interview_id`) [EV `job-application.entity.ts:48–62`].
- **Backend writers:**
  - `performApplicationAction()` [EV `job.service.ts:721`].
  - `scheduleJobInterview()` [EV `job.service.ts:962`]. The interview meeting has no accept/confirm state [EV `meetings/repositories/meetings.repository.ts:855–888`].
- **Admin direct-DB writers:** moderation approve and reject [EV `sc-saas-admin/modules/job-detail.php:118–158`].
- **Recipient:** `job_applications.user_id`. It is nullable [EV `job-application.entity.ts:93–94`].

**Grants:** there is no model for them.

**Payment-completed record (the source for "payment done")**
- `payment_orders`: `module_type`, `module_type_id`, `module_type_sub_id`, `user_id`, `order_status` [EV `payment-management/entities/payment-orders.entity.ts:25–56`].
- `PaymentRepository.verifyPayment(moduleType, moduleTypeId, userId, moduleTypeSubId)` returns success when an order with `order_status ∈ {success, paid}` exists [EV `payment-management/repositories/payment.repository.ts:2211–2251`].
- **CFA** calls it as `('application_programs', programId, submissionId, roundId)`. The `user_id` slot carries the **submission id** [EV frontend `application-program-management-dynamic-form.component.ts:1486`; `.html:576` `applicantId = submissionsId`].
- **Programs** calls it as `('programs', programId, startupId, roundId)`. The `user_id` slot carries the **startup id** [EV frontend `programs-details-page.component.ts:524`; `.html:134`].
- **VS programs:** no payment caller was found in the frontend [NOT SPECIFIED].

**Document-upload record (the source for "documents uploaded", CFA only)**
- `application_program_document_types` (`program_id`, `program_round_id`, `is_mandatory`, `is_active`) [EV `application-program_document_types.entity.ts:20–51`].
- `application_program_document_submissions` (`program_id`, `program_round_id`, `submission_id`, `approval_status`, `is_rejected`) [EV `application-program_document_submissions.entity.ts:22–62`].

**Re-submission record**
- `forms_submissions.submitted` is set back to true on a real submit [EV `form-management/form-management.service.ts:482, 570, 658`].
- No backend code ever clears `requested_for_re_submission` [EV grep: no writer].

**Video-pitch record**
- Programs: `startup_pitch_deck.video_pitch_submitted` is a single sticky flag per startup. It is never reset when a round requests a video [EV `startup/entities/startup-pitch-deck.entity.ts:92–98`; only writer `startup/pitch-deck/pitch-deck.service.ts:263`]. So it cannot show a video was submitted *for this round*.
- CFA and VS: no per-round video-submitted record was found.

**Excluded because they are not status transitions:**
- Admin CSV import [EV `submission-application-management.php:3417–3452`].
- Admin page-load backfill [EV `includes/startup_application_management_funcs.php:620–627`].
- Developer-only soft delete [EV `submission-application-management.php:371–377`].

## Decisions

### Owner decisions (Mahima, 2026-10-06)

**D-1 (was OQ-1) — Every status transition notifies.**
- CFA, program-management, VS-program and mentor notify on:
  - every round move, including the first-round entry;
  - selection, rejection, tentative;
  - draft → submitted (admin);
  - re-submission request (admin).
- Jobs notify on every status move:
  - shortlisted or rejected;
  - interview scheduled or un-scheduled;
  - moderation approved or rejected (admin).
- Challenges notify only through their linked CFA.
  - `participant_status` still has no writer.
  - No new challenge workflow is built.

**D-2 (was OQ-2) — Option (b): admin inserts the notification rows itself, with Medoo.**
- This applies to every admin direct-DB status write:
  - job moderation approve and reject;
  - CFA draft `moveToSubmitted`;
  - program draft `moveToSubmitted`;
  - CFA re-submission request.
- The rows must follow §Notification row contract.
- No new backend route is added.
- Admin rows get no socket push; the 30 s poll picks them up.
- **Admin deploys after the backend.**

**D-3 (was OQ-3, revised by Mahima on 2026-10-06; supersedes "everything NEW")**
- A notification that carries a call-to-action button is `category = 'action_required'`.
- Every other status notification is `category = 'new'`. That covers rejection, moved forward with nothing to do, shortlisted, moderation approved, and submitted.
- Each ACTION_REQUIRED transition has a defined button label, target link and "actioned" condition, all built from existing data. See §Action-required transitions.
- If a transition has no reliable "actioned" condition in the code, it stays NEW. It is listed under "Deferred to ACTION_REQUIRED later".
- Mark all as read leaves ACTION_REQUIRED rows untouched. This is the existing backend behaviour [EV `notification-centre.repository.ts:136–154`].

**D-4 (was OQ-4; confirmed twice, 2026-10-06) — Status updates count in the bell.**
- Add `statusUpdates` to `NotificationCounters`, in the backend service and the frontend model.
- Add `bell += statusUpdates`.
- **This is an explicit, approved exception to SAN-1381 Decision #3.**
- `statusUpdates` counts this user's rows (`to_user_id = me`, `send_to = 'user'`, `deleted_at IS NULL`) of the five D-12 types that are either:
  - (a) `category = 'new'` and `has_read = 0`; or
  - (b) `category = 'action_required'` and not yet actioned (A-12).
- These rows are always per-user, so `notification_reads` (the broadcast-read table) does not apply.

**D-5 (was OQ-5) — Default copy**
- Use the default copy table in §Notification copy. Product may edit the wording later; that does not block this spec.
- When a rejection carries a reason, include it in the message.

**D-6 (was OQ-6)** — In-app only. No new email or WhatsApp.

**D-7 (was OQ-7)** — Grants are skipped entirely.

**D-8 (was OQ-8)** — All program types are in scope: CFA, programs-management, VS-programs and mentor applications.

**D-9 (was OQ-9)** — Silent-transfer rounds still notify in-app. They keep suppressing email and WhatsApp only.

**D-10 (was OQ-10) — Recipients**
- Notify every user account on the applicant's profile team.
  - Backend: use `getAllMembersIds()`.
  - Admin: use `users` rows with the same profile id and `deleted_at IS NULL`.
- Skip applicants with a NULL user:
  - CFA guests (`forms_submissions.user_id IS NULL`);
  - partner-submitted jobs (`job_applications.user_id IS NULL`).
- Do no email matching. Matching by email is a possible future enhancement.

**D-11 (was OQ-11)** — Reuse `notification_centre_enabled`. No sub-flag. Write rows only while the flag is on.

**D-12 (was OQ-12) — One `NotificationType` per source**

| Source | `notifications.type` | Backend key | Frontend `NotificationTypes` key | Admin constant |
|---|---|---|---|---|
| CFA (challenges via `cfa_id`) | `cfa_application_status` | `CFA_APPLICATION_STATUS` | `CfaApplicationStatus` | `notif_type_cfa_application_status` |
| Program management | `program_application_status` | `PROGRAM_APPLICATION_STATUS` | `ProgramApplicationStatus` | `notif_type_program_application_status` |
| VS programs | `vs_program_application_status` | `VS_PROGRAM_APPLICATION_STATUS` | `VsProgramApplicationStatus` | — |
| Mentor applications | `mentor_application_status` | `MENTOR_APPLICATION_STATUS` | `MentorApplicationStatus` | — |
| Job applications | `job_application_status` | `JOB_APPLICATION_STATUS` | `JobApplicationStatus` | `notif_type_job_application_status` |

### Author decisions (A-1 to A-10 accepted by Mahima, 2026-10-06; A-11 to A-13 are new with the revised D-3 — reviewer may overturn)

**A-1 — One shared backend writer:** `NotificationsService.notifyApplicationStatus(...)`.
- It writes only while the flag is on.
- It removes duplicate recipients and skips NULLs.
- A failure is caught and logged; it never fails the caller.
- It sends `fetch-count` to each recipient.
- It sets `category` per D-3 and §Action-required transitions.

**A-2 — Source columns.** `source_type` is the status table name and `source_id` is that row's id. No new columns.

**A-3 — When hooks fire.** Only after the status update succeeds. One row per recipient, per application, per transition.

**A-4 — Deep links.** `url` points to the applicant landing route. Mentor rows have `url = NULL`.

**A-5 — Re-submission copy.** The admin re-submission request uses the "Changes requested" copy.

**A-6 — Extra admin call sites.** The draft `moveToSubmitted` actions (CFA and program) and the CFA re-submission request also write rows.

**A-7 — Known gap.** The generic admin `edit.php` engine is not hooked.

**A-8 — Team rule.** The D-10 team rule also covers mentor and VS-individual profiles.

**A-9 — Admin flag check.** The admin writer checks the tenant constant `notification_centre_enabled` directly, so partner-admin actions also notify.

**A-10 — CFA tentative is blocked.** It depends on the separate bug: the `tentative-round` route is missing from `application-program.controller.ts`, even though admin calls it at `submission-application-management.php:181`.

**A-11 — "Actioned" is resolved at read time from source data.**
- This follows the Phase 1 connection-request precedent (`getPendingConnectionUUIDs`).
- The first time a row is found actioned, `actioned_at` is also written (one idempotent `UPDATE … WHERE actioned_at IS NULL`).
- Round requirements are always checked against the application's **current** round:
  - If the application has since moved to a round with no unmet requirement, or has been rejected, the row counts as actioned. The action no longer applies.
  - No extra "round at notification time" column is needed.

**A-12 — ACTION_REQUIRED rows stay in the bell number until actioned, even if read.**
- Opening the item sets `has_read` but does not clear it from "Needs action" or from `statusUpdates`.
- This follows the Phase 1 rule for action-required items ("stays until you act", BRD §7).

**A-13 — `cta` field in the API.**
- `GET notifications` returns an additive `cta: { label, url } | null` on items of the five types.
- It is non-null only while `category = action_required` and the row is not yet actioned.
- The label and url come from the first unmet requirement, in this order: re-submission, payment, documents.

## Action-required transitions (D-3)

| Transition | Button label | Target link | Actioned when (existing data) |
|---|---|---|---|
| **CFA re-submission request** (admin-written) | Resubmit | The admin's `$programUrl`, the same `redirectUrl` already emailed [EV `application-submission-detail.php:1205–1216`] | `forms_submissions.submitted = 1` for `source_id`'s submission. Set on a real submit [EV `form-management.service.ts:482, 570, 658`] or by admin `moveToSubmitted` [EV `draft_applications.php:190`] |
| **CFA move into a round with `is_payment_required = 1`** | Complete payment | `/programs/apply/{programCode}/{slug}`, the same link the backend already builds for CFA payment reminders. The slug rule is at [EV `application-program.service.ts:830–859`] | A successful `payment_orders` row exists, checked with `verifyPayment('application_programs', program.id, submission.id, currentRound.id)` [EV `payment.repository.ts:2211–2251`; frontend caller `application-program-management-dynamic-form.component.ts:1486`]. Or A-11 applies |
| **CFA move into a round with `is_document_required = 1`** | Upload documents | `/programs/apply/{programCode}/{slug}` [INFERRED — the apply flow is where round documents are uploaded] | Every active, mandatory document type for (program, current round) has a non-deleted submission row for (program, round, submission) with `is_rejected = 0` [EV columns `application-program_document_types.entity.ts:20–51`, `application-program_document_submissions.entity.ts:22–62`; the combination is INFERRED]. Or A-11 applies |
| **Program-management move into a round with `is_payment_required = 1`** | Complete payment | `/programs/details/{programCode}/{slug}`, the page that hosts the payment widget [EV `programs.module.ts:89`; `programs-details-page.component.html:134`]. The slug rule is at [EV `program-management.service.ts:862–864`] | A successful order exists, checked with `verifyPayment('programs', program.id, startup.id, currentRound.id)` [EV `programs-details-page.component.ts:524`; `payment.repository.ts:2211–2251`]. Or A-11 applies |

**When one round needs both payment and documents (CFA):**
- The row is actioned only when both are done.
- The `cta` shows the first unmet requirement (A-13).

### Deferred to ACTION_REQUIRED later (these stay NEW in this phase)

These rounds have no reliable "actioned" condition in the code, so they stay NEW:

- **Program-management round with `is_video_required`.** `startup_pitch_deck.video_pitch_submitted` is sticky per startup and never reset per round. It cannot prove a video was submitted for this round.
- **CFA and VS rounds with `is_video_required`.** No per-round video-submitted record was found.
- **CFA round with its own `form_id`.** No per-round form-completion record was identified [NOT SPECIFIED].
- **VS round with `is_payment_required`.** No VS payment caller and no `module_type` was found in the frontend, so there is no reliable payment lookup.
- **Job interview scheduled.** The job-interview meeting has no accept or confirm state [EV `meetings.repository.ts:855–888`]. Join is time-based only.
- **Mentor rounds.** They have no requirement flags, so nothing is needed.

## Notification copy (D-5)

**Placeholders**
- `{program}` = the program title. Mentor rows have no program, so they use the literal "the mentor programme" [INFERRED].
- `{round}` = the target round name. For tentative, it is the current round.
- `{job title}` = the job title.
- `{reason}` = the trimmed rejection reason. Empty, or admin's `"NA"`, counts as no reason.

| Transition | Category | Title | Message |
|---|---|---|---|
| Moved to next round / first round, **no CTA** | new | Application moved forward | Your application for {program} moved to {round} |
| Moved to next round, **payment required** (CFA, program) | action_required | Application moved forward | Your application for {program} moved to {round}. Please complete the payment to continue |
| Moved to next round, **documents required** (CFA) | action_required | Application moved forward | Your application for {program} moved to {round}. Please upload the required documents |
| Rejected, with a reason | new | Application update | Your application for {program} was not selected. Reason: {reason} |
| Rejected, without a reason | new | Application update | Your application for {program} was not selected |
| Tentative | new | Application update | Your application for {program} is on the tentative list for {round} |
| Draft → submitted (admin) | new | Application submitted | Your application for {program} has been submitted |
| Re-submission requested (admin) | action_required | Changes requested | Please update and resubmit your application for {program} |
| Job shortlisted | new | You've been shortlisted | You've been shortlisted for {job title} |
| Job rejected, with a reason | new | Application update | Your application for {job title} was not selected. Reason: {reason} |
| Job rejected, without a reason | new | Application update | Your application for {job title} was not selected |
| Interview scheduled | new (deferred) | Interview scheduled | Your interview for {job title} has been scheduled |
| Interview un-scheduled | new | Interview update | Your interview for {job title} is no longer scheduled |
| Moderation approved (admin) | new | Application approved | Your application for {job title} has been approved and sent to the employer |

The two "moved forward" lines with a requirement add one sentence to Mahima's copy, in the same style [INFERRED]. Product may edit them.

## Notification row contract (backend and admin must write identical rows)

| Column | Value |
|---|---|
| `uuid` | New UUID v4. Backend: TypeORM. Admin: `gen_uuid()` [EV `sc-saas-admin/includes/core_functions.php:105`] |
| `status` | `1` |
| `from_user_id` | `NULL` |
| `to_user_id` | One recipient (D-10) |
| `startups`, `investors` | `NULL` |
| `title`, `message` | From §Notification copy |
| `object_uuid` | `uuid` of the status row |
| `url` | The applicant landing route (A-4), or the CTA target for ACTION_REQUIRED rows, or `NULL` |
| `privacy` | `private` |
| `send_to` | `user` |
| `type` | One of the five D-12 values |
| `has_read` | `0` |
| `read_at`, `actioned_at` | `NULL` |
| `category` | `new` or `action_required`, per §Notification copy |
| `source_type` | `application_program_submission_rounds`, `program_startup_rounds`, `vs_program_individual_rounds`, `mentors` or `job_applications`. **For the CFA re-submission request use `forms_submissions`**, because the round rows are deleted (:1235) and actioned is judged on `forms_submissions.submitted` |
| `source_id` | Id of that row |
| `created_at`, `modified_at` | DB default |
| `deleted_at` | `NULL` |

## Acceptance criteria

**Gate**
- [ ] With the flag off:
  - No hooked endpoint or admin action writes a row.
  - No socket event is emitted.
  - Email and WhatsApp are unchanged.
  - `counters` returns 403.
- [ ] With the flag on, a failed notification write never fails the status change. The error is logged.
- [ ] No new email or WhatsApp is sent (D-6).

**Backend sources**
- [ ] Each hooked transition writes one row per recipient, of the matching D-12 type. Row fields follow the row contract. Title, message and category follow §Notification copy. The hooked transitions are:
  - CFA, program, VS and mentor: update, reject and tentative;
  - job: actions and schedule-interview.
- [ ] Silent-transfer rounds still write the in-app row and still send no email.
- [ ] The rejection reason is included only when one exists.
- [ ] Every member of the profile team gets a row and a `fetch-count`. Example: a startup with 3 users gets 3 rows.
- [ ] Applicants with a NULL user get no row and cause no error.
- [ ] Challenges are notified only through their linked CFA.

**Action-required (D-3)**
- [ ] CFA move into a payment round:
  - writes `action_required` with `cta = { "Complete payment", /programs/apply/{code}/{slug} }`;
  - the item shows under "Needs action";
  - after a successful `payment_orders` row exists for (application_programs, program, submission, round), the next list/counters call reports it actioned. `actioned_at` is set, `cta` is null, and the item leaves "Needs action".
- [ ] Program-management move into a payment round: same as above, keyed on (programs, program, startup, round).
- [ ] CFA move into a document round:
  - writes `action_required` with the "Upload documents" CTA;
  - is actioned once every active mandatory document type for that round has a non-rejected upload.
- [ ] CFA re-submission request (admin):
  - writes `action_required` with the "Resubmit" CTA to `$programUrl`;
  - is actioned once `forms_submissions.submitted = 1`.
- [ ] If the application later moves to a round with no unmet requirement, or is rejected, the earlier action-required row counts as actioned (A-11).
- [ ] Rounds that only need a video or a round form, VS payment rounds, and interview scheduled all write `new` rows with no CTA (Deferred list).
- [ ] "Mark all as read" sets `has_read = 1` on NEW status rows only. ACTION_REQUIRED status rows keep `has_read` unchanged and stay in "Needs action".

**Counters and bell (D-4, A-12)**
- [ ] `GET notifications/counters` returns `statusUpdates` = (my unread NEW status rows) + (my ACTION_REQUIRED status rows not actioned).
- [ ] `bell` = the Phase 1 terms + `statusUpdates`. Example: 2 unread NEW + 1 open ACTION_REQUIRED + 3 pending connections gives `bell = 6`.
- [ ] Opening a NEW status item lowers `statusUpdates` by 1.
- [ ] Opening an ACTION_REQUIRED item does **not** lower it. Completing the action does.
- [ ] After "Mark all as read":
  - the server-side `statusUpdates` equals the number of still-open ACTION_REQUIRED rows;
  - the frontend `bellBaseline` (localStorage) is lowered when the server `bell` drops below it (`notification-bell.component.ts:70`), so a later arrival raises the shown count by 1.
- [ ] Rows belonging to other users, and deleted rows, never count.

**Admin sources (D-2)**
- [ ] Each of these inserts rows that match the row contract exactly, but only when the tenant flag constant is true and `notifCentreHasColumn($database, "notifications", "source_type")` holds:
  - job moderation approve and reject;
  - CFA draft `moveToSubmitted`;
  - program draft `moveToSubmitted`;
  - CFA re-submission request.
- [ ] The re-submission row is `action_required`, with `source_type = forms_submissions` and `url = $programUrl`. The others are `new`.
- [ ] An admin-written row matches a backend-written row column for column, apart from ids and timestamps.
- [ ] An admin insert failure is caught, and the admin action still returns its usual success JSON.
- [ ] Actions by partner admins also produce rows (A-9).

**Frontend**
- [ ] All five types render in the bell panel and on `/notifications` (dedicated template).
- [ ] ACTION_REQUIRED items with a non-null `cta` show a button with `cta.label` that navigates to `cta.url`. NEW items show no button.
- [ ] Clicking an item marks it read and navigates to its `url`. A NULL `url` only marks it read.
- [ ] Rows written by the backend appear without a refresh (socket). Admin rows appear within 30 s (poll).

**Isolation**
- [ ] Every new query and insert touches only this tenant's DB, including the `payment_orders` and document lookups (invariant #5). `/check-isolation` passes.

## Per-repo plan

### backend (`sc-saas-backend`) — SAN-1726

**Enum**
- Add the five D-12 values to `NotificationType` (`src/core/constants/enum.ts:347`).

**`modules/notifications/`**
- Writer and builder (A-1), recipient helper (D-10), copy helper (§Notification copy).
- Category selection in the writer: look at the target round's `is_payment_required` / `is_document_required` (CFA) or `is_payment_required` (program). Any other requirement is in the Deferred list and stays `new`.

**Actioned resolver** (A-11), in `repositories/notification-centre.repository.ts`
- Add `getActionedStatusNotificationIds(rows)`, modelled on `getPendingConnectionUUIDs`.
- Re-submission: checks `forms_submissions.submitted`.
- Payment: reuses `PaymentRepository.verifyPayment` or an equivalent batched query on `payment_orders` (`order_status IN ('success','paid')`).
- Documents: checks the mandatory, active document types against non-rejected uploads.
- Current round / rejected (A-11): checks the status row.
- Persists `actioned_at` the first time a row resolves.
- Wire it into:
  - `notifications.service.ts` (list): pass the actioned set into `centreFieldsFor()`. Add a parameter, as `pendingConnectionUUIDs` does.
  - `notification-centre.service.ts`: `centreFieldsFor()` reports `isActioned` from that set and adds `cta` (A-13).

**Counters (D-4)**
- `notification-counters.service.ts`: add `statusUpdates`, computed inside the existing `Promise.all`, and add it to `bell`.
- `repositories/notification-counters.repository.ts`:
  - `countUnreadNewStatusUpdates(userId)`;
  - `getOpenActionRequiredStatusRows(userId)`, filtered by the resolver.
- Index review on `notifications(to_user_id, type, category, has_read)`, against the NFR-01 budget.

**Hooks**
- `application-program.service.ts`: `updateRound()` (:691, both branches) and `rejectRound()` (:956).
- `program-management.service.ts`: `updateRound()` (:631), `rejectRound()` (:911), `tentativeRound()` (:1072).
- `vs-programs-management.service.ts`: `updateRound()` (:173), `rejectRound()` (:310), `tentativeRound()` (:420).
- `mentor.service.ts`: `updateApplicationRound()` (:778), `rejectMentorApplicationRound()` (:901), `tentativeMentorApplicationRound()` (:979).
- `job.service.ts`: `performApplicationAction()` (:721) and `scheduleJobInterview()` (:962).

**Jest tests**
- Per-source writes: flag off, failure isolation, silent transfer, reason, copy, category, team fan-out, NULL user, type/source fields.
- The resolver, for each ACTION_REQUIRED transition: payment success, all documents uploaded, resubmitted, moved on, rejected.
- `markAllNewRead` leaves ACTION_REQUIRED status rows alone.
- `statusUpdates` and `bell` arithmetic.
- An isolation spec extension.

### frontend (`sc-saas-frontend`) — SAN-1727

- Add the five values to `NotificationTypes` (`modules/notifications/notifications.enum.ts`), keys per D-12.
- Add `statusUpdates: number` to `NotificationCounters` (`core/state/notifications/notifications.model.ts`). The bell keeps using `counters.bell`.
- **Bell** (`shared/common-components/notification-bell/`):
  - an icon per type;
  - a CTA button for items with `cta` (navigate to `cta.url`), next to the existing Accept/Decline pattern;
  - NULL `url` → mark read only;
  - "Needs action" already filters on `isActionRequired && !isActioned`;
  - keep the `bellBaseline` logic, and commit the uncommitted baseline change together with this work or before it.
- **`/notifications`:** one shared template for the five types, including the CTA button.
- **Karma tests:** both render paths, the CTA, the bell count including `statusUpdates`, mark-all-read followed by a new arrival, and an ACTION_REQUIRED item staying in "Needs action" after being opened.

### admin (`sc-saas-admin`) — SAN-1728

**`includes/notification_centre_functions.php`**
- Constants `notif_type_cfa_application_status`, `notif_type_program_application_status`, `notif_type_job_application_status`. Each is guarded with `if (!defined(...))` and its value must equal the D-12 string.
- `notifCentreInsertApplicationStatus($database, $type, $recipientUserIds, $title, $message, $url, $sourceType, $sourceId, $objectUuid, $category)`:
  - checks the tenant flag constant (A-9);
  - guards with `notifCentreHasColumn`;
  - uses try/catch;
  - writes one insert per recipient, per the row contract.
- `notifCentreTeamUserIds($database, $profileColumn, $profileId)`.
- Copy helpers.

**Call sites** (each runs after the existing successful Medoo write)

| File | Action | Recipient / details | Category |
|---|---|---|---|
| `modules/job-detail.php` | `approveApplication` (:118–136) | `job_applications.user_id` | new |
| `modules/job-detail.php` | `rejectApplication` (:138–158) | `job_applications.user_id`; reason unless `"NA"` | new |
| `modules/application_management/draft_applications.php` | `moveToSubmitted` (:161–193) | team of `forms_submissions.user_id` | new |
| `modules/startup-draft-application-management.php` | `moveToSubmitted` (:173–194) | team of `startup_id` | new |
| `modules/application-submission-detail.php` | re-submission request (:1205–1235) | team of `forms_submissions.user_id`; `source_type = forms_submissions`; `source_id` = submission id; `url = $programUrl` | action_required |

**Conventions**
- `/* */` comments only.
- `count($arr) > 0`.
- Small, surgical edits.
- `php -l` on every touched file.

### tenants / tenants-admin / ai-startups-analyzer / 3rdparty-webservices
- No change.

## Cross-repo contract impact

| Contract | Change | Gate |
|---|---|---|
| Flag `notification_centre_enabled` (#1) | None; reused | `/trace-flag notification_centre_enabled` |
| Backend API (#2) | No new routes. 14 routes gain a side effect only. Additive changes: 5 `type` values and `cta` on `GET notifications`; `statusUpdates` on `GET notifications/counters`; `bell` now includes it | `/audit-contract` against frontend `core/service/notifications.service.ts`, `NotificationCounters`, and the admin cURL callers |
| SAN-1381 Decision #3 | Explicit, approved exception (D-4) | Recorded here |
| `notifications` row shape, now written by two repos | Backend and admin both write rows. The row contract is the single reference. Admin deploys after the backend | Rollout ordering; review |
| Read-only cross-module reads | The backend notifications module now reads `payment_orders`, `application_program_document_*` and `forms_submissions` (same tenant DB) to resolve "actioned". No writes | `/check-isolation` |
| Tenant scoping (#5) | Backend: own deployment's DB only. Admin: per-tenant `$database` only | `/check-isolation` |
| Auth (#4) | Unchanged | — |
| Socket gateway | Only payload-free `fetch-count` | — |
| Tenant verification (#3), PowerPitch (#6) | Not touched | — |

## Test plan

There is no "guardian" skill in this workspace. Say so in the PR wherever coverage cannot be added.

**backend**
- Jest tests above.
- `npm run build`, `npm run lint`.
- Manual run on a dev tenant:
  - every transition, every source;
  - a CFA payment round: pay → item actioned;
  - a CFA document round: upload → actioned;
  - a program payment round: pay → actioned;
  - mark-all-read: ACTION_REQUIRED rows stay;
  - `statusUpdates` / `bell` arithmetic;
  - `EXPLAIN` on the counter queries.

**frontend**
- Karma tests above.
- `npm run build`.
- Manual: CTA buttons, "Needs action", the bell number, mark-all-read.

**admin**
- `php -l` on every touched file.
- Manual: all five call sites with the flag on and off. Check the re-submission row is `action_required` and clears after the applicant resubmits.
- Compare an admin row with a backend row, column by column.

**cross-repo**
- Flag off: no rows and no counter change.
- Tenant A only: tenant B is unaffected.

## Rollout

1. **backend:** enum values, writer, hooks, resolver and `statusUpdates`. All behind the flag.
2. **frontend:** types, CTA rendering, template and model field. Older builds ignore `cta` and `statusUpdates`; their bell number already includes it through `bell`.
3. **admin:** deploy **after the backend**. The column check and try/catch make an early deploy harmless.
4. Verify on the internal tenant, then follow the per-tenant flag rollout.

## Out of scope

- **Grants:** entirely out (D-7).
- **New email or WhatsApp:** none (D-6).
- **ACTION_REQUIRED for the deferred transitions:** rounds that need a video pitch or a round form, VS payment rounds, and interview scheduled. Each first needs a reliable "actioned" record.
- **Notifying NULL-user applicants by matching email:** possible future enhancement (D-10).
- **A challenge-participant workflow** (D-1).
- **Known uncovered path:** the generic admin `edit.php` engine (A-7).
- **Per-document accept/reject** (`application-submission-detail.php:1318–1381`).
- **Fixing the missing CFA `tentative-round` route** (A-10).
- **Preferences, quiet hours and consent** (EX-19, EX-20, EX-21).
- **Socket-gateway authentication.**

## Open questions

None. All were resolved by Mahima on 2026-10-06; see Decisions. The spec stays `status: draft` until Mahima approves it herself.

## Implementation notes (2026-10-08)

Built on branch `ai_native_setup_mahima` in all three repos; not committed.

- **Writer location (A-1).** It is `ApplicationStatusNotificationsService.notifyApplicationStatus()` in `sc-saas-backend/src/modules/notifications/application-status-notifications.service.ts`, inside its own `ApplicationStatusNotificationsModule`. It is not on `NotificationsService`: NotificationsModule already imports ProgramsManagementModule, so the program modules cannot import it back. The behaviour is the same as A-1.
- **Resolver name.** The resolver is `NotificationCentreRepository.getOpenStatusActions(rows)`, not `getActionedStatusNotificationIds`. It returns open row id → the requirement still due, which also drives the `cta` label (A-13). A row whose source is gone or unknown counts as actioned.
- **In-app preferences (SAN-1478).** The four program types map to `applicationUpdates` and the job type maps to `jobApplications`, in `NOTIFICATION_TYPE_IN_APP_CATEGORY`. `statusUpdates` leaves muted types out, including ACTION_REQUIRED ones.
- **Interview un-scheduled.** It notifies only when an interview was actually scheduled before.
- **Admin re-notify guard.** Admin updates notify only when Medoo reports success and at least one row changed. So a repeated approve or move does not notify twice.
- **Frontend type.** `NotificationCounters.statusUpdates` is optional (`statusUpdates?: number`), so an older backend that omits it still type-checks.
- **Index review.** Both counter queries lead with `to_user_id`, which has an FK index. No new index was added.

## Linear tracking

- **Parent:** SAN-1471 (project "Enhancement", assignee Mahima Sharma).
- **Sub-issues:** all Todo, priority Low, assignee Mahima Sharma, project Enhancement, parent SAN-1471, labelled `Feature` plus the repo badge.

| Repo | Issue | Notes |
|---|---|---|
| backend | SAN-1726 | — |
| frontend | SAN-1727 | blocked by SAN-1726 |
| admin | SAN-1728 | blocked by SAN-1726; deploys after backend |
