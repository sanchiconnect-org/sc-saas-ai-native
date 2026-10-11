---
id: FA-011                      # next free FA- id (FA-010 = Jury NDA). Linear: Enhancement project (P-SAN-48), milestone "Limit Jury Access"; parents SAN-1676..SAN-1683.
title: Limit Jury Access — round-level hiding of application-form questions from jurors
type: feature
status: approved                # [CONFIRMED — Nirmal, 2026-10-06] "ok now create the project + tasks" — OQ-1..OQ-4 answered same day
linear: https://linear.app/sanchiconnect/project/enhancement-7825a8dad14b   # milestone "Limit Jury Access"
owner: nirmal.s@sanchiconnect.com   # spec owner; all Linear work assigned to Sandeep (sandeep.k@sanchiconnect.com)
repos: [tenants, backend, frontend, admin]   # dependency order. frontend = one-line IFeatures type addition only (invariant #1). 3rdparty / ai-startups-analyzer / tenants-admin code untouched.
contracts:
  api: []                       # no backend route added/changed — admin reads/writes via Medoo (same as every round toggle). See "Contracts & invariants > API".
  flags: [limit_jury_access_enabled]   # OQ-1 decided 2026-10-06: tenant-level flag, default off
  events: []
  # Schema (backend owns it, synchronize:true): 1 new table + 3 new nullable columns on application_program_rounds. Tenants schema: 1 new boolean column on tenant_users.
tenant_scoped: true
depends_on: [FA-010]            # reuses FA-010's admin scope helper, audit wrapper and schema-probe pattern (already shipped: sc-saas-admin includes/jury_nda_functions.php, backend src/modules/jury-nda/)
created: 2026-10-06
---

# FA-011 — Limit Jury Access

## Source & evidence status

- **Requirements source:** *BRD — Limit Jury Access v0.3*, 5 Oct 2026, business owner Dr. Sunil Shekhawat (16 pp incl. wireframes W1–W6; decisions D1–D5 resolved). Supplied in chat 2026-10-06. BRD ids (FR-, BR-, NFR-, US-, D1–D5, W1–W6) are cited as written.
- **Code evidence:** three read-only sweeps of `sc-saas-admin` + `sc-saas-backend` on 2026-10-06 (form data model, juror data surfaces, round settings/Kanban/rubric), key claims spot-checked by hand. Paths below are relative to each repo root. `ADMIN` = `sc-saas-admin`, `BE` = `sc-saas-backend/src`.
- **Tag legend** (specs/spec-authoring-practices.md Practice 3): unmarked + `file:line` = evidenced; `[INFERRED — requires validation]`; `[DESIGN DECISION PENDING]`; `[DECIDED — recommended default]` = taken on a recommended default, owner may override.

## Roles — no new role is introduced

"Juror" in this spec (and in the BRD) means **an existing admin user who has the existing jury role** (`spa_admin_roles.code = jury_role_id`, `config/config.php:225-252`), logging into the existing jury portal (`modules/jury/*`). This feature adds **no new role, no new role permission column and no new user type**. Every BRD role maps to something that already exists:

| BRD role | Existing role in code | What this feature does for it |
|---|---|---|
| Jury / Evaluator | jury role (`jury_role_id`) | sees the restricted application view |
| Jury reviewer (not named in BRD) | the **same jury role**, with the existing per-user flag `spa_admin_users.is_jury_reviewer = 1` (`checkIfJuryisReviewer()`, `core_functions.php:4714-4728`) — not a separate role | sees the same restricted view (D-Reviewers) |
| Program Manager | `program_manager_role_id` / `corporate_program_manager_role_id`, listed in the programme's `program_managers` | configures Limit Access |
| Program Admin | any other existing non-jury admin role passing the existing programme scope check (`juryNdaManageScope()`) | configures Limit Access, exports activity |
| Partner (incubator admin) | existing partner login, own `partner_id` only | configures Limit Access on own programmes |
| Super Admin | `super_admin_role_id` | full access |

The only role checks used are: "is this session the jury role?" (restrict / deny) and the existing scope helper (who may configure). Nothing is added to `spa_admin_roles`, `spa_admin_users` or `config.php` roles.

## Problem

Every question on a programme's application form (and every round form) is shown to every allotted juror. Sensitive answers — financials, cap table, KYC (PAN/Aadhaar), bank details, named customers — reach external evaluators. The BRD asks for a per-round, server-enforced "hidden from jury" set of questions, configured from Round Settings → Jury Allotment, audited, and editable until evaluation closes (BRD §2, §5).

### What the code actually looks like (drives the design)

