---
id: FA-010                      # next free FA- id (FA-009 is the last). Linear: Enhancement project (P-SAN-48), milestone "Jury NDA Signing"; parents SAN-1488 (backend), SAN-1489 (admin).
title: Jury NDA Signing for Application Evaluation Rounds
type: feature
status: approved                # [CONFIRMED — Sandeep (spec owner), 2026-10-01] approved to build. Footer + owner sign-off CONFIRMED same day; DPDP decided as 'retain' pending legal; legal click-wrap sign-off still open (release gate).
linear: https://linear.app/sanchiconnect/issue/SAN-1488   # parent tasks SAN-1488 (backend) and SAN-1489 (admin); milestone "Jury NDA Signing" in project Enhancement
owner: sandeep.k@sanchiconnect.com
repos: [backend, admin]         # dependency order. tenants, frontend, sc-saas-3rdparty-webservices, ai-startups-analyzer, tenants-admin are deliberately NOT touched — see "Cross-Repo Contract Impact".
contracts:
  api:
    - "POST api/v1/admin-actions/jury-nda-signed-copy-email/:adminMd5   (NEW, backend) — email the signed NDA PDF to the juror; auth = :adminMd5 path token (existing admin-actions convention)"
    - "POST api/v1/admin-actions/jury-nda-notification-email/:adminMd5   (NEW, backend) — reminder / re-sign-required / decline-notice emails; auth = :adminMd5 path token"
    - "POST api/v1/admin-actions/jury-startup-allotment-email/:adminMd5   (CHANGED, additive only) — optional DTO fields ndaRequirement, ndaNote so the assignment email states the NDA requirement (BRL-04)"
    # Schema (backend owns it, synchronize:true — precedent SAN-1028 zenxai_calls): 3 new columns on application_program_rounds, 2 new tables (jury_nda_versions, jury_nda_acceptances), 1 new column on spa_admin_roles. Not API routes; listed because sc-saas-admin reads/writes them directly via Medoo.
  flags: []                     # NONE — see "Contracts & invariants > Flags"
  events: []                    # none. New ses_email_queue email_type value 'jury_nda' (additive).
tenant_scoped: true
depends_on: []
created: 2026-10-01
---

# Jury NDA Signing for Application Evaluation Rounds

## Source & evidence status

- **Requirements sources (read in full, 2026-10-01):** `~/Downloads/SanchiAPP_Jury_NDA_Signing_BRD_v1.0.pdf` — **BRD v1.0 (consolidated with wireframes), 1 Oct 2026, owner Dr. Sunil Shekhawat, status "For sign-off"** (40 pp; Appendix A = 22 wireframe screens A1–A10, J1–J8, E1–E3, D1; Appendix B = requirement-to-wireframe traceability). It supersedes the v0.1 `.docx` and the standalone wireframe PDF, which I read earlier. BRD ids (BR-, FR-A/J, BRL-, D-) are cited as written.
- **v1.0 closes the earlier questions:** BRD §17 turns v0.1's OQ-1..12 into decisions **D-1..D-12** (each on its proposed default; the owner may override any at sign-off, Assumption 5). D-2 Decline with optional reason; D-3 notify admin only, re-allotment manual; D-4 banner only after skip; D-5 static PDF + certificate page; D-6 one NDA per round; D-7 no admin CC; D-8 access via the "View Jury NDAs" role permission only; D-9 programme duration + 3 years, per client (FR-A19); D-10 settings stay editable with warnings + versioning; D-11 no countersignature; D-12 jury only. **Corrections to earlier drafts of this spec:** retention is **FR-A19** (not FR-A20); **there is no BRL-11** (rules are BRL-01..10; wireframe A6 maps to FR-A8, BRL-05, BRL-06, BRL-09). The Sign-off table (§20) is still blank — the spec cannot be `approved` until the owner signs. Spec decision ids below are prefixed `D-<Name>` to avoid clashing with the BRD's `D-<n>`.
- **Workspace (checked 2026-10-01):** six repos are cloned under `SanchiSaaS/`: `sanchiconnect-saas-tenants`, `sanchiconnect-saas-tenants-admin`, `sc-saas-3rdparty-webservices`, `sc-saas-admin`, `sc-saas-backend`, `sc-saas-frontend` (each its own `.git`). `ai-startups-analyzer` is a sibling folder outside `SanchiSaaS/` (`~/Desktop/ai-startups-analyzer`) and is not touched. The SanchiPowerpitch workspace is not present. So the gateway claims below are now code-verified against `sc-saas-3rdparty-webservices`; `tenants` was available but needs no change (no flag, no verify_tenant shape change).
- **Tag legend** (specs/spec-authoring-practices.md Practice 3): unmarked claim + `file:line` = evidenced; `[INFERRED — requires validation]`; `[NOT SPECIFIED IN SOURCE]`; `[DESIGN DECISION PENDING]`; `[DECIDED — recommended default]` = decision taken on the recommended default, pending owner confirmation (see "Decisions").

## Problem

Programmes want every juror who evaluates a round to accept a round-specific NDA before seeing applicant data, with a tamper-evident record (who/when/IP/version/hash), a signed copy emailed to the juror, and admin-side tracking, reminders, export and retention (BR-01..09, BRL-01..10). Nothing exists today: no NDA concept in `sc-saas-backend/src` or `sc-saas-admin/modules|includes` [INFERRED — term-based grep, not exhaustive].

**Key code finding:** the juror experience is **not in `sc-saas-frontend` and not behind `sc-saas-backend`**. Jurors are `spa_admin_users` with `jury_role_id` who log into the **PHP admin panel** (`sc-saas-admin/modules/jury/*`, `themes/default/html/jury/*`). The jury module "makes no direct API calls" (`sc-saas-admin/modules/jury/module.spec.md:58-59`) and reads the tenant DB directly via Medoo. Therefore:
1. The **BRL-03 server-side gate lives in `sc-saas-admin`**; backend has no juror-facing application-data endpoint.
2. `sc-saas-frontend` is untouched.
3. Wireframes show a modern SPA-style UI; the implementation is PHP + `sparkAdminTpl` + Bootstrap 4 + jQuery — adapted, not pixel-matched (Decision D-UI).

## Decisions taken on recommended defaults

Each is `[DECIDED — recommended default]`; the owner may override. Spec Q-numbers refer to the retired question list.

