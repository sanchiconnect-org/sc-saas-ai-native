---
id: FA-009                      # next free FA- id. Linear: SAN-1156 (backend), SAN-1157 (admin). Project P-SAN-65.
title: Platform Email Stats for All Emails
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/project/platform-email-stats-for-all-emails-fd92c2078655
owner: nirmal.s@sanchiconnect.com
repos: [backend, admin]         # dependency order: sc-saas-backend, then sc-saas-admin
contracts:
  api:
    - "NONE on the sc-saas-backend REST contract (no controller or DTO change)."
    - "Internal only: SESEmailService.sendEmail(reqBody, options?) gains an optional second parameter. The body POSTed to sc-saas-3rdparty-webservices /ses/send-email is unchanged."
    - "DB contract (shared per-tenant DB): ses_email_queue gains nullable template_code varchar(100). Written by sc-saas-backend, read by sc-saas-admin."
  flags:
    - "custom_smtp (existing, read only. Decides whether SES stats can exist for a tenant. Not changed.)"
  events: []
tenant_scoped: true
depends_on: [SAN-1155, SAN-1154]   # both Done 2026-09-30
created: 2026-09-30
---

# Platform Email Stats for All Emails

Evidence tags used below (per `specs/spec-authoring-practices.md`):
**[verified: file:line]** means read in code on 2026-09-30. **[INFERRED]** is a reasoned
extrapolation that needs validation. **[NOT SPECIFIED IN SOURCE]** is a real gap.
**[USER DECISION 2026-09-30]** means the user has already decided it.

## Problem

Client request: show delivery, open and bounce stats for application accepted/rejected emails,
OTP emails and every other non-broadcast platform email, the way `broadcast_messages/details`
already does for broadcasts (SAN-1154, SAN-1155).

Today this is impossible for most email types because no record of the send exists:

- Every platform email is sent through one method, `SESEmailService.sendEmail()`
  **[verified: sc-saas-backend/src/core/services/ses-email.service.ts:239-309]**. It POSTs to
  sc-saas-3rdparty-webservices `/ses/send-email` (:288-293), which sends through SES SMTP, or
  through the tenant's own SMTP when `saasFeatures[Feature.CUSTOM_SMTP]` and all four
  `EMAIL_SMTP_*` settings are set (:272-285).
- `ses-email.service.ts` has **116** `this.sendEmail(` call sites and **51**
  `addToSesEmailQueueAsSent(` call sites (plus its definition at :316-343)
  **[verified: grep count 2026-09-30]**. The user's function-level audit counts 48 functions that
  log and 68 that log nothing, including `sendOtpEmail` (:351), `sendEmailVerificationEmail`
  (:422), `sendAdminPasswordResetEmail` (:5382), meetings, connections, events, facility
  management, tickets, proforma invoice and `sendChatMessageEmail` (:4428).
- The SAN-1155 stats cron only looks at `broadcast` / `partner_broadcast` rows
  **[verified: sc-saas-backend/src/modules/cron/sync-broadcast-email-stats.service.ts:87-93]**.
- sc-saas-admin has no stats page for non-broadcast email. `modules/common.php:183` only defines
  a generic column list for `ses_email_queue` **[verified]**.

## Decisions already made

1. **[USER DECISION 2026-09-30]** Log and track **all** email types **except** chat-notification
   emails (`sendChatMessageEmail`, `EmailTemplateCode.CHAT_MESSAGE`
   **[verified: ses-email.service.ts:4434]**). Chat emails are never logged and have no stats.
2. **[USER DECISION 2026-09-30]** Logging is centralised inside `sendEmail()`. All per-function
   `addToSesEmailQueueAsSent()` calls are removed or replaced so nothing is logged twice. The
   queue-sender cron path skips logging because its row already exists.
3. **[USER DECISION 2026-09-30]** Add a nullable `template_code` column to `ses_email_queue`
   holding the `EmailTemplateCode` value, so admins can filter by fine-grained type.
4. **[USER DECISION 2026-09-30]** No email body is stored for sensitive templates: OTP, password
   reset and email verification. Their rows keep recipient, subject, template_code, status,
   response/message id and stats only.
   **[USER DECISION 2026-09-30, resolves former open question 1]** `admin-account-created` and
   `jury-account-created` are sensitive too (their body carries the new account's plaintext
   password): no stored body, and `data.password` is masked in the stored subject.
5. **[USER DECISION 2026-09-30]** Stats are collected by polling: the SAN-1155 cron is extended
   to every logged type. SES event publishing (configuration set to SNS to a per-tenant backend
   webhook) is a possible later phase and is out of scope here.
6. **[USER DECISION 2026-09-30]** New sc-saas-admin "Email Logs" page. Filters: email type or
   template, date range, recipient, status. Counters: Sent / Delivered / Opened / Bounced /
   Failed. Per-row stats and Request Stats like the broadcast details page. CSV export. Reuse
   SAN-1154's status logic.