1. **The juror experience is PHP admin, not the SPA/backend.** Jurors are `spa_admin_users` with the jury role and use `ADMIN/modules/jury/*`; there are **no juror-facing backend endpoints** (only `:adminMd5` email routes, `BE/modules/admin-actions/admin-actions.controller.ts:961,985,1012`). Same finding as FA-010. → The BRD's `GET/PUT /rounds/{id}/visibility` API (§12) is implemented as admin Medoo handlers, not backend routes.
2. **Questions are JSON, keyed by a stable random key.** `forms.fields` is an array of sections `{key:"section_XXXXXXXXXX", name, type:"form_section", multi_value, visiblity, fields:[<JSON-string of field>]}`; each field has `key:"field_"+10 random chars` (`ADMIN/themes/default/html/form-management/edit-form.php:2779-2786,3214,3345`). Keys are **reused on every edit/re-order** and only generated when missing (`:3360-3362`). → `(form_id, field_key)` is a usable stable question id (BRD Assumption 1 holds, with caveats in Edge cases).
3. **A juror sees more than one form.** `round-applications.php:800-811` loads the submission's main form **plus every active round form of the programme** (not only the current round's). Round forms are separate `forms` rows (`application_program_rounds.form_id`, `BE/modules/application-management/entities/application-program-rounds.entity.ts:137-138`; created by `createRoundForm`, `ADMIN/modules/application_management/edit_program_round.php:1585-1620`). Round-form answers are separate `forms_submissions` rows looked up by `(form_id, email)` (`round-applications.php:825-828`).
4. **Answers** are `forms_submissions.data` JSON keyed by `field_key`; multi-value sections store `section_key → [ {field_key: value} ]`. Uploaded files are S3 keys **inside** the answer (no file table) (`form-field.component.ts:417-428`, upload key `BE/core/upload-module/upload.service.ts:70-89`).
5. **URLs are minted for every answer before the template runs.** `formatFormSubmissionsData()` (`ADMIN/includes/custom_form_functions.php:397`) creates a **7-day** presigned URL for each `file_upload` (`formatFileFields` :41-75 → `generateS3SignedUrl`, `core_functions.php:3381-3391`) and a **public, non-expiring ImageKit URL** for each `image_upload`/`video_upload` (`formatImageFields` :317, `formatVideoFields` :340 → `generateS3FileUrl` :3367). → The filter **must run before** `formatFormSubmissionsData` (`round-applications.php:839`), not in the template.
6. **Conditional logic exists, one level.** Fields and sections carry `visiblity:{show, field:<parent key>, condition:"is"|"is_not", value}` (`edit-form.php` template :1700-1730, :1915-1945). The juror template evaluates these against other answers (`themes/default/html/jury/round-applications.php:355-384, 432-433`). Child→parent only; no reverse index.
7. **There is no rubric-criterion ↔ question link.** `application_program_submission_rating_criterias` = id, name, description, weightage, is_active, program_id, program_round_id (`BE/.../application-program-submission-ratings-types.entity.ts:3-25`); jury questions (`application-programs-jury-questions.entity.ts:8-45`) likewise have no form/field reference. → BR-03 / US-04 warning has nothing to evaluate (see D-Rubric).
8. **There is no round-level "evaluation closed" state.** `application_program_rounds` has no end date / closed flag / status beyond soft-delete `status`/`deleted_at` (full column list: entity :14-177). Nearest: round `freeze_applications` (blocks moving/rejecting), `editable_jury_ratings`, and programme-level `program_closed` (`application-programs.entity.ts:79-94`, makes the Kanban read-only, theme `submission-application-management.php:1652-1656`). → BR-08 resolved by D-Closed.
9. **Jurors can reach full application data outside the jury module today.** `ADMIN/modules/application-submission-detail.php:2` only calls `checkLoggedIn()` (verified) — it exposes `download_pdf :288`, `get_attachment_urls :894`, `download_attachments :937`, AI `download_screening :1123` / `download_prior_art :1129`, transcripts `:30,:102`, all via `collectSubmissionExportData()` (`includes/submission_export_helpers.php:10-160`) which exports **every** field. `application_management/form-submission-detail.php:2` and `submission-application-management.php` exports (`download_program_data(_xlsx) :1628`, `download_bulk_pdf :2179`) have no jury block either; `analysis_form.php` (`generateThesisDraft` → analyzer `:137`) only `checkLoggedIn()`. Already recorded as F1 in FA-010's `nda-gate-repro-matrix.md:78-83`. `[INFERRED — requires validation]` that a jury session actually gets HTTP 200 (code has no block; not run). → Filtering only the jury page would leave FR-09/FR-10 unmet. See D-Block / OQ-4.
10. **Existing precedent to copy:** programme documents already have a per-round `is_jury_can_view` filter in the jury view (`round-applications.php:1038,1046`; set in `edit_program_round.php:1823`). FA-010 provides a fail-closed scope check `juryNdaManageScope()` (`includes/jury_nda_functions.php:935-1000`), an audit wrapper `juryNdaAudit()` (:2729-2752) and a schema probe `juryNdaSchemaReady()` (used `edit_program_round.php:2687`).

## Decisions taken on recommended defaults