| # | Decision | Basis |
|---|---|---|
| D-Scope (Q2) | v1 covers **application-management rounds only** (`application_program_rounds`). Legacy `program_rounds`, mentor and venture-studio/individual jury flavours are out of scope and documented as a residual gap. | BRD title "Application Evaluation Rounds" |
| D-Reviewers (Q3) | Jury **reviewers** (`is_jury_reviewer`) are **exempt** — only evaluating jurors sign. | BRD D-12 "Jury only"; BRD §4 excludes "reviewers" |
| D-Gate (Q4) | **Default-deny** for jury-role sessions on any route the gate cannot resolve to a round while the juror has ≥1 blocking mandatory round; plus resolver-based per-route coverage. Manual verification with a real juror session required. | BRL-03 "every API serving application data" |
| D-Email (Q5) | Signed copy / reminders / notices sent through new **backend** endpoints via `SESEmailService` (queue row + delivery/bounce back-fill), not admin PHPMailer. No admin CC. Gateway verified to pass attachments straight to nodemailer (no 3rdparty change). | D-7; FR-J12 needs delivery tracking |
| D-Merge (Q6) | PDF merge of original + certificate done with a **`qpdf`/`pdfunite` binary** invoked from admin (certificate page rendered by dompdf). Binary install on admin hosts is an infra prerequisite. | no PHP merge lib in `composer.json`; free FPDI can't read PDF ≥1.5 xref [INFERRED] |
| D-Storage (Q7) | NDA originals and signed copies live in a **separate private bucket** (SSE enabled, delete-deny/Object Lock, India region), presigned ≤5 min, no public/CDN URL. The shared bucket and `modules/aws/ajax`/`acl_update` are not used for NDA data. | NFR §16; aws module spec |
| D-Immut (Q8) | Immutability is **application-level**; `spa_admin_logs` reused for audit (`module='jury_nda'`). DB triggers are a documented optional DBA hardening step, not a code requirement. | backend has no migration framework |
| D-Perm (Q10) | `can_view_jury_ndas` is a **per-role** boolean on `spa_admin_roles`. Super Admin implicitly allowed. Programme managers need the permission too (plus existing PM/partner scoping). | D-8 "admin role permission" |
| D-Notif (Q11) | No notification table. Alerts are **derived state** (badges + panel on the allotment tab, no read/unread). "Round admins" = programme's `program_managers` ∪ holders of `can_view_jury_ndas`. | no per-admin notification mechanism exists |
| D-Tracker (Q12) | NDA tracker is **added to the existing Jury Allotment tab** (`edit_program_round_jury.php` area), not a new page. | FR-A10, wireframe A7 |
| D-Retention (Q9c) | Retention policy stored per tenant in two `spa_settings` rows, edited by Super Admin in the admin panel; post-retention manual delete action by Super Admin, each deletion audit-logged. | wireframe A10 |
| D-Name (Q14) | Typed name vs `spa_admin_users.name`: trim + collapse whitespace + case-insensitive; no diacritic/initial folding; error "Name must match your profile: <name>". | FR-J7, wireframe J3 |
| D-IP (Q15) | Store derived IP **and** raw `REMOTE_ADDR`; certificate prints the derived IP. | `getIP()` is header-spoofable |
| D-Ref (Q17) | Reference id `NDA-R{round_id}-{6-digit acceptance id}`. | wireframe D1 sample |
| D-TZ (Q18) | Certificate and UI timestamps always **IST**; stored UTC. | FR-J10 |
| D-Flag (Q19) | **No tenant flag.** Per-round default-Off is the gate. | avoids 3-repo flag propagation |
| D-Config (Q21) | Whoever may edit round settings today may configure NDA; programme managers may toggle off (with confirmation). | assumption |
| D-Retry (Q22) | Retry cron every 5 min, max 3 attempts; "persistent failure" = 3 failed send attempts. Bounce after a delivered-looking send is surfaced via `bounce_timestamp` but does not trigger resend. | FR-J12 |
| D-Cost (Q23) | One indexed lookup per jury request is accepted; measure in pilot. | |
| D-Midround (Q24) | Turning on Mandatory blocks Pending/Skipped jurors on next entry; submitted scores untouched. | BRL-05, BRL-09 |
| D-End (Q9a) | Retention clock = **the later of the programme's `application_closed_date` and the latest `jury_nda_acceptances.decided_at` in that programme**, plus the retention period. Rounds carry no end date (`application-program-rounds.entity.ts` has none) and `program_closed` is a boolean with no timestamp (`application-programs.entity.ts:93`), so this needs no new column and never expires earlier than N years after the last NDA activity. `[DECIDED — recommended default; conservative]` | no programme-end timestamp exists |
| D-Clone (Q13) | **FR-A9 is deferred out of v1.** No round clone/duplicate exists for `application_program_rounds` in backend or admin (only a cross-tenant *programme* clone is referenced in `application-programs.repository.ts:171-259`, implemented elsewhere and not visible here). Any future clone path must copy NDA settings + current file as a new version row and **zero** acceptance rows; the cross-tenant programme clone must not copy `jury_nda_*` rows. Filed as a follow-up. | code search |
| D-Sender (Q16) | Sender = the platform's standard programme sender, identical to other program emails: `<brandName> <SaaSSettingKey.EMAIL_SENDER_SES>` (`ses-email.service.ts:259-261`), with display name `<partner.name>` for partner (spoke) programmes (:1588-1590). Reply-to = `application_programs.reply_to_email` (`application-programs.entity.ts:273`) when set, else none. | existing convention |
| D-Footer | Signed-copy email is sent **without** the unsubscribe footer (footer-less option in backend `sendEmail`; default for all other callers unchanged). `[CONFIRMED — Sandeep, 2026-10-01]` | legal-record email must always reach the juror |
| D-DPDP | Signed NDAs are **retained for the retention period** as a legal-obligation record, not erased on request; legal to confirm. `[CONFIRMED — Sandeep, 2026-10-01; legal confirmation pending]` | FR-A17, BRL-10 |
| D-Signoff | BRD v1.0 signed off by the business owner with **no overrides** to D-1..D-12; the `[DECIDED — recommended default]` decisions above stand. `[CONFIRMED — per Sandeep, 2026-10-01; relayed, not seen as a signed document]` | BRD §20 |
| D-UI (Q20) | Wireframes adapted to the PHP/Bootstrap 4 theme; **PDF.js added as a static asset** for scroll-to-end detection and zoom. Permission screen and audit viewer have no wireframe — follow existing `auth/admins.php` and `system_logs` patterns. | no `<iframe>` scroll events |