7. **[USER DECISION 2026-09-30]** TypeORM `synchronize` applies the schema change on deploy.
   Production MySQL is 8.4.11, where adding a nullable column is an INSTANT metadata change. The
   generated DDL **must be verified to be a single `ADD COLUMN`**.

## Code findings that shape the design (evidence-tagged)

### F1. Existing ses_email_queue writers: sendEmail() is not the only place rows are created

Besides `addToSesEmailQueueAsSent()`, `ses-email.service.ts` creates rows in three other ways.
Removing the helper alone is not enough to prevent double-logging:

| Kind | Function (lines) | What it writes | Treatment in this spec |
|---|---|---|---|
| Inline post-send row with functional columns | `sendInstantEmailInvitationEmail` (send :2818, row :2820-2843) | `INVITATION` row with `invitation_code`, `program_code`, `invite_code_valid_till`, `invitation_user_type`, `email_data`. **Used for registration and reminders.** | Keep its own row and add `templateCode`. Pass `skipLog: true` to `sendEmail()`. |
| Inline post-send row | `sendStartupKitEmail` (send :3461, row :3463-3475) | `STARTUP_KIT_APPLICATION` row incl. `email_data` (has cc) | Keep its own row and add `templateCode`. Pass `skipLog: true`. |
| Inline post-send row, conditional | `sendGrowthMetricReviewerAllotmentEmail` (send :5299, row :5301-5323 only if `invitationCode`) | `GROWTH_METRICS_INVITATION` row with invitation columns | With an invitation code: keep own row, add `templateCode`, pass `skipLog: true`. Without one: central logging. |
| Enqueue only (sent later by the queue cron) | `sendBroadcastMessageCEOEmail` non-instant (:1590-1614), `sendBulkPendingConnectionReminderEmail` (:2622-2641), `sendProfileCompletenessEmail` (:2695-2706), `createInvitationEmailsInEmailQueue` (:2985-3005), `sendProgramManagementPendingApplicationEmail` (:3859-3880), `sendApplicationPendingApplicationEmail` (:6428-6441), `sendPremiumModuleRequestEmail` non-instant (:7918-7931) | `pending` rows | Set `templateCode` on the queued entity. No `sendEmail()` call happens here. |
| Instant send with **no** row today | `sendBroadcastMessageCEOEmail` with `send_instant` (:1587-1588) | nothing | Central logging with `emailType = data.emailType \|\| BROADCAST` and `broadcastMessageId`, so these rows appear on the broadcast details pages and in the SAN-1155 broadcast budget. |

**[verified: all line refs above, ses-email.service.ts, 2026-09-30]**

### F2. Both cron callers of sendEmail() update an existing row

- `EmailQueueService.sendEmailQueueEmail()` updates the pending row to sent/failed
  **[verified: sc-saas-backend/src/modules/cron/ses-email-email-queue.service.ts:72-96]**.
- `InvitationReminderService` resends an invitation and updates that row's `response`,
  `total_email_sent` and `last_sent_at`
  **[verified: sc-saas-backend/src/modules/cron/invitation-reminder.service.ts:97-115]**.

Both must pass `skipLog: true`. These are the only `sendEmail()` callers outside
`ses-email.service.ts` **[verified: grep `\.sendEmail\(` across src/, 2026-09-30]**.

### F3. The OTP subject contains the OTP

The default seeded subject for `verify-email-address` is
`Verify your {{ brand_name }} account. OTP: {{ otp }}`
**[verified: sc-saas-admin/config/admin-data/email_templates.php:3]**. `sendOtpEmail` renders the
subject with the same attributes as the body, including `otp`
**[verified: ses-email.service.ts:389-401]**. Storing the rendered subject would store the OTP,
which defeats decision 4. **Requirement:** for sensitive templates the stored subject must have
the secret value masked. This follows directly from decision 4 and is not a new choice.

### F4. The account-created email embeds a plaintext password

`sendAdminAccountCreatedEmail` (templates `admin-account-created` / `jury-account-created`) puts
`data.password` into the rendered body when not SSO **[verified: ses-email.service.ts:1099-1101]**.
Today it logs no row (:1116). Once logging is central, its body would be stored unless it is
redacted too. **Resolved:** both codes are sensitive (decision 4).

Separate existing issue, not in scope: `console.log('attributesToMap', attributesToMap)` at
**[verified: ses-email.service.ts:1103]** prints that password to stdout on every admin/jury
account creation. It should be filed as its own bug.

### F5. Schema facts