| # | Decision | Basis |
|---|---|---|
| D-Store | Hidden set stored as rows `(round_id, form_id, field_key)` in a new table; section-level selection in the UI just selects all its field keys (sections are not stored). | stable keys (finding 2); one row per hidden question gives clean audit diffs and indexes |
| D-List | The pop-up lists **every form the juror sees for that round**: the programme's main form, then each active round form (in round `id` order), each grouped by its sections — i.e. exactly the set loaded at `round-applications.php:800-811`. Fields of type with `invisible:"1"` are still listed. | FR-02 "every question"; finding 3. Listing only the main form would leave round-form answers unhideable. |
| D-Scope | One hidden set per **application-management round** (`application_program_rounds`). Legacy `program_rounds`, mentor, individuals and venture-studio jury pages (`round-startups.php`, `round-individuals.php`, `round-mentors.php`, `startups.php`) are out of scope. | Same scoping as FA-010 D-Scope; BRD is about the CFA Kanban |
| D-Which | A juror opening an application in round R gets round R's hidden set applied to **all** forms rendered (main + all round forms). | BRD "round-level configuration" (§5) |
| D-Child | BR-05 is computed **at read time**: any field or section whose `visiblity.field` is a hidden key (transitively) is also hidden. Children are not auto-ticked in the pop-up; the pop-up shows them as "also hidden (depends on Qn)". | no reverse index exists (finding 6); read-time closure stays correct after form edits |
| D-Section | A section whose every visible field is hidden is dropped, heading included (W5 note 2). Multi-value sections: hidden sub-field keys are removed from every row. | W5; finding 4 |
| D-Rubric | **BR-03 / US-04 warning and the "Used in scoring" tag are deferred** — no rubric↔question link exists (finding 7). BRD Assumption 3 explicitly allows this ("if not, the warning is deferred"). BR-02 (cannot hide everything) **is** in scope. | BRD §14 Assumption 3 |
| D-NoAPI | No backend endpoint. Config load/save, copy-from-round, activity log and preview are admin POST handlers on `edit_program_round.php` (`submitAction=jury_visibility_*`), like every other round setting. Backend only owns the schema. | finding 1; FA-010 precedent |
| D-Prev | "Copy from previous round" (FR-13) = the same programme's round with the greatest `id` lower than the current one, `status=1`, `deleted_at IS NULL`. Only keys whose form/field still exists are copied. | `priority` exists but is never written (`submission-application-management.php:298-306`); effective order is `id` |
| D-Unreviewed | "N new questions not reviewed" (W1 state 3): on save store a snapshot of all listed field keys on the round; unreviewed = current keys − snapshot, shown only when the hidden set is non-empty. Opening and saving the pop-up refreshes the snapshot. | BRD §9 edge case |
| D-Audit | `spa_admin_logs` via a wrapper `juryVisibilityAudit()` modelled on `juryNdaAudit()`; `module='jury_visibility'`, actions `visibility_saved`, `visibility_copied`, `visibility_activity_exported`; `data` = `{round_id, hidden_added:[{form_id,field_key,label}], hidden_removed:[…], hidden_total, ip, remote_addr, user_agent}`. `createAdminLogs` stores no IP itself (`core_functions.php:6517-6543`) so IP goes in `data`. Application-level immutability only (same as FA-010 D-Immut). | NFR-04; FA-010 D-Immut |
| D-Perm | Config & activity endpoints: `checkLoggedIn()` + not jury role + `verifyCSRFToken()` + `juryNdaManageScope()` (partner on own `partner_id`, PM only if in `program_managers`, corporate PM by `corporate_id`, jury denied). Activity **export** (NFR-04): Super Admin, or a programme-scoped admin passing the same scope check. No new role and no new role permission column — existing roles only (see "Roles"). | BR-01, NFR-03; reuse of shipped fail-closed helper |
| D-Fail | NFR-07: if the hidden-set query returns `false` (Medoo error) on a round whose table exists → jury page shows an error, **no answers rendered**. If the table does not exist yet (admin deployed before backend) → feature treated as unavailable: config button hidden, jury view unchanged (nothing can be hidden). | NFR-07; FA-010 D-Gate pattern |
| D-TTL | In jury context only, `file_upload` presigned URLs drop from 7 days to **15 minutes**. Image/video public ImageKit URLs are **not** changed in R1 (residual, see Risks). | NFR-02 hardening; changing ImageKit delivery is a larger change |
| D-Pitch | Pitch deck (`forms_submissions.pitch_document`) and Power Pitch video (`power_pitch_url`, per form) are **not form questions**. They are added to the pop-up as two fixed "system" rows in a top "Attachments" group, stored with `form_id = 0` and `field_key = '__pitch_deck'` / `'__power_pitch_video'`. Programme documents keep their existing per-round `is_jury_can_view` control (not duplicated). | W3 shows "Pitch deck" as a hideable row; finding 10 |
| D-Toast/Copy | UI copy as BRD §10 / W2–W6, adapted to the Bootstrap 4 + jQuery theme (not pixel-matched), same as FA-010 D-UI. | |
| D-Export/AI | **No juror export, print view or AI summary exists in the jury module today** (verified by grep). FR-10/FR-08 are therefore met for jury pages by construction, **provided** the jury role is blocked from the non-jury pages in finding 9 (D-Block). Any future juror export/AI must call `juryApplyHiddenFields()`; stated in the module spec. | finding 9 |
| D-Flag | Tenant flag `limit_jury_access_enabled` (default off) gates the **config UI** (button, pop-up, badges, activity, handlers). The **juror-side filter applies whenever hidden rows exist, regardless of the flag** — switching the flag off must never re-expose questions that were hidden. `[CONFIRMED — Nirmal, 2026-10-06, OQ-1]` | BRD §15 |
| D-Closed | BR-08 "evaluation closed" = programme `program_closed = 1` (`application-programs.entity.ts:79-94`). No new round-level close concept in R1. `[CONFIRMED — Nirmal, 2026-10-06, OQ-2]` | already makes the Kanban read-only |
| D-Reviewers | Jury users flagged as reviewers (existing `is_jury_reviewer = 1`, same jury role — not a separate role) get the **same restricted view** as other jury users, incl. the `previewOnly` iframe. (Differs from FA-010, which exempted reviewers from the NDA.) `[CONFIRMED — Nirmal, 2026-10-06, OQ-3]` | they are jury-role users |
| D-Block | Close the finding-9 leak by **blocking the jury role** (incl. reviewers) on `application-submission-detail.php`, `application_management/form-submission-detail.php`, `submission-application-management(.tableview).php` and `analysis_form.php` (redirect GET, 403 JSON on POST), rather than filtering their exports. Admin/PM exports stay complete (BRD §9 "Bulk export by admin: unaffected"). Ships **first, as its own Urgent issue**, independent of the flag. `[CONFIRMED — Nirmal, 2026-10-06, OQ-4]` | jurors have no legitimate use of these pages |

## Prior art (reused vs new)