## Prior art (Practice 1 — reused vs new)

| Need | Existing mechanism | Decision |
|---|---|---|
| Round record / toggles | `application_program_rounds` (`application-management/entities/application-program-rounds.entity.ts:11-12`) with per-round booleans (`editable_jury_ratings` :76-82, `jury_can_view_overall_ratings` :92-98, `freeze_applications` :145-151); admin toggles in `sc-saas-admin/modules/application_management/edit_program_round.php` (:228, :276, :329, :372) | **REUSE**: 3 new columns on this table |
| Jury-to-round allotment | `application_program_rounds.jury_members` JSON (:22-23) and `application_program_rounds_jury` (`application-program-rounds-jury.entity.ts:11-46`); admin `add_jury_member` :599, `remove_jury_round` :677, `sendAllotmentEmail` :988 | **REUSE** as "is juror in round" source of truth |
| Jury tracker | none (no "tracker" in `modules/application_management`); closest `edit_program_round_jury.php` (:256) | **EXTEND** allotment tab (D-Tracker) |
| Round clone (FR-A9) | none (`cloneRound/duplicateRound/copyRound` → 0 hits); `program.php:1015` "Create a duplicate" is actually the delete handler | FR-A9 deferred (D-Clone) |
| S3 upload/presign | `putObject` + `'ACL'=>'private'` (`includes/portfolio_functions.php:241-246`); `generateS3SignedUrl()` default TTL **7 days** (`includes/core_functions.php:3381-3404`) | **REUSE pattern**, new private bucket, TTL ≤5 min |
| PDF | admin `dompdf ^3.1` (`composer.json:40`, `application-submission-detail.php:417-426`); backend `PdfRenderHtmlService` (`core/upload-module/pdf-render-html.service.ts:16`); no merge capability | dompdf for certificate; merge via qpdf (D-Merge) |
| SHA-256 / ZIP / CSV | `hash_file('sha256')`; `ZipArchive` (`submission-application-management.php:2274,2532`); `includes/xlsx_export_helpers.php` | **REUSE** |
| Transactional email | `SESEmailService.sendEmail` (`ses-email.service.ts:264-354`), one `ses_email_queue` row per send; attachments shape `[{path, filename}]` (`:7370-7375`); jury assignment email `admin-actions.controller.ts:959-973` → `sendJuryStartupAllotmentEmail` (`:5548-5626`), called from `edit_program_round.php:25-39` | **REUSE**; 2 new endpoints; additive change to allotment email |
| Delivery/bounce status | `ses_email_queue.send/delivery/bounce_timestamp, bounce_message` (`core/entities/ses-email-queue.entity.ts:123-153`), back-filled by `SyncBroadcastEmailStatsService` for all email types (`modules/cron/sync-broadcast-email-stats.service.ts:27-53`) | **REUSE** for FR-J12 |
| Broadcast attachments | resolve to public ImageKit URLs (`ses-email.service.ts:1681-1700`) | **REJECTED** (public links violate NFR) |
| Audit | `createAdminLogs(...)` → `spa_admin_logs` (`core_functions.php:6514-6540`), viewer `modules/system_logs` | **REUSE** (D-Immut) |
| Permissions | per-role bool on `spa_admin_roles` (`spa_admin_roles.entity.ts:70-76`), read by `checkRole()` (`core_functions.php:731-743`), edited in `themes/default/html/auth/admins.php` | **REUSE pattern** (D-Perm) |
| Juror name | `spa_admin_users.name/.email` (`spa_admin_users.entity.ts:9,12`) | **REUSE** |
| Client IP / IST | `getIP()` (`core_functions.php:330-356`, spoofable); `convertToKolkataTime()` (:6542-6549) | **REUSE with caveat** (D-IP, D-TZ) |
| Per-tenant config | `spa_settings` + `getSetting()` (`core_functions.php:3287`) | **REUSE** (D-Retention) |

## Acceptance criteria

All must pass for `done`. Ids reference BRD v1.0 and its wireframes (Appendix A).

**Admin configuration (Round settings → Jury allotment)**
- [ ] AC-1 (FR-A1) New and existing rounds default `nda_required=0`; with NDA off every juror route behaves byte-identically to today.
- [ ] AC-2 (FR-A2, FR-A3) With NDA on, requirement type (Mandatory/Optional) has no preselected value and a PDF is required before saving/publishing; otherwise inline error and no DB write (errors shown only after a save attempt).
- [ ] AC-3 (FR-A4) Upload accepts only a real PDF (server-side `finfo` MIME sniff, not extension) ≤ 10 MB; inline error naming the problem; SHA-256 of the exact bytes stored.
- [ ] AC-4 (FR-A5, FR-A7) Admin sees file name, version, upload date, uploader, size, Preview (renders the juror dialog with actions disabled) and a ≤300-char note with counter.
- [ ] AC-5 (FR-A6, BRL-07, wireframe A5) Replace creates a new `jury_nda_versions` row; the "Do signed jurors need to sign again?" dialog appears only when ≥1 juror signed the current version, with no default for a new round; Yes → `requires_resign=1`, No → `0`; older versions and signatures remain.
- [ ] AC-6 (FR-A8) Turning NDA off after any signature requires confirmation ("N jurors have signed. Their signed copies stay available…"); no NDA row is deleted.
- [ ] AC-7 (FR-A9, "Not wireframed" in v1.0) **Deferred (D-Clone)** — BRD still lists FR-A9, but no round-clone path exists to attach it to; owner to confirm the deferral at sign-off. Not implemented in v1. Guard: the cross-tenant programme clone must not copy `jury_nda_*` rows.
- [ ] AC-29 (wireframe A6, BRL-05/06) Changing requirement type shows a confirmation with counts of affected jurors ("2 jurors skipped and 1 hasn't opened the round… Scores already submitted are kept."); Mandatory→Optional uses the same pattern and notes Declined jurors can now skip.
- [ ] AC-33 (wireframe A3/A5) Version history lists every version with uploader, date and signature count; versions are never deletable.