- `ses_email_queue` **[verified: sc-saas-backend/src/core/entities/ses-email-queue.entity.ts]**:
  `to` varchar(120) (:11), `email_subject` varchar(255) (:28), `email_data` json (:89),
  `html_content` text (:92), `email_sent_status` enum pending/sent/failed (:95-101),
  `response` json (:103), `broadcast_message_id` (:109), `email_type` **MySQL enum** default
  `normal` (:112-118), `last_sent_at` (:120), send/bounce/delivery/open timestamps (:130-149),
  `bounce_message` (:151), `ses_region` (:154). `modified_at` is an UpdateDateColumn from
  `AbstractEntity`.
- The table has **no secondary indexes** (only the PK from `abstract.entity.ts`)
  **[verified]**.
- `spa_email_templates.template_code` is `varchar(100)` nullable
  **[verified: sc-saas-backend/src/modules/global/admin/spa_email_templates.entity.ts:20-26]**.
  The new column uses the same type.
- `EmailQueueEmailType` **[verified: sc-saas-backend/src/core/constants/enum.ts:923-948]**.
  **No new enum values are added.** Adding one would change the `email_type` column definition,
  which is not a single `ADD COLUMN`. Newly logged types use the default `normal` and are told
  apart by `template_code`.

### F6. Who reads ses_email_queue by email_type (non-regression surface)

- Admin dashboard "Invitations" counters filter `email_type = invitation`
  **[verified: sc-saas-admin/config/default-settings/dashboard_counters.php:1287-1350]**. They
  are unaffected because invitation rows are still written only by their own code paths (F1).
- Broadcast details pages filter by `broadcast_message_id` and `email_type`
  **[verified: sc-saas-admin/modules/broadcast_messages/details.php:305-308,
  modules/partners/broadcast/details.php:298]**. The only change is that instant-broadcast rows
  now appear (F1). Today they are missing.
- `InvitationReminderService` selects invitation rows **[verified]** and is unaffected.

### F7. Stats cron (SAN-1155) specifics

**[verified: sync-broadcast-email-stats.service.ts]**

- Settings: MIN_AGE 15 min, MAX_AGE 30 days, RECHECK 20 h, UNTOUCHED_SLACK 60 s,
  BATCH_SIZE 300, delay 200 ms between calls (:48-57).
- Candidate query at :76-110 (a full scan today, because there is no index).
- It merges events from **all** `Insights[]` entries (:197-201). For an email with CC
  recipients, an open by a CC recipient would be counted for the `to` row. The SES v2
  `EmailInsights` item carries a `Destination` **[INFERRED — requires validation against the
  3.600.0 SDK types]**.
- Bounce side effect: sets `users.promotional_emails_enabled = false` for `row.to` (:246-251),
  the same as admin `getEmailStats` (details.php:226-228).
- Scheduling: the cron uses job name `syncBroadcastEmailStats`, seeded active at `20 * * * *`
  **[verified: sc-saas-backend/src/modules/cron/repository/cron-job.repository.ts:174-179,198-202;
  cron.service.ts:675-691]**.

### F8. Admin permission surface

- `$canbroadCastMessage` is true when `spa_admin_users.can_broadcast_messages = 1` for
  `$_SESSION['admin_user_id']` **[verified: sc-saas-admin/modules/common.php:528-533;
  includes/core_functions.php:1979-1986]**. The broadcast details page (the reference UI) is
  gated by it and also redirects jury sessions **[verified: modules/broadcast_messages/details.php:29-37]**.
- `$canExportData` is `spa_admin_users.can_export_data = 1` **or** any partner session
  **[verified: modules/common.php:542-546]**.
- Partner-portal logins set `partner_id` / `partner_user_id` but not `admin_user_id`
  **[verified: modules/partners/auth/login.php:61-69]**. `$canbroadCastMessage` is therefore
  false for partner sessions, but the new page will reject them explicitly anyway, because it
  shows tenant-wide email and must not reach partners.
- Quick Links shows broadcast entries under `$quickLinksCanBroadcast`
  **[verified: themes/default/html/elements/header.php:242-263;
  header_without_sidebar.php:215]**.

## Acceptance criteria

### Backend (sc-saas-backend, SAN-1156)

- [ ] **Schema:** `ses_email_queue.template_code` exists as `varchar(100) NULL` and has no
      index. On staging, the DDL TypeORM synchronize generates for this deploy is exactly one
      `ALTER TABLE ses_email_queue ADD template_code varchar(100) NULL` (captured from TypeORM
      query logging or a before/after `SHOW CREATE TABLE` diff). No other table or column
      changes are in the same deploy.
- [ ] **One row per send:** every successful `sendEmail()` call, except where `skipLog` is set,
      inserts exactly one row with `email_sent_status = sent`, `is_sent = 1`,
      `total_email_sent = 1`, `response` = the third-party response, `template_code`,
      `email_type` (caller-supplied, else `normal`), `broadcast_message_id` when supplied,
      `last_sent_at` = send completion time, and `from` / `to` / `reply_to` / subject.