| Need | Existing | Decision |
|---|---|---|
| Round record | `application_program_rounds` (entity :14-177) | **EXTEND**: 3 columns |
| Hidden-question store | none; precedent `application_program_report_charts.field_key` (`application-program_report_charts.entity.ts:11`) references form fields by key | **NEW** table |
| Jury answer rendering | `round-applications.php:799-849` → template :337-448 | **EXTEND**: filter before :839 |
| Per-round jury visibility of documents | `is_jury_can_view` (`round-applications.php:1038,1046`) | keep; model for the new filter |
| Scope / CSRF / audit / schema probe | FA-010 helpers in `includes/jury_nda_functions.php` | **REUSE** |
| Modal with checkbox list | `#juryNdaReminderModal` (theme `edit_program_round.php:767`), tri-state select-all `analysis_result.php:1111-1215`, `#manageChartsModal` keyed by `data-field-key` (`reports.php:521-560`) | **REUSE patterns** |
| Kanban round header | `fetchProgramData()` (`includes/application_program_management_funcs.php:23-117`) → `build_titles()` (`themes/default/assets/libs/kanban/js/kanban-applications.js:42-109`, header at :106) | **EXTEND**: `jury_hidden_count`, `jury_unreviewed_count` |
| Tableview round tabs | `submission-application-management-tableview.php` theme :484-491 | **EXTEND**: badge |
| Form parsing | `getFormDetails()` (`custom_form_functions.php:550-672`) | **REUSE** for pop-up list and filter |

## Acceptance criteria

**Configuration (Round Settings → Jury allotment) — W2, W3, W4**
- [ ] AC-1 (FR-01, BR-01, W2) "Limit Access" button with lock icon in the "Jury members for this round" card header; label "Limit Access (N hidden)" when N>0. Not rendered for jury sessions; config handlers return 403 JSON to jury / out-of-scope users (NFR-03).
- [ ] AC-2 (FR-07, W2) Helper line "Hidden questions apply to all N jurors in this round, including jurors added later." under the button when N>0.
- [ ] AC-3 (FR-02, D-List, W3) Modal "Limit jury access — Round: <round name>" + help text; lists the Attachments group (D-Pitch) then each form (main form first, then round forms) → sections → fields in form order; each row: checkbox, Q-number (running per pop-up), label (truncated, full text in `title`), answer type, file icon for `file_upload`/`image_upload`/`video_upload`.
- [ ] AC-4 (FR-03, FR-04, W3) Multi-select; keyword search filters rows as typed; Select all / Clear all act on rows currently shown by the search; section checkbox tri-state (indeterminate when partially hidden).
- [ ] AC-5 (FR-05) Live counter "X of Y questions hidden from jury" (Y = listed rows incl. system rows).
- [ ] AC-6 (FR-06, W4c) Save disabled until a change; Cancel discards. Save replaces the round's hidden set atomically (transaction), writes one audit row (D-Audit), refreshes the unreviewed snapshot, and shows toast "Access updated. N questions hidden from jurors in <round>." with "View activity" link.
- [ ] AC-7 (BR-02, W4b) If every listed question is ticked: inline error "At least one question must stay visible to jurors. Untick one or more questions to save."; Save disabled; server rejects the same case.
- [ ] AC-8 (D-Child) Rows whose visibility depends on a ticked row show "Also hidden — depends on Qn" and are counted in the juror-side effect (not in the ticked count).
- [ ] AC-9 (FR-13, D-Prev) "Copy from previous round" pre-ticks the previous round's keys that still exist; disabled with tooltip when there is no previous round; nothing saved until Save.
- [ ] AC-10 (BR-07) A new round, and every existing round at deploy, has nothing hidden.
- [ ] AC-11 (BR-03 deferred, D-Rubric) No "Used in scoring" tag / warning in R1 — documented in the module spec as a known gap.

**Juror view — W5**
- [ ] AC-12 (FR-08, D-Which, D-Child, D-Section) For a juror in round R, hidden fields, their dependent children, and fully-hidden sections are **absent** from `round-applications` (main + round forms), including the reviewer `previewOnly` iframe (D-Reviewers). Not greyed out; no placeholder.
- [ ] AC-13 (FR-09, NFR-01, NFR-02) Hidden keys are removed from the answer data **before** `formatFormSubmissionsData()`; no presigned URL, ImageKit URL, file name or answer for a hidden key appears anywhere in the HTML response (incl. HTML comments) or in `$tpl->record['data']` (stripped). Verified by grepping the rendered page for each hidden key's S3 object key and answer value.
- [ ] AC-14 (D-Pitch) When `__pitch_deck` / `__power_pitch_video` is hidden, the pitch-deck block (template :488-526, incl. the commented PDF link :491) / Power Pitch iframe (:471-476) are not rendered and no URL for them is generated.
- [ ] AC-15 (FR-11, W5) When ≥1 question is hidden in round R, one neutral banner "Some application fields have been restricted by the program manager." at the top of the application; no titles or counts.
- [ ] AC-16 (FR-12, BRD §9) Saving a change applies on the juror's next page load; draft ratings and jury-question answers already entered are untouched.
- [ ] AC-17 (BRD §9) Same juror in two rounds: each round's set applies independently.
- [ ] AC-18 (D-Fail, NFR-07) Forced query failure on the hidden-set lookup → error message, zero answers rendered.
- [ ] AC-19 (D-TTL) In jury context, `file_upload` presigned URLs expire in ≤15 min.
- [ ] AC-20 (D-Block, FR-09/FR-10) A jury-role session (juror and reviewer) gets a redirect / 403 on every route in finding 9, including each POST action listed; admin/PM behaviour unchanged.