**Juror flow**
- [ ] AC-8 (FR-J1, BRL-03) In a Mandatory round with no valid acceptance, **every** juror-reachable route in "BRL-03 enforcement" returns the NDA-required response and **fetches no application data** (request trace shows no `forms_submissions`/attachment query). Dashboard, email link and direct URL hit the same gate.
- [ ] AC-9 (FR-J2..J4) Mandatory modal shows programme, round, note, embedded PDF with zoom, and Download; checkbox, typed-name field and Accept stay disabled until the PDF is scrolled to the end; no close icon, no click-outside/Esc dismissal.
- [ ] AC-10 (FR-J7) Accept needs the checkbox and a typed name matching `spa_admin_users.name` per D-Name; otherwise "Name must match your profile: <name>" and nothing is stored.
- [ ] AC-11 (FR-J8, FR-J10) On accept: one append-only `jury_nda_acceptances` row (UTC time, typed name, IP, raw remote addr, user agent, reference id, version id, original SHA-256) and a signed PDF = **byte-unaltered original pages + Acceptance Certificate** with all FR-J10 fields (IST to the second, "No countersignature", full SHA-256). Generated in < 10 s.
- [ ] AC-12 (FR-J11, FR-J12) Signed PDF emailed **only** to the juror (no admin CC), subject `Your signed NDA: <Programme> / <Round>`, file `Signed_NDA_Round<N>_<Juror_Name>.pdf`. If PDF/email fails, acceptance is still recorded and access granted; retried per D-Retry; persistent failure marked `failed` and flagged in the tracker. Delivery status shown = sent/delivered/bounced/failed. ≥99 % delivered within 2 min (O4).
- [ ] AC-13 (FR-J5, D-3) Decline (optional reason) stores `declined`; round stays locked; juror returns to dashboard; round admins get an email + derived alert with reason, count of the juror's allotted applications and a link to the tracker; juror can re-open via "Review NDA" and accept later. No automatic re-allotment.
- [ ] AC-14 (FR-J6a-c, D-4) Optional round: "Accept & sign" or "Skip for now"; Skip stores `skipped`, opens the round, shows a persistent non-dismissible banner "You haven't signed the NDA for this round. [Review & sign]" on every round page; popup does not auto-reappear; juror can sign later via banner or "My NDA" header link.
- [ ] AC-15 (FR-J9, BRL-02) A juror with a valid acceptance is never re-prompted; re-sign only when the accepted version is below the validity floor (BRL-07), with the J8 text.
- [ ] AC-16 (FR-J13) Juror can re-download only their own signed copy ("My NDA"); each download audit-logged; presigned ≤ 5 min.
- [ ] AC-17 (BRL-04) Dashboard cards show NDA badges (required / available to review / declined / signed); assignment email states the requirement; neither contains application content.
- [ ] AC-18 (BRL-08) A juror added later is subject to current settings at first entry.
- [ ] AC-19 (BRL-09) Changing requirement type never alters submitted scores; status is re-derived.
- [ ] AC-32 (BRD §16) Viewer supports zoom; modal responsive and keyboard-navigable; a 10 MB PDF renders < 3 s.

**Admin visibility, export, retention**
- [ ] AC-20 (FR-A10..A12) Allotment tab shows per-juror NDA Status (Pending, Signed, Skipped, Declined, Re-sign Required, Not Applicable); clickable count tiles; filter/sort by status.
- [ ] AC-30 (FR-A11) Tiles (Signed / Pending / Declined / Re-sign required, + Skipped for Optional) satisfy the round-level summary.
- [ ] AC-21 (FR-A13) Per signed juror: view/download signed PDF + details (version, signed-at, typed name, IP, browser, reference id, email status, history timeline from audit log, decline reason). Each view/download is audit-logged.
- [ ] AC-22 (FR-A14, FR-A15) Bulk ZIP `<RoundName>_<JurorName>_<Date>.pdf` and CSV/Excel report (name, email, status, version, timestamp, IP, email delivery status); exports audit-logged.
- [ ] AC-23 (FR-A16, wireframe A9) Reminder to Pending / Re-sign-required jurors only (others dropped with a note), editable message (HTML-escaped), fixed line "The email includes a link to the round. It never includes application details.", logged.
- [ ] AC-24 (FR-A17, BR-08, BRL-10) No code path edits or deletes a signed copy or record during retention — including `deleteApplicationProgram`, `deleteRound`, `remove_jury_round` and the generic `spa_actions.php` delete endpoints — for any role including Super Admin.
- [ ] AC-25 (FR-A18) Only Super Admin and roles with `can_view_jury_ndas` open signed copies / details (others 403); existing PM/partner scoping preserved.
- [ ] AC-26 (FR-A19, BRL-10, wireframe A10) Super Admin sets per-tenant retention (default programme end + 3 yrs, or custom N yrs); records past retention are listed; deletion is manual, Super Admin only, each deletion audit-logged.
- [ ] AC-27 (BR-09) Every action in BRD §14's audit list produces a `spa_admin_logs` row with `module='jury_nda'`.
- [ ] AC-28 (BRD §15; "Not wireframed" in v1.0) When the last allotted juror in an Optional round signs, round admins get a derived "all signed" alert; when a signed-copy email fails after retries they get a failure alert.

## Data model

**Extended (backend entities; backend owns schema via `synchronize:true`, `src/core/database/database.module.ts:32`; precedent `core/zenxai/zenxai.module.ts:5-10`):**
- `application_program_rounds` + `nda_required` bool default false, `nda_requirement_type` enum(`mandatory`,`optional`) nullable, `nda_admin_note` varchar(300) nullable.
- `spa_admin_roles` + `can_view_jury_ndas` bool default false.

**New tables (no FKs, zenxai precedent; never deleted by product code during retention):**
- `jury_nda_versions`: `id`, `program_id`, `round_id`, `version_no`, `file_key`, `original_file_name`, `file_size`, `sha256` char(64), `requires_resign` bool, `is_active` bool, `uploaded_by`, `created_at`. **Validity floor** = highest `version_no` with `requires_resign=1`; an acceptance is valid iff its version ≥ floor (encodes Replace Yes/No with no bulk update).
- `jury_nda_acceptances` (append-only events): `id`, `program_id`, `round_id`, `jury_id`, `version_id`, `decision` enum(`signed`,`skipped`,`declined`), `decided_at` UTC, `typed_name`, `ip_address`, `ip_remote_addr`, `user_agent`, `reference_id` unique, `signed_pdf_key`, `signed_pdf_sha256`, `decline_reason`, `email_status` enum(`pending`,`sent`,`failed`,`not_applicable`), `email_attempts`, `email_last_error`, `ses_email_queue_id`, `created_at`. Index `(round_id, jury_id, id)`; current state = latest row.
- **Status derived at read time, never stored** (one shared PHP function, mirrored in backend for the cron): Not Applicable / Signed (latest `signed`, version ≥ floor) / Re-sign Required (latest `signed`, version < floor) / Skipped (latest `skipped` and type=optional) / Declined (latest `declined` and type=mandatory) / Pending (all else, incl. Declined under Optional per BRL-06).
- **Audit:** `spa_admin_logs`, `module='jury_nda'`; actions `nda_toggled`, `nda_type_changed`, `nda_uploaded`, `nda_replaced`, `nda_resign_triggered`, `nda_viewed`, `nda_accepted`, `nda_skipped`, `nda_declined`, `nda_copy_viewed`, `nda_copy_downloaded`, `nda_bulk_exported`, `nda_report_exported`, `nda_reminder_sent`, `nda_retention_changed`, `nda_record_deleted`.
- **Storage:** private NDA bucket (D-Storage), key `<storage_domain>/jury_nda/<program>/<round>/…`; never `generateS3FileUrl` (public ImageKit, `core_functions.php:3367-3379`).
- **Retention:** `spa_settings` rows `jury_nda_retention_mode` (`programme_plus_3y` | `custom_years`) and `jury_nda_retention_years`. "Programme end" has no column; see D-End.