- [ ] **No double-logging:** after the change, `addToSesEmailQueueAsSent` has 0 references.
      Each of the 51 former call sites passes its previous `EmailQueueEmailType` through the
      options, so `email_type` values for those emails are unchanged.
- [ ] **Skip paths:** the queue-sender cron, the invitation reminder cron and the three inline
      writers from F1 create **no** extra rows. For a queued broadcast to N recipients the row
      count is exactly N before and after the queue cron runs.
- [ ] **Failures:** when the third-party call throws, one row is inserted with
      `email_sent_status = failed`, `is_sent = 0`, `total_email_sent = 0`,
      `response = { error: <message>, httpStatus: <status or null> }` and `template_code`, and
      `sendEmail()` still throws the same `InternalServerErrorException` as today. The
      no-recipient `BadRequestException` path (:242-248) logs nothing.
- [ ] **Logging never breaks sending:** if the log insert throws (e.g. `to` > 120 chars), the
      error is caught and logged with `logger.warn`, and `sendEmail()` returns or throws exactly
      what it would have without logging. Subject is truncated to 255 chars before insert (see
      SAN-99's cause at ses-email-queue.entity.ts:20-27).
- [ ] **Chat excluded:** `sendChatMessageEmail` passes `skipLog: true`, so no row is created
      for `chat-message`.
- [ ] **Sensitive templates:** for `verify-email-address`, `verify-email-address-via-link` and
      `admin-password-reset`, `admin-account-created` and `jury-account-created`, the row has `html_content = NULL` and `email_data = NULL`, and the
      stored subject contains none of the secret values (OTP, verify URL, reset URL, account password), which are
      replaced with `******`. `sendEmail()` enforces "no body" for these template codes even if
      a caller forgets the redact option. The list of codes is one constant.
- [ ] **template_code everywhere:** every `sendEmail()` call site in `ses-email.service.ts`
      passes `templateCode`, and every enqueue-only and inline writer (F1) sets it on its row.
      A unit test or lint-style check fails if a call site in `ses-email.service.ts` calls
      `this.sendEmail(` without an options argument.
- [ ] **Instant broadcast:** `sendBroadcastMessageCEOEmail` with `send_instant` now logs rows
      with `email_type = data.emailType || broadcast` and `broadcast_message_id`.
- [ ] **Posted body unchanged:** the object POSTed to `/ses/send-email` has exactly the same keys
      as before. The options are not merged into `reqBody`.
- [ ] **Stats cron, broadcast non-regression:** broadcast/partner_broadcast selection, the
      300-row budget, recheck rules and ordering are unchanged.
- [ ] **Stats cron, other types:** a second budget (default 900 rows per run, class constant)
      selects `sent` rows whose `email_type` is not broadcast/partner_broadcast and whose
      `response` holds an SES `250 Ok <id>` message id. Same 15 min to 30 day window,
      not opened, not bounced, 20 h recheck. Rows that already have `delivery_timestamp` and
      are older than 7 days are no longer rechecked. The run summary logs candidates and
      updates per budget.
- [ ] **Recipient-scoped insights:** when an `Insights[]` item carries a `Destination`, only
      events for the row's `to` are used. When none carries one, behaviour is as today. This
      applies to both budgets.
- [ ] **Bounce side effect unchanged in kind:** a bounce on any logged type sets
      `users.promotional_emails_enabled = false` for that address, the same rule as today for
      broadcasts and as admin `getEmailStats` **[INFERRED — keeps the existing rule; flag at
      review if transactional bounces should not do this]**.
- [ ] `npm run build` and `npm run lint` pass. New unit tests for the logging and redaction
      behaviour pass under `npm test`.

### Admin (sc-saas-admin, SAN-1157)

- [ ] **Route and auth:** `email_logs/list` (module `modules/email_logs/list.php`, template
      `themes/default/html/email_logs/list.php`) calls `checkLoggedIn()` and includes
      `modules/common.php`. It redirects to `_admin_url` unless `$canbroadCastMessage`, and
      also redirects when `$_SESSION['partner_id']` is set or the session role is jury. The same
      checks apply to every POST/AJAX action on the page.
- [ ] **Tenant scope:** every query uses `$database` (this tenant's DB) only. No
      `$mainDatabase` and no cross-tenant lookup.
- [ ] **Filters:** email type (`email_type` values present), template (`template_code`, with
      labels from `spa_email_templates.template_title` and the raw code shown when no template
      row matches), date range on `created_at` (default last 30 days; input in IST, converted to
      UTC), recipient (`to[~]`), and status (Queued = pending, Sent = sent with no SES detail,
      Delivered, Opened, Bounced, Failed). Filters survive pagination and are carried into CSV.
- [ ] **Counters:** Sent (`email_sent_status = sent`), Delivered (`delivery_timestamp` not null),
      Opened (`open_timestamp` not null), Bounced (`bounce_timestamp` not null) and Failed
      (`email_sent_status = failed`), computed by SQL `COUNT` over the **whole filtered set**,
      not the visible page.
- [ ] **List:** server-side pagination, ordered `id DESC`, showing date, recipient, subject,
      template, type and status. Status uses the SAN-1154 rules (SES detail overrides, otherwise
      it falls back to `email_sent_status`; "not found in SES" is shown as "Sent · stats
      unavailable in SES", not overwritten). Rows with no SES message id show "Stats not
      available" (custom SMTP or legacy rows).
- [ ] **Request Stats:** the AJAX action takes `recordId` only. The server loads the row by id
      from `$database` and uses the row's own `to` and message id (parsed the same way as
      details.php:323-346). It never trusts POSTed `email` or `messageId`. SES handling, the
      writes to the timestamp columns and the promotional-email side effect all match
      details.php:126-298. Auto-fetch runs only for visible-page rows that the SAN-1154
      AUTO_FETCH rules accept.
- [ ] **CSV export:** requires `$canExportData` in addition to page access. It applies the
      current filters and exports date, recipient, subject, template_code, email_type, status
      and the four timestamps plus bounce message. **Never** `html_content` or `email_data`.
- [ ] **Graceful on a lagging tenant:** if `template_code` does not exist yet in this tenant's
      DB (backend not yet deployed there), the page still loads with the template filter and
      column hidden, instead of throwing an SQL error.
- [ ] **Navigation:** a Quick Links entry "Email Logs" under `$quickLinksCanBroadcast` in both
      `header.php` and `header_without_sidebar.php`.
- [ ] **Conventions:** `/* */` comments only (PHP and inline JS), `count($x) > 0`, output
      buffers flushed before JSON, inline scripts deferred to `window.load`, and `php -l`
      clean on every edited file.
- [ ] New `sc-saas-admin/modules/email_logs/module.spec.md`, and
      `specs/admin-module-specs-index.md` is updated.

## Per-repo plan

### backend (sc-saas-backend), first

1. **Entity:** add `@Column({ name: 'template_code', type: 'varchar', length: 100, nullable: true }) templateCode: string;`
   to `src/core/entities/ses-email-queue.entity.ts`. No index and no enum change.
2. **Options type:** in `src/core/types/ses-email.type.ts` add
   `SendEmailLogOptions { templateCode?: EmailTemplateCode; emailType?: EmailQueueEmailType; broadcastMessageId?: number; skipLog?: boolean; redactSecrets?: string[] }`.
   `SESEmailDataDto` (:11-21) is **not** changed, because it is the POSTed body.
3. **`sendEmail(reqBody, options?)`** (`ses-email.service.ts:239`):
   - On success, call a new private `logSentEmail(reqBody, options, response, sentAt)` unless
     `options?.skipLog`.
   - In the catch, call `logFailedEmail(...)` unless `skipLog`, then rethrow as today.
   - Both helpers are wrapped in their own try/catch, so they never throw.
   - Redaction: if `templateCode` is in `SENSITIVE_TEMPLATE_CODES`, store no body and mask each
     `redactSecrets` value in the subject.
   - Note that `reqBody.html` is already wrapped with the unsubscribe footer at this point
     (:258-268), the same content the old helper stored.
   - While here, fix the unreachable `LOG_EXIT` at :308.
4. **Remove** `addToSesEmailQueueAsSent` (:316-343) and all 51 calls. At each site, pass
   `{ templateCode, emailType: <previous type> }` to `sendEmail()` instead.
5. **Add options to the remaining call sites** (116 total): `{ templateCode: EmailTemplateCode.X }`
   using the same code the function already loads with `getEmailTemplateByTemplateCode`.
   - The OTP, verification and password-reset functions also pass `redactSecrets`.
   - `sendChatMessageEmail` passes `{ skipLog: true }`.
   - The F1 inline writers pass `skipLog: true` and set `templateCode` on their own row.
   - The enqueue-only writers set `templateCode` on their queued entities.
   - Functions that use more than one template (e.g. `sendAdminAccountCreatedEmail`
     :1046-1056) pass the one actually used.
6. **Cron callers:** `ses-email-email-queue.service.ts:72` and `invitation-reminder.service.ts:97`
   pass `{ skipLog: true }`.
7. **Stats cron** (`sync-broadcast-email-stats.service.ts`):
   - Split into two selections with separate budgets: broadcast (unchanged, 300) and other
     (`OTHER_BATCH_SIZE = 900`, with the extra SQL filter
     `JSON_UNQUOTE(JSON_EXTRACT(q.response, '$.response')) LIKE '250 Ok %'` and the 7-day
     "delivered, stop rechecking" rule).
   - Run the broadcast budget first.
   - Keep the stop-on-throttle/AccessDenied behaviour covering both.
   - Filter insights by `Destination` when present.
   - Keep the class and job name `syncBroadcastEmailStats`, so no new cron seed and no
     `cron_jobs` change. Update the class doc comment to say it now covers all types.
   - **Capacity** [INFERRED — real per-tenant volumes are not measured]: 1,200 calls × 200 ms
     is about 4 min per hourly run. With at most about 9 checks per unopened non-broadcast row
     (first check, then every 20 h until delivered + 7 days), 900 per hour (21,600 per day) covers
     about 2,400 new non-broadcast emails per day in the worst case. The per-budget summary log
     shows whether candidates exceed the budget. If they do, raise `OTHER_BATCH_SIZE` or move
     the job's `cron_jobs.time` to every 30 min. That is a data change with no deploy.
8. **Docs:** update `src/modules/cron/module.spec.md` (job description) and the module spec
   covering `core/services` / email (find it via `specs/backend-module-specs-index.md`) to
   record central logging, `template_code` and the redaction rule.

### admin (sc-saas-admin), second (after the backend is live on the tenant)

1. **`modules/email_logs/list.php`:**
   - Auth block as in the acceptance criteria.
   - Build Medoo conditions from GET filters: `email_type`, `template_code`,
     `created_at[<>]` (UTC range), `to[~]`, and status mapped to column conditions.
   - Counters with `$database->count("ses_email_queue", $conds + extra)`.
   - Page rows with `LIMIT => [offset, per]`, selecting no `html_content` / `email_data`.
   - Template label map from `$database->select("spa_email_templates", ["template_code","template_title"])`.
   - Column-existence check for `template_code` (`SHOW COLUMNS ... LIKE 'template_code'`).
2. **Request Stats handler (`submitAction = getEmailStats`)** in the same file:
   - Flush output buffers.
   - Load the row by `(int) recordId` from `$database`.
   - Parse the message id from the stored `response`.
   - Call `SesV2Client->getMessageInsights` with the `spa_amazon_*` constants, as details.php:20-27.
   - Write the timestamps and apply the bounce side effect, as details.php:219-238.
   - Implementation choice: extract the SES-parsing closures (details.php:141-217) into a shared
     helper in `includes/` so both pages use one copy, **or** duplicate them. Prefer the shared
     helper only if the broadcast page is switched to it in the same change **and** re-tested.
     Otherwise duplicate, to keep SAN-1154's page untouched.
3. **CSV export action:** `$canExportData` check, same conditions, streamed with `fputcsv` as in
   details.php:400-432.
4. **`themes/default/html/email_logs/list.php`:** filter form, counters row and table. Port the
   SAN-1154 status/auto-fetch JS (`deriveStatus`, `isDueForAutoFetch`, `postItem`,
   `runWithConcurrency` from `themes/default/html/broadcast_messages/details.php:485-770`),
   limited to visible rows. Counters come from the server, not `recomputeCounters()` (the
   broadcast page computes counters client-side over all rows, which does not scale to a
   tenant-wide log).
5. **Quick Links entry** in `themes/default/html/elements/header.php` and
   `header_without_sidebar.php`.
6. **Docs:** add `modules/email_logs/module.spec.md` (owns: Email Logs page; consumes: the
   `ses_email_queue` DB contract, `spa_email_templates`; tenant_scoping: per-tenant `$database`)
   and update `specs/admin-module-specs-index.md`.

## Cross-Repo Contract Impact

- **REST API (invariant #2):** none. No controller or DTO changes in sc-saas-backend, so there
  is nothing for sc-saas-frontend or admin cURL callers to change. `/audit-contract` should
  confirm zero diff under `src/modules/**/dto` and controllers.
- **Backend to sc-saas-3rdparty-webservices `/ses/send-email`:** body unchanged (acceptance
  criterion). The new options are a second function parameter, not body keys.
- **Shared per-tenant DB table `ses_email_queue`:**
  - Backend adds a nullable column and many more rows.
  - Admin readers are listed in F6. None select `*` with positional assumptions, and none filter
    in a way the new `normal` rows would enter, except the new page. Broadcast details pages
    gain the previously missing instant-broadcast rows.
  - The generic table engine column list (`modules/common.php:183`) is unaffected.
- **Flags (invariant #1):** none added, renamed or removed. `custom_smtp` is only read, as today.
- **Tenant verification (invariant #3), PowerPitch (invariant #6):** not touched.
- **Auth (invariant #4):** no change to JWT. The new admin page uses the existing admin session
  and the `can_broadcast_messages` permission (F8).
- **Tenant scoping (invariant #5):**
  - Backend is one deployment per tenant. The logging insert and the cron use that deployment's
    own DB connection, with no host or tenant config referenced.
  - Admin uses the per-request `$database` only.
  - Run `/check-isolation` on both repos before `in-review`.

## Contracts & invariants

- **Flags:** `custom_smtp` (read only, existing).
- **API:** none (see above).
- **Events:** none. SES event publishing is out of scope.
- **Invariants at risk:** #5 (tenant scoping). It stays safe because all new reads and writes
  use the tenant's own DB handle. #2 is explicitly untouched.

## Test plan

Automated test-first is currently blocked workspace-wide (the "guardian" skill does not exist).
Use the strongest verification available and state explicitly which automated coverage was added.

- **backend:**
  - `npm run build`, `npm run lint`.
  - New jest unit tests for `SESEmailService.sendEmail`: mock axios and `SesEmailQueueEntity.save`.
    Cover: success logs once; failure logs `failed` and rethrows; `skipLog` logs nothing;
    sensitive codes store no body and a masked subject; an insert error does not change the
    result.
  - A test that asserts every `this.sendEmail(` in `ses-email.service.ts` has a second argument.
  - Staging manual checks:
    1. Capture the synchronize DDL (single `ADD COLUMN`).
    2. Trigger an OTP: one row with `template_code = verify-email-address`, `html_content NULL`,
       and a subject without the OTP.
    3. Accept and reject an application: one row each, with the correct `email_type` and
       `template_code`.
    4. Queue a broadcast to N users and run the queue cron: exactly N rows.
    5. Send a chat message: no row.
    6. Run the stats cron: both budgets are logged, broadcast rows are still processed, and a
       delivered OTP row gets `delivery_timestamp`.
- **admin:**
  - `php -l` on every new or edited file.
  - Manual checks: access with and without `can_broadcast_messages`, and as jury and partner
    (both redirected); each filter; counters match SQL run by hand; Request Stats with a forged
    `email` POST field (ignored); CSV with and without `can_export_data`, containing no body
    columns; the page on a DB without `template_code` (column hidden, no error).
- **cross-repo:** on one staging tenant, send one email of each of about 5 types from the
  frontend and admin flows. They appear on Email Logs within a minute, and after 15 min or more
  a cron run or Request Stats shows Delivered. Run `/check-isolation` (backend and admin) and
  `/audit-contract` (backend, expected no-op).

## Rollout

1. **Backend first, per tenant deployment.**
   - Before the first production deploy, confirm on staging that the synchronize DDL is the
     single `ADD COLUMN` (INSTANT on MySQL 8.4.11).
   - No flag gating: logging starts immediately on deploy. There is no backfill.
   - Rollback is safe: an older build ignores the extra column, and rows it writes have NULL
     `template_code`.
2. **Admin second.** The page tolerates tenants whose backend has not yet added the column
   (acceptance criterion), so admin can deploy once and serve lagging tenants safely. It shows
   useful data only after the tenant's backend is live.
3. **After a week:** check the stats cron summary logs on the busiest tenant. If "other"
   candidates regularly exceed the budget, adjust `OTHER_BATCH_SIZE` or the job time (F7 and
   plan step 7).
4. **Table growth:** `ses_email_queue` now receives a row for almost every email.
   - [NOT SPECIFIED IN SOURCE] Current per-tenant row counts and send volumes.
   - Measure `SELECT COUNT(*)` and the approximate daily volume on the largest tenant before
     deploy, and record them in the implementation notes. If the table is large enough that the
     Email Logs `COUNT`s or the cron scan are slow, add an index as a **separate** follow-up
     change. That change is online INPLACE, not INSTANT, so it is deliberately not part of this
     spec's single-`ADD COLUMN` deploy.

## Known limits

- No retroactive stats for emails sent before deploy that were never logged. Previously logged
  types (the 51 call sites) sent within the last 30 days **do** get picked up by the extended
  cron, but have NULL `template_code`.
- Tenants on custom SMTP (`custom_smtp` + `EMAIL_SMTP_*`) get sent/failed only. Their responses
  carry no SES message id, so no delivery, open or bounce data exists.
- Open tracking is approximate (image blocking, privacy proxies such as Apple Mail Privacy
  Protection).
- SES message-insight retention is **assumed** to be about 30 days (unconfirmed. SAN-1155 saw
  fetches work at 12 days and fail at about 71 days).
- Stats are per `to` recipient only. CC recipients are not logged as separate rows.
- Stats appear with up to about 1 h of lag (hourly cron) unless an admin clicks Request Stats.

## Out of scope

- SES event publishing (configuration set to SNS to webhook). Possible later phase.
- A retention or purge policy for `ses_email_queue`. Rows are kept indefinitely, as today for
  the already-logged types. Propose separately if growth warrants it.
- Viewing email bodies in the Email Logs page.
- Any change to sc-saas-3rdparty-webservices, sanchiconnect-saas-tenants, tenants-admin or
  sc-saas-frontend.
- Fixing the password `console.log` at ses-email.service.ts:1103 (file as a separate bug).
- Adding indexes to `ses_email_queue` (see Rollout step 4).
- The `this.fromEmail` shared-state race in the singleton `SESEmailService` (partner sends
  overwrite it, e.g. :380, :1472). This is an existing issue and is not changed here.

## Open questions

None. Former question 1 (account-created emails) was resolved by the user on 2026-09-30:
treat `admin-account-created` and `jury-account-created` as sensitive (see decision 4).

## Implementation notes (2026-09-30, spec-implementer)

Both repos implemented on `ai_native_setup`, **uncommitted**, awaiting review. SAN-1156 and
SAN-1157 moved to In Review.

**Backend (sc-saas-backend).**
- Synchronize DDL, produced offline from TypeORM 0.3.6 metadata (schema builder run against a
  table built from the pre-change entity, no DB connection): exactly one query,
  ``ALTER TABLE `ses_email_queue` ADD `template_code` varchar(100) NULL`` (down:
  `DROP COLUMN`). A control run with an unchanged table produced zero queries. The staging capture
  in the test plan is still needed to rule out drift between the live table and the entity.
- The helper had **49** call sites, not 51 (the 51 counted its own `LOG_ENTER`/`LOG_EXIT`
  strings). All 49 now pass their previous `EmailQueueEmailType` via options. All 116
  `this.sendEmail(` calls pass an options object with `templateCode`. A static jest check enforces
  this.
- `SendEmailLogOptions.templateCode` is typed `EmailTemplateCode | string`, not only
  `EmailTemplateCode`. Invitation codes are computed (`invitation-to-join-<userType>`), and the
  startup-kit email has no template row, so it logs the pseudo-code `startup-kit`
  (`STARTUP_KIT_TEMPLATE_CODE`).
- `last_sent_at` on central rows is the send-completion time. The old helper used a timestamp taken
  just before the send.
- A failed central insert no longer makes the calling function throw after a successful send.
  Before, a failing `addToSesEmailQueueAsSent()` insert did (same failure class as SAN-99).
- Tests added: `src/core/services/ses-email.service.logging.spec.ts`,
  `src/modules/cron/email-log-skip.spec.ts`, `src/modules/cron/sync-broadcast-email-stats.service.spec.ts`
  (60 new tests). The existing `invitation-reminder.service.spec.ts` assertion was updated for the
  new `{ skipLog: true }` argument. Four unrelated suites (`programs.repository`,
  `application-programs.repository`, `partner-domain-access.service`, `global-onboarding-design`)
  fail identically on a clean HEAD (22 failures, pre-existing).
- F4's `console.log('attributesToMap', ...)` no longer exists in `sendAdminAccountCreatedEmail`
  (checked 2026-09-30), so there is nothing to file. Two other `console.log('DEBUG TEMPLATE CONTEXT')`
  calls remain in the payment-reminder functions.

**Admin (sc-saas-admin).** New `modules/email_logs/list.php`, `themes/default/html/email_logs/list.php`
and `modules/email_logs/module.spec.md`, plus Quick Links in both headers. The SES-parsing code is
duplicated from `broadcast_messages/details.php` (plan step 2), and that page is untouched.
Verified with a PHP built-in-server harness: the real module, template, Medoo and sparkAdminTpl over
SQLite with stubbed session, permissions and SES. Checked: auth redirects (no permission, partner,
jury, including POST); counters over the whole filtered set; pagination; each status filter;
type/template filters; invalid input ignored; default and invalid dates; CSV filters, no bodies,
formula guard, `can_export_data` gate; Request Stats with forged `email`/`messageId`/`sesRegion`
(ignored, row's own values used, bounce side effect hits the row's recipient only); pending and
notFound paths; no-message-id rows skip SES; a lagging tenant without `template_code` loads with the
template filter and column hidden. The inline JS passes `node --check`. It was not run in a browser.

**Open follow-ups (not in scope, not done).**
- Pre-existing: `sendEmail()` writes `smtpServerSettings` (including the tenant SMTP password) onto the
  caller's object. The three inline writers (instant invitation, startup kit, growth-metrics
  invitation) then save that object into `ses_email_queue.email_data`, so on custom-SMTP tenants the
  SMTP password lands in that JSON. FA-009's central rows store `email_data = NULL` and are not
  affected. Worth a bug.
- Pre-existing: `auditServiceUsage()` stores the unmasked subject, which includes the OTP, in
  `service_usage.data`.
- Admin Request Stats merges all `Insights[]` entries, as details.php does. The backend cron now
  scopes to the row's `Destination`.
- Rollout step 4 (per-tenant `COUNT(*)` and volume) could not be measured without DB access.