**Admin visibility — W1, W6**
- [ ] AC-21 (FR-14, W1) Kanban round header and tableview round tab show a lock badge "N hidden from jury" when N>0; amber "N hidden · M new questions not reviewed" when M>0 (D-Unreviewed). Clicking opens Round Settings → Jury allotment with the pop-up open.
- [ ] AC-22 (FR-15, BRD §9) Admin, PM and partner views (application detail, Kanban, exports) always show every answer.
- [ ] AC-23 (FR-16, US-05, W6a) "Activity" view on the Jury allotment tab lists, newest first: date/time (IST), user, Hid/Unhid, questions (labels), sourced from `spa_admin_logs` `module='jury_visibility'` for this round; CSV export (NFR-04) audit-logged.
- [ ] AC-24 (BR-08, US-03, W6b, D-Closed) When the programme is closed (`program_closed = 1`), the pop-up opens read-only (checkboxes disabled, Save removed, banner "Programme closed. Access settings are read-only." — no close date exists to print), and the save handler rejects writes server-side.
- [ ] AC-25 (BRD §9) Deleting a question from the form: its row stays in the table but is ignored (not listed, not counted); the audit trail is unchanged.
- [ ] AC-26 (UI/UX Should) "Preview as juror" opens the first application in the round through the jury rendering path with the **saved** hidden set, read-only (no rating/answer actions). Hidden if the round has no applications.