## Per-repo plan

Dependency order: backend → admin.

### backend
- New module `src/modules/jury-nda/` with its own `module.spec.md`: entities `JuryNdaVersionsEntity`, `JuryNdaAcceptancesEntity`; new columns on `ApplicationProgramRoundsEntity` and `SpaAdminRolesEntity` (`modules/global/admin/spa_admin_roles.entity.ts`).
- `core/constants/enum.ts`: `EmailQueueEmailType.JURY_NDA='jury_nda'` (:923-948); `EmailTemplateCode` entries `jury-nda-signed-copy`, `jury-nda-reminder`, `jury-nda-resign-required`, `jury-nda-declined-admin`. Seed in `modules/global/admin/spa_email_templates.repository.ts` beside `admin-jury-allotment-email` (:1688-1695) [INFERRED — requires validation: whether master-default install inserts only missing rows so existing tenants receive them].
- **Endpoint 1** `POST api/v1/admin-actions/jury-nda-signed-copy-email/:adminMd5` (beside `admin-actions.controller.ts:959`). DTO `JuryNdaSignedCopyEmailDto`: `acceptanceId`, `email @IsEmail`, `receiverName`, `programName`, `roundName`, `referenceId`, `signedPdfKey`, `filename`, `partnerId?`. Validates admin via `checkIsValidAdmin` (`admin-actions.service.ts:222-252`); loads the acceptance by id and **checks key/email/round against the row**; idempotent (no resend if `email_status='sent'`); presigned URL via `UploadService.getSignedUrlWithCustomExpiration` (`upload.service.ts:437`) from the NDA bucket; `SESEmailService.sendEmail` with `attachments:[{path,filename}]`, `emailType: JURY_NDA`, `broadcastMessageId: acceptanceId`; updates acceptance email columns. No admin CC. Unsubscribe-footer suppression variant (Open Q-1).
- **Endpoint 2** `POST api/v1/admin-actions/jury-nda-notification-email/:adminMd5`: DTO `{type:'reminder'|'resign_required'|'declined_admin', recipients[], programName, roundName, roundUrl, adminMessage?, jurorName?, reason?, allottedCount?, trackerUrl?}`; `adminMessage` HTML-escaped; no application-content fields by construction (BRL-04).
- **Change** `jury-startup-allotment-email` DTO + `JuryStartupAllotmentEmailDataType` + `sendJuryStartupAllotmentEmail` (`ses-email.service.ts:5548-5626`): optional `ndaRequirement`, `ndaNote`; `nda_notice` shortcode. `whitelist:true` keeps old callers unaffected.
- **Cron** `retryJuryNdaEmails` (jobs registered via `cron_jobs` rows): `decision='signed' AND email_status IN ('pending','failed') AND email_attempts<3`, every 5 min (D-Retry); delivered/bounced come from the existing stats cron.
- **Auth model:** both new routes use the admin-actions convention — no JwtAuthGuard; authorised by `:adminMd5` resolved through `AdminUsersEntity.authToken` (`admin-actions.service.ts:222-231`). The token is a URL-path bearer secret on a role-1 account (`:235-239`): routes must never be exposed to a juror browser; admin calls them server-side only. No unauthenticated route is added.
- **Tenant scoping (#5):** one deployment per tenant; reads/writes only this DB; presigned URLs only for keys read from the acceptance row.
- Verify: `npm run build`, `npm run lint`, existing `npm test`; after-the-fact jest specs for status derivation and the retry cron/email service.

### admin
- **`includes/jury_nda_functions.php`** (included beside `index.php:31-38`): `juryNdaState`, `enforceJuryNdaGate`, `juryNdaRecordDecision`, `juryNdaBuildSignedPdf`, `juryNdaAudit`, plus a table-existence probe so admin deployed before backend degrades to "NDA off".
- **Gate (BRL-03):** a single pre-dispatch hook in the front controller `index.php:57-76`, jury-role sessions only (mind the `admin_roles` plural/singular session-key trap, `modules/jury/module.spec.md:245-249`).
- **Config UI** in `modules/application_management/edit_program_round.php` + theme, following the toggle pattern (:228/:276/:329/:372): `jury_nda_save_settings`, `jury_nda_upload_version`, `jury_nda_replace_version`, `jury_nda_toggle_off`; each with `checkLoggedIn()`, non-jury, `verifyCSRFToken()`, PM/partner scoping as `submission-application-management.php:1466-1494`.
- **Tracker / details / exports** on the Jury Allotment tab (D-Tracker): tiles, filters, per-juror detail drawer, signed-copy view/download (presigned ≤5 min, audit write first), ZIP (`ZipArchive`), CSV/XLSX (`xlsx_export_helpers.php`), reminders (backend endpoint 2). Gate: Super Admin (`super_admin_role_id`, `config.php:224-225`) or `checkRole('can_view_jury_ndas')` + PM/partner scoping.
- **Juror UX:** `modules/jury/nda.php` (`get_state`, `get_pdf`, `accept`, `decline`, `skip`, `my_copy`); modal + banner + dashboard badges in `themes/default/html/jury/round-applications.php`, `dashboard.php` and the other round templates. Each endpoint: `checkLoggedIn()` + jury role + CSRF + **juror allotted to the round** (today `round-applications.php:541-552` does not verify allotment of the URL's round).
- **PDF:** `finfo` validation, original bytes stored untouched, `hash_file('sha256')`, certificate via dompdf, merge via qpdf (D-Merge). **PDF.js** as a new static asset (no PDF asset exists under `themes/default/assets`).
- **Permission UI:** `can_view_jury_ndas` control in `themes/default/html/auth/admins.php` (pattern :398/:1051).
- **Protect NDA data from existing destructive paths (AC-24):** refuse in `program.php:1016-1085` (`deleteApplicationProgram`) when any `jury_nda_*` row exists; same for `deleteRound`; keep `remove_jury_round` (`edit_program_round.php:677`) away from acceptance rows; denylist `jury_nda_versions`/`jury_nda_acceptances` in `modules/ajax/spa_actions.php` `table_management` and generic table/add/edit handlers.
- **Retention UI** (Super Admin only): section in `modules/developer/settings_management.php` writing the two `spa_settings` rows; past-retention list; manual audited delete action.
- **Auth model (every new route):** session login + role check + CSRF; juror routes = jury role + allotted to that round; admin routes = Super Admin or `can_view_jury_ndas` + PM/partner scoping; signed-copy download only after the audit write. None unauthenticated. Do **not** copy the `modules/aws/*` pattern (`aws/module.spec.md:71-79`).
- **Tenant scoping (#5):** all queries on the per-request `$database` selected by `admin_domain`; never `$mainDatabase` for NDA data; retention from this tenant's `spa_settings`.
- Verify: `php -l` on every edited file; CLI harness for `juryNdaState` and `juryNdaBuildSignedPdf`; manual repro matrix.

## BRL-03 enforcement — mechanism and inventory

**Mechanism:** `enforceJuryNdaGate()` called once from `index.php` immediately before `include $filename` (both branches, `index.php:66-75`), jury-role sessions only.
1. Resolve the route's round scope: `jury/round-applications/program/{p}/round/{r}/{uuid}` (`$vars[3],[5],[6]`), `jury/round-applications-overall-ratings` (`$vars[3],[5]`), `jury/review-applications-ratings` (`$vars[2],[4]`), POSTs carrying `programId`/`roundId`/`submission_id` (e.g. `dashboard.php:25-53`), and submission-id routes outside `jury/*`.
2. Round `nda_required=1`, Mandatory, state ≠ Signed → **deny before the module loads**: HTML → redirect to the NDA entry; AJAX/POST → `{error:true, success:false, errorCode:'nda_required'}` with HTTP 403. Optional → allow (banner/popup are UX). Off → allow.
3. **Fail closed on errors:** Medoo returns `false` on query errors (`specs/bug-fixes/SAN-1151-admin-system-messages-count-crash.md:12-16`); a `false` from the lookup on a round whose columns exist denies. Missing NDA columns/tables (backend not yet deployed) = feature off = allow.
4. **Default-deny** (D-Gate): unresolvable route + jury session + ≥1 blocking mandatory round → deny.

| # | Route / handler | Data exposed | Role guard today | Covered |
|---|---|---|---|---|
| a1 | `jury/round-applications/…` GET (`modules/jury/round-applications.php:541-806`) | allotted list (:552), `forms_submissions` (:662), answers (:781-795), documents (template :591 direct href), jury-question files (:820, :1152 presigned), Power Pitch URL (:789-790) | jury role :18-22 | yes |
| a2 | same file, POST `addQuestionAnswer :29`, `save_sort_by_session :94`, `mark_not_interested :124`, `request_call :204`, `addRating :286`, `answerQuestions :458` (run before round resolved from URL, ids from POST) | scoring / ratings / call requests | jury role | yes (resolver reads POST) |
| a3 | `jury/round-applications-overall-ratings` | ratings across jurors | jury role :9 | yes |
| a4 | `jury/review-applications-ratings` GET + POST `approveRating :19`, `approveRatingBulk :51`, `mark_not_interested :85`, `editRating :142`, `setFiltersInSession :167` | reviewer view | jury role :177 | **reviewers exempt** (D-Reviewers) |
| a5 | `jury/dashboard` POST `getOverallProgramRoundRatings :25` | per-round aggregates | jury role :6 | yes; dashboard GET stays allowed (cards, BRL-04) |
| a6 | `round-startups`, `round-individuals`, `round-mentors`, `programs`, `startups`, `review-startups/individuals-ratings`, `round-startups-overall-ratings` | legacy / mentor / VS rounds on other tables | jury role | **out of scope** (D-Scope) |
| b1 | `application-submission-detail/{id}` incl. `download_pdf :288`, `download_grant_letter :470`, `get_attachment_urls :894`, `download_attachments :937` | full application + attachments | `checkLoggedIn()` only (:2) | yes via submission-id resolver / default-deny; `[INFERRED — requires validation]` that a jury session returns 200 today — verify manually |
| b2 | `application_management/form-submission-detail/{id}`, `timeline.php`, `reports.php`, `round-applications-question-answers.php`, `submission-application-management(.tableview).php` | applications, answers, exports | `checkLoggedIn()` + PM/partner scoping | same as b1 |
| b3 | `form_builder/*`, `modules/table.php` | generic | jury already redirected | keep |

**Residual gaps a request-time gate cannot close (must be stated in issues):**
1. Pre-issued S3 presigned URLs live up to **7 days** (`core_functions.php:3388-3391`); mitigation: jury-context presigns ≤15 min per call site; residual window remains.
2. Image attachments are public ImageKit CDN URLs (`generateS3FileUrl`, used in `form-submission-detail.php:36`).
3. Power Pitch video URLs are external.
4. `modules/aws/ajax` / `acl_update` are reachable without login and can set `public-read`/delete keys (`aws/module.spec.md:63-79,158-164`) — pre-existing; out of scope to fix here but **must be filed** (follow-up a).
5. Developer-role tools (`ajax/crud_actions` `sql_query`, `table_management delete_record`) can write any table; defeats FR-A17 for developers (D-Immut).
6. Legacy/mentor/VS jury rounds carry no NDA (D-Scope).

## Contracts & invariants

- **Flags:** none (D-Flag). Per-round default-Off means non-users see zero change; precedent `freeze_applications` is flag-independent (`application_management/module.spec.md:531-537`). If product later wants a tenant switch: `jury_nda_enabled` (`tenant_users` column in tenants → backend `Feature` enum → admin `config.php` with `?? "0"`), and `/trace-flag` becomes a blocking gate (the tenants repo is present but would then need the entity column + migration).
- **API:** the 3 backend routes in frontmatter; additive only; consumers = `sc-saas-admin` cURL; frontend none. `/audit-contract` required.
- **Invariants at risk:** #2 API contract (additive); #4 Auth — new juror gate and reuse of the `:adminMd5` boundary, must fail closed; #5 Tenant scoping — NDA records + signed PDFs are tenant data (per-tenant DB, private bucket prefix), `/check-isolation` required on new queries and S3 key construction. #1 flags, #3 tenant-verification shape, #6 PowerPitch: untouched.

## Cross-Repo Contract Impact

| Item | Owner | Consumers affected | Gate |
|---|---|---|---|
| NEW `…/jury-nda-signed-copy-email/:adminMd5` + DTO | backend | `sc-saas-admin` (new `sendJuryNdaSignedCopyEmail()` in `includes/jury_nda_functions.php`, shape of `sendAllotmentEmailToJury`, `edit_program_round.php:25-39`); frontend none | `/audit-contract` |
| NEW `…/jury-nda-notification-email/:adminMd5` + DTO | backend | `sc-saas-admin`; frontend none | `/audit-contract` |
| CHANGED `…/jury-startup-allotment-email/:adminMd5` (optional `ndaRequirement`, `ndaNote`) | backend | existing callers `edit_program_round.php:28`, `edit_program_round2.php:28`, `application_management/edit_program_round.php:28` omit the fields → unchanged output | `/audit-contract` |
| Schema: 3 cols + 2 tables + 1 col | backend (`synchronize:true`) | `sc-saas-admin` reads/writes directly; never rename after release (`core/zenxai/module.spec.md:84`) | `/check-isolation`; deploy order |
| `spa_admin_logs` rows `module='jury_nda'` | admin | `system_logs/list.php` displays them | none |
| `/trace-flag` | — | not applicable (no flag) | — |
| Frontend `core/service/*`, `brand.model.ts` | — | none | — |
| 3rdparty gateway `POST email/ses/send-email` | gateway | **No change needed (verified).** `SESService.sendEmail` (`sc-saas-3rdparty-webservices/src/modules/ses/ses.service.ts:56-58`) spreads the DTO straight into nodemailer `transport.sendMail({...emailData})`; `attachments` is an untyped passthrough (`ses/dto/ses-email-data.dto.ts:62-64`, documented in `ses/module.spec.md:44`). nodemailer fetches `{path: <https URL>, filename}` attachments itself — the same shape the backend already uses for invoice PDFs (`ses-email.service.ts:7370-7375`). The presigned URL must stay valid until the gateway fetches it (TTL ≥ 15 min for this send, not the 5 min used for browser downloads) | — |

## Test plan

**Automated test-first coverage is BLOCKED workspace-wide** (the "guardian" skill doesn't exist — workspace CLAUDE.md, Standing process step 6). Substitute verification is stated explicitly in each Linear issue/PR: "automated test-first coverage was not added".
- backend: `npm run build`, `npm run lint`, `npm test`; after-the-fact jest for status derivation + validity floor and for the retry cron / email service. Manual: each new route with valid/invalid `:adminMd5`, mismatching `acceptanceId`/email, simulated gateway failure; inspect the `ses_email_queue` row (`email_type='jury_nda'`).
- admin: no test suite or CI exists. `php -l` on every file; CLI harness for `juryNdaState` over the status × requirement × floor matrix and for `juryNdaBuildSignedPdf` (original bytes unchanged, SHA-256 matches, < 10 s). **Manual BRL-03 matrix with a real jury-role session** on Mandatory, before and after signing: request every route in a1–a5, b1, b2 plus POST handlers, assert 403/redirect and no `forms_submissions` query; repeat for Optional, NDA-off, a juror not allotted to the round, columns absent (backend not deployed), and a forced query failure (must fail closed).
- cross-repo staging smoke: backend first, then admin; admin uploads NDA → juror signs → PDF in private bucket → email with attachment → `delivery_timestamp` back-filled → tracker shows Signed + delivered → Replace(No) keeps validity / Replace(Yes) flips to Re-sign required → ZIP/CSV → program delete, round delete, `delete_record` refuse NDA rows. `/audit-contract`, `/check-isolation`, `/cross-repo-review` before `in-review`.

## Rollout

1. **Backend first** (additive): columns/tables via `synchronize:true` (nullable/defaulted, no backfill), routes (unused until admin ships), enum/template seeds, cron row. Old admin builds ignore everything.
2. **Admin second**, tolerant of an undeployed backend (existence probe → NDA unavailable, toggle hidden with a note). Default Off everywhere.
3. **Infra before the first real signature (blocking, not code):** private NDA bucket with SSE + delete-deny/Object Lock in an India region; `qpdf` on admin hosts; PHP `upload_max_filesize`/`post_max_size` ≥ 10 MB; legal sign-off on click-wrap wording.
4. No flag to flip. Pilot: one tenant, one Optional round, then one Mandatory round. Measure the per-request gate lookup.

## Linear breakdown (created 2026-10-01)

Project **Enhancement** (P-SAN-48), milestone **Jury NDA Signing**; every task assigned to Sandeep (single owner for the whole feature), status Backlog. One repo per task. Two parent tasks, 24 subtasks (no task spans repos). Severity = Linear priority; repo badge = `Repo: *` label.

| Parent | Repo | Priority | Subtasks (build order) |
|---|---|---|---|
| **SAN-1488** Backend — schema, email endpoints, retry cron | sc-saas-backend | 2 High | SAN-1357 NDA columns on `application_program_rounds` + `can_view_jury_ndas` · SAN-1358 `jury-nda` module (versions, acceptances) · SAN-1359 `JURY_NDA` email type + 4 templates · SAN-1360 footer-less send (blocked on decision) · SAN-1361 signed-copy email endpoint · SAN-1362 notification email endpoint · SAN-1363 additive allotment-email fields · SAN-1364 retry cron |
| **SAN-1489** Admin — gate, juror signing, round config, tracker, retention | sc-saas-admin | 1 Urgent | Foundation: SAN-1365 status/audit/probe helper · SAN-1366 BRL-03 gate (Urgent) · SAN-1367 allotment check. Config: SAN-1368 round settings · SAN-1369 file card/replace/versions · SAN-1370 mid-round warnings. Juror: SAN-1371 NDA modal · SAN-1372 signed PDF build · SAN-1373 badges/banner/My NDA/re-sign. Governance: SAN-1374 tracker · SAN-1375 ZIP+CSV · SAN-1376 reminder dialog · SAN-1377 permission · SAN-1378 delete protection · SAN-1379 retention · SAN-1380 derived alerts |

Superseded and cancelled: SAN-1351 / SAN-1352 (original two large issues). Deploy order: SAN-1488 before SAN-1489.

Follow-ups **not yet filed** (one repo each, per the one-repo-per-issue guardrail): (a) Admin — fix unauthenticated `modules/aws/ajax` / `acl_update` and public-read ACL (Urgent, security); (b) Admin — close jury-role access to `application-submission-detail` and other `checkLoggedIn()`-only data pages if confirmed reachable (Urgent); (c) Admin — extend NDA to legacy/mentor/VS jury rounds (future, D-Scope); (d) Round clone support for FR-A9 (future, D-Clone). The former conditional 3rdparty issue is dropped — gateway verified.

## Delivery process (the standing 10-step loop)

Per workspace CLAUDE.md "Standing process" and the Developer Guide. Gates are held by Sandeep; steps run only on his typed command. Current position marked.

| Step | What | Status |
|---|---|---|
| 1 | Orient on the Linear issue | done (SAN-1488 / SAN-1489 parents) |
| 2 | `/from-linear` — recommend full loop (not `/bug-fix`: two repos, new tables, gate) | done; full loop chosen |
| 3 | Governing spec drafted with file:line evidence; Linear tasks created | **done (this file + Linear breakdown)** |
| 4 | Resolve open design questions; never invent an answer; record `[CONFIRMED — role, date]`; flip to `approved` only on Sandeep's word | **Done 2026-10-01** — approved; footer, DPDP and owner sign-off confirmed; only legal sign-off remains (release gate) |
| 5 | Contract checks: `/audit-contract` (3 backend routes), `/check-isolation` (every new query + S3 key construction), `/trace-flag` not applicable (no flag) | not run |
| 6 | Tests first — blocked (no guardian skill). Substitute and say so: backend `npx tsc --noEmit`, `npm run lint`, `npm run build`, `npm test`; admin (PHP, no suite/CI) `php -l` + CLI harness + manual BRL-03 repro. Node commands do not apply to admin | not started |
| 7 | Branch — skipped; work directly on `ai_native_setup` (standing override, 2026-07-30) | n/a |
| 8 | `/spec-implement` in dependency order backend → admin; Linear Todo → In Progress → In Review → Done as work happens | not started |
| 9 | Verify with real command output (including failures); update module specs + Gap Register + Linear states | not started |
| 10 | Commit and push to `ai_native_setup` only when Sandeep confirms; close the Linear issues | not started |

New module specs to write during step 9: `sc-saas-backend/src/modules/jury-nda/module.spec.md`, plus updates to `sc-saas-admin/modules/jury/module.spec.md` and `application_management/module.spec.md`, and both repos' module-spec indexes.

## Out of scope

Aadhaar eSign/DSC, countersignature, multi-language NDA, org-level NDA template library, merge fields, NDAs for mentors/reviewers/observers, auto re-allotment, juror-facing client role (BRD §4/§18). In this spec: NDA on legacy/mentor/VS jury rounds (D-Scope); a global audit viewer (no wireframe); fixing `aws/ajax`, the 7-day presign default for non-jury callers and `getIP()` spoofability repo-wide (filed as follow-ups); any `sc-saas-frontend` / `tenants` / `ai-startups-analyzer` change.

## Open questions (approval given 2026-10-01)

Three of the original four are now answered (see D-Footer, D-DPDP, D-Signoff). What remains:

1. **Legal sign-off** on click-wrap acceptance under the IT Act 2000 and on the NDA wording (BRD §7/§16). Blocks the production release only.
2. **Legal confirmation of D-DPDP** (retain signed NDAs through the retention period even when a juror requests erasure). Blocks SAN-1379's delete action only; the build proceeds on the confirmed 'retain' decision.

Business sign-off was relayed by Sandeep, not attached; attach or reference the signed BRD §20 page when available.

## Changes after approval (2026-10-07, Sandeep) — signed-copy email

- **Download link instead of attachment.** The signed-copy email (`jury-nda-signed-copy`) no longer attaches the PDF. It shows a "Signed Copy" row with a green Download button in the details table (shortcode `download_url`). The link is a private-bucket presigned GET valid for 7 days (S3 maximum) with `Content-Disposition: attachment; filename="Signed_NDA_...pdf"`; a retry signs a fresh link. This supersedes the Endpoint 1 wording above ("`attachments:[{path,filename}]`", presigned TTL of at least 15 minutes) and the 30-minute gateway link. Trade-off accepted: the link works without login until it expires (the juror can always download from My NDA).
- **Unsubscribe footer on all four emails.** The signed copy used to opt out of the standard unsubscribe footer (`skipUnsubscribeFooter`, decision of 2026-10-01 / SAN-1360). Since 2026-10-07 none of the four Jury NDA emails opts out.
- **Decline alert recipients** now always include every Super Admin of the tenant (SAN-1770), see `specs/bug-fixes/SAN-1770-jury-nda-decline-email-super-admin.md`.
- **Tenant switch** `jury_nda_enabled` gates the whole feature (FA-012).
- Verification of the email change: backend `npx tsc --noEmit` clean and the related jest suites pass (ses-email service, signed-copy service, admin-actions signed-copy, upload service); no real e-mail was sent yet. No automated test coverage was added to sc-saas-admin.


## Changes after approval, 2026-10-09 (Sandeep) — tracker and Replace follow-ups

- **Program Managers see the tracker (SAN-1836).** The tracker (status column, tiles, drawer, copies, exports, reminders) is open to Super Admin, Developer, roles with `can_view_jury_ndas` AND every Program Manager / Corporate Program Manager login, limited by `juryNdaManageScope` to their own programmes (PM must be in `program_managers`, corporate PM to their business challenges, partner to its partner). Record: `specs/bug-fixes/SAN-1836-program-manager-jury-nda-tracker.md`.
- **Tracker UI (SAN-1837, SAN-1838).** Action bar on one row with the status message below; the evidence drawer has View / Download once, at the top; only the newest signed copy is reachable from it.
- **Replace with re-sign (SAN-1839).** The admin is told how many jurors were e-mailed or why none were; the admin retries 502 / 503 / refused connections up to 3 times; the backend notification route sends recipients in parallel groups of 5. Not confirmed yet: the cause of the reported `http_502`. Record: `specs/bug-fixes/SAN-1839-replace-nda-resign-email.md`.
