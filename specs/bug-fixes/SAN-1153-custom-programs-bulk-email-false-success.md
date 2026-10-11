# SAN-1153 — Custom Programs bulk email shows false success when backend rejects the send

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1153
- **Repo:** sc-saas-admin · **Priority:** High · **Assignee:** Nirmal Singh · **Related:** SAN-910, SAN-911
- **Classification:** CODE_ERROR

## Problem
Several bulk-email handlers call `sendBroadcastEmail()` and ignore its response. If sc-saas-backend
rejects the send (403 permission check, 400 DTO validation, missing template), the admin still sees
"Message sent successfully!". A `broadcast_messages` row with a recipient count is left behind, and
zero `ses_email_queue` rows are created, so nothing is sent and the Broadcast details page shows 0.

## Evidence (real incident)
SINE tenant (adm.sineedge.sineiitb.org), Sep 21 2026, 11:36–12:18 IST: about 180 application-status emails
(IITB IOE / SIDBI Seed Fund / DST-NIDHI SSS, source "Custom Programs") were listed as sent with
recipients, but every details page showed 0.
- `ses_email_queue` on the tenant DB: no rows matching those subjects on Sep 21–22. The only row queued
  that whole day was 1 `invitation` email.
- **Correction:** the backend checks permissions against the account that owns the backdoor token.
  That is always the role-1 Developer account (`checkIsValidAdmin()`, no acting-admin id passed), not
  the admin who clicked Send, so the sender's own permissions don't matter. The Developer account has
  `can_broadcast_messages` (the Sep 9 and Sep 28 sends worked), so a 403 is less likely than first
  thought. The exact rejection reason on Sep 21 is still unknown. Candidates: a 400 from backend
  validation (`name` is `@IsNotEmpty` per recipient, so one blank applicant name rejects the whole
  batch), a 404 from a backdoor-token race, or the backend being unreachable. The backend logs for
  06:06–06:48 UTC would settle it. Whatever the reason, zero rows were queued.
- CloudWatch `AWS/SES Send` for 06:00–07:00 UTC only showed a steady 50-per-5-minute queue drain
  that started before the first send. That is shared-account background traffic, not these emails.

Conclusion: the emails were never sent. They have to be resent; there are no stats to recover.

## Root cause
SAN-910 (ec5ae05d) fixed the response check only in
`application_management/submission-application-management.php` (list view). The sibling handlers
never checked the response.

## Second defect found during verification
Every existing check (SAN-910's list view, `broadcast_messages/create.php`, `approvals.php` ×2,
`partners/broadcast/create.php`) tested `statusCode`. sc-saas-backend's `GlobalExceptionFilter` and
`TransformInterceptor` both return **`status_code`** (snake_case), so those checks never fired on a real
rejection. SAN-910's fix was therefore ineffective in production.

## Fix
- `includes/core_functions.php`: new `checkBroadcastEmailResponse($sendEmails)` helper: failure if
  the response is empty, not JSON, or has `status_code` (fallback `statusCode`) `>= 400`. It flattens NestJS
  array-valued `message`.
- All 5 existing checks now read `status_code` (keeping `statusCode` as a fallback), and array-valued
  `message` is flattened so validation errors don't print as "Array". Only the error message shown
  changes; no status or row handling changed in create/approvals/partners.
- On failure, each handler below now deletes the phantom `broadcast_messages` row and returns
  `error: true` with `Broadcast failed: <backend message>`. The check runs before a canned response is saved.
  - `modules/application_management/submission-application-management-tableview.php` (`bulkEmailRoundApplications`)
  - `modules/application_management/draft_applications.php` (`bulkEmailToDraftApplications`)
  - `modules/form_builder/submissions.php` (`bulkEmails`)
- Each page's front-end JS already shows `data.errorMessage` when `data.error` is true, so no template change was needed.

## Not fixed here (same unchecked pattern, reported for follow-up)
The following handlers insert a live `broadcast_messages` row and ignore the response:
`startup-application-management.php`, `startup-application-management-tableview.php`,
`startup-draft-application-management.php` (`programs`), `mentor_application_management.php`,
`venture-studio-application-management.php`, `growth_metrics/list.php`, `events/edit/publish.php`,
`events/details.php`. The `*-detail.php` pages also ignore the response, but their `broadcast_messages`
insert is commented out, so they show a false toast without leaving a phantom row. They can adopt
`checkBroadcastEmailResponse()` directly.

## Verification
- `php -l` clean on all 8 touched files.
- Helper run against realistic bodies: 201 success → ok; 403, 404, 400 (array message), raw
  `statusCode` 500, nginx HTML 502, empty body and cURL `false` → all fail with a readable message.
- No automated test: sc-saas-admin has no test framework.
- Not exercised against a live backend yet. Manual check on a non-prod tenant: temporarily set
  `can_message_profiles = 0` on the role-1 Developer account (the account that owns the backdoor token),
  then send a bulk email from the Custom Programs table view. It should show an error toast, and no new
  row should appear under Broadcast Messages. Restore the flag afterwards, send again, and confirm the
  success path still queues rows.

## Commit
sc-saas-admin `5528ce48` (pushed to `ai_native_setup` 2026-09-30)