**Non-functional**
- [ ] AC-27 (NFR-06) Pop-up data for a 200-field form loads < 1.5 s; jury page adds one indexed query (`round_id`).
- [ ] AC-28 (NFR-08) Every new query filters by `round_id` + `program_id` on the per-tenant `$database`; never `$mainDatabase`.
- [ ] AC-29 (BR-06, D3) No applicant-facing change; submitted data never modified.
- [ ] AC-30 (D-Flag) Flag off: no button, badge, pop-up or activity view; config handlers return 403 JSON. Flag switched off after rows exist: jurors still do not see the hidden questions.
- [ ] AC-31 (invariant #1) `limit_jury_access_enabled` present, same snake_case string, in tenants entity + `global.service.ts` field lists, backend `Feature` enum, frontend `IFeatures`, admin `config.php`; `/trace-flag` reports no orphans.

## Data model

Backend owns schema (`synchronize:true`, `BE/core/database/database.module.ts:32`). No FKs (zenxai / FA-010 precedent).

**New table `application_program_round_jury_hidden_fields`** (entity `ApplicationProgramRoundJuryHiddenFieldsEntity` in `BE/modules/application-management/entities/`):
`id` PK · `program_id` int · `round_id` int · `form_id` int (0 for system rows) · `field_key` varchar(64) · `created_by` int (admin user id) · `created_at`.
Unique `(round_id, form_id, field_key)`; index `(round_id)`. Replace-on-save = delete round's rows + insert, in one transaction.

> Departure from the BRD's suggested `round_question_visibility` (§12): no `tenant_id` (one DB per tenant — invariant #5), int ids (not UUID — matches the schema), no `is_hidden_from_jury` boolean (row presence = hidden; the BRD explicitly allows adapting names).

**`application_program_rounds` + 3 nullable columns:**
- `jury_visibility_reviewed_keys` JSON — snapshot of listed keys at last save (D-Unreviewed).
- `jury_visibility_updated_at` datetime, `jury_visibility_updated_by` int — for the button/badge and W6 without scanning logs.

**Audit:** `spa_admin_logs`, `module='jury_visibility'` (D-Audit). The BRD's `visibility_audit_log` table is not created.

## Per-repo plan

Dependency order: tenants → backend → frontend → admin. (The D-Block issue in admin has no dependency and ships first.)

### tenants
- `TenantUsersEntity` boolean column `limit_jury_access_enabled`, default false, after `tripura_certificate_theme_enabled` (`src/modules/tenants/entities/tenant-users.entity.ts:2417`).
- Add it to **all three hand-maintained field lists** in `src/modules/global/global.service.ts` — the select list (beside :339), the response mapping (beside :690-691) and the settings list (beside :937). Precedent: `operational_cost_reimbursement_enabled` at :335, :686-687, :933. A column alone does not reach the API.
- Operators switch it on per tenant from `sanchiconnect-saas-tenants-admin`'s generic edit page over `tenant_users`. `[INFERRED — requires validation]` that the column appears there without a `spa_data_management` metadata row; if not, add the row (data, not code).
- Verify: `npx tsc --noEmit`, `npm run lint`, `npm run build`, `npm test`; call `verify_tenant` on staging and see the field.

### backend
- New entity `ApplicationProgramRoundJuryHiddenFieldsEntity` registered in the application-management module; 3 new columns on `ApplicationProgramRoundsEntity` (beside FA-010's `nda_*` at :153-177). All nullable/defaulted, no backfill.
- Add `LIMIT_JURY_ACCESS_ENABLED = 'limit_jury_access_enabled'` to the `Feature` enum (`core/constants/enum.ts`, beside :1258) for parity — no backend guard needed (backend serves no juror data).
- No routes, DTOs, services. Update `src/modules/application-management/module.spec.md` (owns: new table + columns; consumer: sc-saas-admin via Medoo).
- Verify: `npx tsc --noEmit`, `npm run lint`, `npm run build`, `npm test`; boot against a staging DB copy and confirm `synchronize` adds exactly the new table/columns.

### frontend
- One optional boolean `limit_jury_access_enabled?: boolean` in `IFeatures` (`src/app/core/domain/brand.model.ts`), for invariant #1 parity only. No UI. Verify: `ng build`/lint.

### admin
- **New `includes/jury_visibility_functions.php`** (included beside `jury_nda_functions.php`):
  - `juryVisibilitySchemaReady($db)` — probe (D-Fail).
  - `juryVisibilityListQuestions($db, $programId, $roundId)` — forms per D-List via `getFormDetails()`; returns groups/sections/rows with key, label, type, file flag, `visiblity.field` parent, Q-number.
  - `juryHiddenFieldsForRound($db, $programId, $roundId)` → `[form_id => [field_key,…]]`, `[]` if none, **`false` on error**.
  - `juryHiddenClosure($formD, $hiddenKeys)` — transitive dependants (D-Child).
  - `juryApplyHiddenFields(&$formD, &$data, $hiddenKeys)` — strips from `$formD` sections/`fields`/`main_fields`/`file_fields`/`image_fields`/`video_fields`, drops emptied sections, strips `$data` top-level keys and keys inside every multi-value row.
  - `juryVisibilitySave(...)` — CSRF + `juryNdaManageScope()` + not-closed + BR-02 + transaction + snapshot + `juryVisibilityAudit()`.
  - `juryVisibilityCounts($db, $round)` — hidden + unreviewed counts for Kanban/button.
- **Jury view** `modules/jury/round-applications.php`: after the round/allotment checks, load the hidden set once (fail closed); inside the loop at :818-845 call `juryApplyHiddenFields()` **before** `formatFormSubmissionsData()` (:839); strip `$tpl->record['data']` (:723-727, :869); skip pitch deck (:1096-1106) and Power Pitch (:833-835) when system keys hidden; set `$tpl->juryFieldsRestricted`. Lower `file_upload` presign TTL to 15 min in jury context (pass TTL into `formatFileFields`; default unchanged for admin callers).
- **Jury template** `themes/default/html/jury/round-applications.php`: FR-11 banner at top of the application panel. No other template change needed (it iterates the already-filtered definition, :337-448).
- **Round Settings** `modules/application_management/edit_program_round.php` + theme (jury_allotment block, theme :449+): button + helper line (W2); modal (W3/W4) following `#juryNdaReminderModal`; handlers `submitAction=jury_visibility_load | jury_visibility_save | jury_visibility_copy_previous | jury_visibility_activity | jury_visibility_activity_csv | jury_visibility_preview`. Do **not** copy the legacy toggle handlers (:389-574) — they lack CSRF and scoping.
- **Kanban**: `fetchProgramData()` adds `jury_hidden_count`, `jury_unreviewed_count`; badge in `kanban-applications.js` `build_titles()` (:106) and in the tableview tab (:484-491). The `getProgramRounds` AJAX handler runs before the page's PM/partner scoping (:705 vs :1456-1500) — counts only, no question labels, so no new exposure; noted in Risks.
- **D-Block (OQ-4)**: jury-role (and reviewer) redirect/403 at the top of `application-submission-detail.php`, `application_management/form-submission-detail.php`, `submission-application-management.php`, `submission-application-management-tableview.php`, `application_management/analysis_form.php` — **before** any POST handler.
- **Flag (D-Flag):** `config/config.php` constant `limit_jury_access_enabled` defined from `$getDatabaseSettingsFromMainTable["limit_jury_access_enabled"] ?? "0"` (pattern :119-123); gate button, badges, pop-up, activity and every `jury_visibility_*` handler on it. The jury-side filter is **not** flag-gated.
- **Read-only (D-Closed):** load `application_programs.program_closed` with the round; when `1`, render the pop-up read-only and reject `jury_visibility_save` / `jury_visibility_copy_previous` server-side.
- **Reviewers (D-Reviewers):** apply the filter on the `round-applications` path regardless of `checkIfJuryisReviewer()` (the reviewer exemptions at :32-34 and :706-708 are for allotment, not for this filter).
- Module specs: update `modules/jury/module.spec.md`, `modules/application_management/module.spec.md`; refresh `specs/admin-module-specs-index.md`.
- Mind the jury session-key trap (`admin_roles` plural/singular, `modules/jury/module.spec.md:245-249`) and `// ` comments are forbidden in this repo (use `/* */`, incl. `<script>` blocks).
- Verify: `php -l` on every edited file; CLI harness for `juryApplyHiddenFields()` / `juryHiddenClosure()` over: flat field, file field, multi-value sub-field, conditional child, chained child, fully-hidden section, deleted key, system keys; manual matrix (Test plan).

## Contracts & invariants

- **API:** none added or changed (D-NoAPI). `/audit-contract` not required for routes; run it anyway only if the backend diff touches a controller/DTO (it should not).
- **Flags:** `limit_jury_access_enabled` (D-Flag), owned by tenants → backend `Feature` enum → frontend `IFeatures` → admin `config.php`. `/trace-flag` is a blocking gate before `in-review`.
- **Schema contract:** backend entity ↔ admin Medoo reads/writes; never rename after release.
- **Invariants at risk:** #4 Auth — new admin handlers must check role + scope + CSRF, juror path must fail closed, D-Block closes an existing jury-role leak. #5 Tenant scoping — per-tenant `$database` only; `/check-isolation` on every new query. #1 Flags — new flag, propagated to all four places. #3 Tenant-verification shape — **additive** field in the `verify_tenant` / `tenant-settings` response; existing consumers ignore unknown fields. #2, #6 untouched.

## Cross-Repo Contract Impact

| Item | Owner | Consumers | Gate |
|---|---|---|---|
| New table + 3 round columns | backend (`synchronize:true`) | sc-saas-admin (Medoo) | `/check-isolation`; deploy backend first |
| `spa_admin_logs` `module='jury_visibility'` | admin | `system_logs/list.php` (hard-coded action filter list `:209` — add the new actions) | none |
| Flag `limit_jury_access_enabled` | tenants | backend enum, frontend `IFeatures`, admin `config.php` | `/trace-flag` |
| `verify_tenant` / `tenant-settings` response (+1 field) | tenants | backend bootstrap, frontend `brand.model.ts` (additive) | `/trace-flag` |
| 3rdparty, ai-startups-analyzer | — | none | — |
| tenants-admin | — | none in code; operator toggles the column | — |

## Edge cases (BRD §9 mapped to the code)

- **Form edited after save:** new field keys are visible by default and counted as unreviewed (D-Unreviewed). Label/order edits keep keys.
- **Field duplicated in the form builder:** the copy gets a **new key** (`edit-form.php:3548,3712`) → visible by default, shows as unreviewed. Visibility rules on a copied child still point at the original parent key.
- **Form blob replaced** (`importFieldsFromForm` `modules/form-management/edit-form.php:456-488`, dev `uploadFieldsJson` :510-575, version restore `versions.php:29-76`): keys may change → previously hidden questions become visible. Mitigation: they appear as unreviewed and the badge turns amber; documented in the help text. `[INFERRED — requires validation]` against a real import.
- **Field deleted:** row ignored (AC-25).
- **Hidden mid-evaluation / unhidden:** next load (AC-16).
- **Juror who is also a PM:** not applicable in this codebase — a user has exactly one admin role (`admin_role_id`), so an account is either the jury role or a PM role, never both.
- **Comments / discussion threads:** out of scope (BRD).
- **Admin bulk export:** unaffected (AC-22).

## Risks & residual gaps

1. **Public ImageKit URLs** for `image_upload`/`video_upload` answers never expire (`generateS3FileUrl`). Hiding a question stops *new* issuance; a URL a juror saw before the question was hidden stays valid. Same for the pitch-deck slides. Fix needs private delivery for these objects — follow-up, not R1.
2. **Pre-issued 7-day presigned URLs** (before deploy / before hiding) remain valid until expiry.
3. **Google Docs viewer**: with brand `enable_file_viewer` on, presigned URLs are passed to `docs.google.com/gview` (`themes/default/html/elements/footer.php:452-471`) — third-party receipt of visible files; pre-existing, unchanged.
4. **Jury reviewers bypass allotment** across programmes (`round-applications.php:32-34,706-708`; no partner scoping). Pre-existing; the filter still applies to whatever they open (D-Reviewers). Follow-up issue.
5. **Unscoped AJAX on the Kanban page** (`getProgramRounds` etc. run before PM/partner scoping). Pre-existing; this feature adds counts only.
6. **FA-010 gate resolver mismatch**: `juryNdaResolveRoute` (`jury_nda_functions.php:524-547`) treats the `application-submission-detail/{id}` id as a `forms_submissions` id; it is an `application_program_submission_rounds` row id. Moot for jurors once D-Block ships; file as an FA-010 follow-up.
7. **Free-text leakage**: sensitive data typed into a visible question, or inside the pitch deck, is not redacted (BRD §14 risk, accepted).
8. **Developer SQL tools** can edit the hidden-set table and `spa_admin_logs` (FA-010 D-Immut residual).

## Test plan

**Automated test-first coverage is BLOCKED workspace-wide** (no "guardian" skill; workspace CLAUDE.md step 6). Each Linear issue must state "automated test-first coverage was not added" and use:
- **backend:** `npx tsc --noEmit`, `npm run lint`, `npm run build`, `npm test`; schema diff on a staging copy.
- **admin:** `php -l` on every touched file; CLI harness for `juryApplyHiddenFields()` / `juryHiddenClosure()` (cases listed in Per-repo plan); **manual juror matrix** with real sessions: (a) juror in round R with Q-file, Q-image, Q-multi-value-subfield, Q-parent-of-child, pitch deck hidden → view-source has none of the answers, S3 keys, ImageKit paths, labels; banner shown; (b) juror in round R' (nothing hidden) → unchanged; (c) reviewer via `previewOnly` iframe; (d) forced DB error → fail closed; (e) table absent → feature unavailable, jury view unchanged; (f) D-Block: every route/action in finding 9 as juror and reviewer → redirect/403, as admin/PM → unchanged; (g) config as PM not in `program_managers`, as partner on another partner's programme, without CSRF token → 403; (h) BR-02 server-side; (i) `program_closed=1` → read-only + server rejects; (m) flag off → no config UI + handlers 403, existing hidden rows still enforced; (j) Kanban/tableview badges incl. amber state after adding a field to the form; (k) Copy from previous round; (l) audit rows + CSV.
- **tenants:** `npx tsc --noEmit`, `npm run lint`, `npm run build`, `npm test`; `verify_tenant` shows the field.
- **frontend:** `ng build` + lint.
- **cross-repo:** tenants → backend → frontend → admin on staging; `/trace-flag limit_jury_access_enabled`, `/check-isolation`, `/cross-repo-review` before `in-review`.

## Rollout

0. **D-Block first** — standalone admin security fix, no schema or flag dependency (own Urgent issue). `[CONFIRMED — OQ-4]`
1. **Tenants**: flag column (default off) + field lists. Additive; nobody reads it yet.
2. **Backend**: `Feature` enum + additive schema. Old admin ignores it.
3. **Frontend**: `IFeatures` type only; can ship any time after 1.
4. **Admin**: tolerant of an undeployed backend (D-Fail probe) and of a missing flag column (`?? "0"`). Nothing hidden anywhere at deploy (BR-07).
5. **Pilot**: switch the flag on for one tenant, use it on one live programme round (BRD §15 step 4), then enable for all tenants. Help article / security collateral are business tasks, not code.

## Decisions taken during the build (2026-10-06 to 2026-10-08)

| Decision | What was decided | Where it lives |
|---|---|---|
| D-Flag (confirmed) | Flag off = nothing for everyone. A developer-admin bypass was added on 2026-10-06 and **removed on 2026-10-08**, so AC-30 holds for developers too. The grey developer note ("why is the button hidden") is shown only when the flag is ON. | `limitJuryAccessEnabled()` in `sc-saas-admin/includes/jury_visibility_functions.php` |
| D-Attach | The pop-up lists form questions from the programme form and the round form (inactive forms marked "(not active yet)"). The attachments group "Pitch deck and video" lists the pitch deck only when the programme toggle "Enable Pitch Deck field" is on, and the Power Pitch video only when "Enable Video Pitch" is on. Jurors follow the same toggles. | `juryVisibilityListQuestions()`, `juryBuildFormsForSubmission()` |
| D-SamePage | The Limit Access button always opens the pop-up on the same page, also inside the Edit Round modal (a new-tab variant was tried and reverted). The Kanban / tableview badge still opens Round Settings in a new tab with `?open=limit_access`. | theme `application_management/edit_program_round.php` |
| D-Modal-UX | Static backdrop; the project's standard loader (`#loaderOverlay`) on load, copy and save; while saving the pop-up cannot be closed; inside the Edit Round modal the parent header and the strip under the frame are dimmed. Activity shows a table with Hidden / Unhidden / No change badges. | same theme file; see the module spec |

UAT: Linear SAN-1813 with 11 end-to-end scenarios (SAN-1814 to SAN-1824).

## Linear breakdown (created 2026-10-06)

Project **Enhancement** (P-SAN-48), milestone **Limit Jury Access**. Every task is assigned to **Sandeep**, status Todo. Each task covers exactly one repo, shown by its `Repo:` label. 8 parent tasks, 36 subtasks. (A standalone project P-SAN-77 was created first, then moved to Canceled when the user asked for a milestone inside Enhancement instead.)

| Parent | Repo | Priority | Blocked by | Subtasks (build order) |
|---|---|---|---|---|
| **SAN-1676** P0 Block jury role on application-data pages | admin | Urgent | — (ships first) | SAN-1684 helper · SAN-1685 detail pages · SAN-1686 Kanban/tableview · SAN-1687 analysis_form · SAN-1688 verification |
| **SAN-1677** P1 Tenants flag | tenants | High | — | SAN-1689 entity · SAN-1690 3 field lists · SAN-1691 staging + tenants-admin toggle |
| **SAN-1678** P1 Backend enum + schema | backend | High | — | SAN-1692 enum · SAN-1693 hidden-fields entity · SAN-1694 round columns · SAN-1695 staging schema + docs |
| **SAN-1679** P1 Frontend `IFeatures` | frontend | Low | — | (single task) |
| **SAN-1680** P2 Admin foundation | admin | High | SAN-1677, SAN-1678 | SAN-1697 flag const + include · SAN-1698 probe + loader · SAN-1699 question list · SAN-1700 filter + CLI harness · SAN-1701 audit + counts |
| **SAN-1681** P3 Juror filter | admin | Urgent | SAN-1680 | SAN-1702 filter before formatFormSubmissionsData · SAN-1703 strip record.data · SAN-1704 pitch deck / Power Pitch · SAN-1705 banner · SAN-1706 15-min TTL · SAN-1707 verification |
| **SAN-1682** P4 Config pop-up | admin | High | SAN-1680 | SAN-1708 button · SAN-1709 load + modal · SAN-1710 controls · SAN-1711 save · SAN-1712 copy previous · SAN-1713 read-only + flag-off · SAN-1714 verification |
| **SAN-1683** P5 Badges, activity, preview | admin | Medium | SAN-1682 | SAN-1715 Kanban badge · SAN-1716 tableview badge · SAN-1717 activity + CSV · SAN-1718 preview · SAN-1719 gates + E2E + docs |

Deploy order: SAN-1676 (any time) → tenants → backend → frontend → admin P2–P5.

## Delivery process (the standing 10-step loop)

| Step | What | Status |
|---|---|---|
| 1 | Orient on the BRD / issue | done |
| 2 | `/from-linear`: full loop, not `/bug-fix` (4 repos, new table, flag) | done |
| 3 | Spec drafted with file:line evidence | done (this file) |
| 4 | Design questions resolved; approved by Nirmal | **done 2026-10-06** (OQ-1..4) |
| 5 | Contract checks: `/trace-flag limit_jury_access_enabled`, `/check-isolation`, `/cross-repo-review` | not run; built into SAN-1691, SAN-1695, SAN-1698, SAN-1711 and SAN-1719 |
| 6 | Tests first: blocked (no guardian skill). Substitutes are tsc/lint/build/test for Node repos, and `php -l` + CLI harness (SAN-1700) + manual matrices (SAN-1688, SAN-1707, SAN-1714) for admin | not started |
| 7 | Branch: none, work directly on `ai_native_setup` | n/a |
| 8 | Implement in the order above; Linear states move as the work happens | not started |
| 9 | Verify with real output; update module specs + indexes | not started |
| 10 | Commit and push to `ai_native_setup` only after Nirmal confirms each diff; close the issues | not started |

## Out of scope

Per-juror / per-panel sets (D2); partial masking; redaction inside documents; applicant-side marking/notice (D3); form-builder confidential tag (D1); mentors/sponsors (D5); restriction templates FR-17 (Could — deferred); rubric-linked warning BR-03 (D-Rubric, until a criterion↔question link exists); legacy/mentor/individual/VS jury rounds (D-Scope); private delivery for ImageKit image/video (Risk 1); juror PDF export and juror AI summary (do not exist — D-Export/AI).

## Open questions

None. OQ-1..OQ-4 were answered by Nirmal on 2026-10-06:

| # | Question | Answer |
|---|---|---|
| OQ-1 | Tenant feature flag? | **Yes**, `limit_jury_access_enabled`, default off (D-Flag). Overrides the recommendation of "no flag". |
| OQ-2 | What is "evaluation closed" (BR-08)? | **Reuse programme `program_closed`** (D-Closed). |
| OQ-3 | Restrict jury users flagged `is_jury_reviewer` too? | **Yes** (D-Reviewers) — same existing jury role, no new role. |
| OQ-4 | Block jurors from the admin data pages? | **Yes, shipped first as its own Urgent issue** (D-Block). |

Approved by Nirmal on 2026-10-06. The remaining `[DECIDED — recommended default]` rows (D-List, D-Child, D-Rubric, D-Pitch, D-TTL, etc.) stand unless overridden.
