---
id: FT-006
title: CFA E2E Regression Suite
type: feature
status: approved                 # draft → approved → in-progress → in-review → done
linear: https://linear.app/sanchiconnect/project/cfa-e2e-regression-suite-ft-006-a022b5a7a1fd
owner: Ritu Raj                 # user-confirmed owner 2026-10-12 (email not recorded here)
repos:
  - sc-saas-e2e                 # ONLY repo edited by this spec (Playwright + TypeScript, branch main).
                                # App-side data-testid asks (sc-saas-admin, sc-saas-frontend) are listed
                                # under "Follow-ups" and get their own separately-labelled issues later —
                                # they are NOT part of this spec's edit scope.
contracts:
  api:
    # CONSUMED, not changed. Any rename/shape change here breaks the suite.
    - "POST api/v1/public/application-program-leads/upsert"                         # guest lead upsert (PWA guest modal)
    - "POST api/v1/public/otp_verifications/send | /verify"                         # md5-hashed code; rate-limited 10/60s
    - "POST api/v1/public/forms-management/submission/:formUUID/submit"             # draft save + final save (guest)
    - "POST api/v1/application-programs-management/:programUUID/:submissionId/apply" # apply
    - "sc-saas-admin submitAction contract (session-cookie jQuery AJAX POSTs, see Contracts & invariants)"
    - "sc-saas-admin GET download routes under /application_management/submission-application-management/{programId}/{slug}/…"
  flags:
    # READ (via skip-when-off), never toggled by the suite.
    - application_management
    - application_management_round_status_updates
    - call_for_applications_submitted_email_enabled
    - limit_jury_access_enabled
    - jury_nda_enabled
  events: []
tenant_scoped: true             # runs against exactly one QA tenant per environment and writes CFA rows into it
depends_on: []                  # soft deps: SAN-1864/SAN-1877 deployed per env (fixed OTP + wildcard), SAN-1613 (nightly reset)
created: 2026-10-12
---

# CFA E2E Regression Suite

**Evidence-strength key:** Evidenced = cited `file:line` (spot-checked in code 2026-10-12 where marked ✔, otherwise taken from the same-day code inventory). `[INFERRED — requires validation]` = reasonable extrapolation. `[NOT SPECIFIED IN SOURCE]` = real gap. `[DESIGN DECISION PENDING]` = needs a human call. Decisions marked **(decided 2026-10-12)** were made by the user/product owner and are not open.

**Linear tracking:** project [CFA E2E Regression Suite (FT-006)](https://linear.app/sanchiconnect/project/cfa-e2e-regression-suite-ft-006-a022b5a7a1fd). There is one issue per phase. All are assigned to Ritu Raj, state Todo, labelled `Improvement` (there is no `Repo: E2E` label), and related to SAN-1576.

| Phase | Issue | Priority |
|---|---|---|
| P1 Fixture & wiring | SAN-1879 | High |
| P2 Program setup & form builder | SAN-1880 | Medium |
| P3 Applicant path (PWA), related to SAN-1606 | SAN-1881 | Medium |
| P4 Admin review & rounds, related to SAN-1607 and SAN-1878 | SAN-1882 | Medium |
| P5 Jury & evaluation, related to SAN-1607 | SAN-1883 | Medium |
| P6 Downloads & reports | SAN-1884 | Medium |
| P7 AI analysis pages (load only) | SAN-1885 | Low |

## Problem

Call for Applications (CFA, a.k.a. application programs) is the most-used workflow on the platform and spans three repos: admin program setup and review (`sc-saas-admin`), applicant apply flow (`sc-saas-frontend`), and the business API (`sc-saas-backend`). The only automated coverage is the SAN-1576 smoke suite, which has two CFA journeys (4: apply, 5: approve) and must stay under 10 minutes. Regressions in round transitions, jury evaluation, form builder, downloads and applicant emails currently only show up in manual QA or in production. The Q2 backlog issues SAN-1606 (startup path) and SAN-1607 (program-office/admin path) describe this need but have no design. This spec defines a nightly `@regression @cfa` Playwright suite in `sc-saas-e2e` that covers CFA end to end. Each run is isolated by its own **test-mode program**, so the suite is parallel-safe on a shared QA tenant.

## Goal

- A per-run CFA program fixture. It creates a test-mode program with a form and rounds, and tears it down afterwards. SAN-1576 journeys 4 and 5 also reuse it.
- Regression coverage, in 7 phases, of program setup, the form builder, guest and logged-in apply, admin review and round transitions, jury evaluation, downloads and reports, and AI-analysis page loads.
- Every test is tagged `@regression @cfa` (plus `@write` where it writes, `@admin`/`@frontend`, and a stakeholder tag). The exceptions are SAN-1576 journeys 4 and 5, which stay `@smoke`.

## Scope / Out of scope

**In scope:** everything under P1–P7 below, on `development` (primary) and `staging`. On production only read-only, non-`@write` tests run, and the per-run fixture is `@write`, so in practice the CFA suite is skipped on production (`playwright.config.ts:16` ✔ `grepInvert: /@write/` when writes are disallowed).

**Out of scope (decided 2026-10-12):**
- **Payments.** These hit real gateways.
- **AI voice agent.** Each call is a real, billed phone call (`sc-saas-admin/CLAUDE.md`, voice agent section).
- **Program promotion / outreach.** It writes the *main* tenants DB and mails other tenants. The `sendOutreachRequestEmailPartnerPayload` path reads `$mainDatabase` `tenant_users` (`program.php:133-148` ✔).
- **Invite / move to community.**
- **AI analyzer calls.** These spend real LLM money and no mock exists. P7 is pages-load only.
- **Toggling tenant-wide cockpit flags mid-run.** Tests `test.skip()` when a flag they need is off.
- **`add_new_jury`.** It creates accounts and sends mail. Use `add_jury_member` with the seeded QA jury instead.
- **`sc-saas-admin/modules/form_builder/public_submissions.php`.** It has no auth (already recorded in that module's spec). No test is built on it.
- **Kanban drag-and-drop as the primary path for moving applications.** At most one smoke-level kanban render check. All moves go through the table view (see Risks).
- **Creating the data-testid asks as Linear issues now.** They are listed under Follow-ups only.

## Decisions (decided 2026-10-12, user/product owner)

1. **D1 Repo and environments.** The repo is `sc-saas-e2e` (Playwright + TS, branch `main`). `E2E_ENV=development` points at `ai_native_setup` on `thub.sanchidev.in`. `staging` points at `stagingdemo` on `demo.sanchiapp.com`. `production` is read-only and `@write` tests are skipped there (README "Test environments" ✔).
2. **D2 Owner.** Ritu Raj owns the suite and every journey in it.
3. **D3 AI analysis (P7) is pages-load only.** No analyzer calls.
4. **D4 Guest-apply addresses.** `sc_cfa_*@yopmail.com` is added to the **dev** backend's `QA_FIXED_OTP_EMAILS`. The local-part wildcard comes from SAN-1877 and the fixed OTP from SAN-1864. This is approved for development. On staging the guest-OTP tests skip unless the same pattern is allowlisted there (see Prerequisites).
5. **D5 Tentative is broken.** SAN-1878 is filed to Sandeep: the backend has no tentative-round route for CFA. The tentative test is written as `test.fail()` with a SAN-1878 annotation and is flipped to a normal test when the fix lands.
6. **D6 Exclusions.** As listed under Out of scope.
7. **D7 Smoke / regression split.** SAN-1576 journeys 4 (apply) and 5 (approve) are `@smoke`, stay under the 10-minute smoke budget, and reuse the P1 fixture. Everything else in this spec is `@regression @cfa`. This spec absorbs the CFA parts of SAN-1606 (startup path) and SAN-1607 (program-office/admin path), and its Linear issues are linked to them.
8. **D8 Isolation primitive is test mode.** `changeTestMode` with `action=enable` sets `test_mode_enabled=1` **and** `status=1` (`sc-saas-admin/modules/application_management/program.php:1272-1308` ✔). Test-mode programs are hidden from public and authenticated program lists (`sc-saas-backend/.../repositories/application-programs.repository.ts:125,348` ✔ `testModeEnabled=false`) and are ignored by the notification counters (`notification-counters.repository.ts:91` ✔). The PWA ignores closed and deadline state for test-mode programs (`sc-saas-frontend/.../program-public-apply.component.ts:897` ✔). Tests reach the program by direct URL `/programs/apply/{code}/{slug}`.
9. **D9 "Closed program blocks applying" is tested on a dedicated, long-lived closed program, never by turning test mode off.** Test mode deliberately ignores closed and deadline state (D8), so a per-run program can't show it. Each environment gets one `[QA] CFA Closed (do not delete)` program, live with test mode **off** and applications closed. It sits under "Past" on the PWA, which is harmless, and is never written to by tests. Decided 2026-10-12. The alternative, briefly turning test mode off on a per-run program, was rejected because it would list a `[QA]` program publicly.
10. **D10 Backend apply ignores closed, deadline and unpublished state: filed as SAN-1886** (Enhancement → milestone `QA_Automation_Bugs-Found`, Sandeep). The suite covers it with an API-level test that is **known-failing** (`test.fail()`) until SAN-1886 ships, the same pattern as Tentative / SAN-1878 (also moved to that milestone). Decided 2026-10-12.

## How CFA is driven (verified surface)

- **Admin has no REST API.** Admin mutations are jQuery AJAX POSTs to the same page URL with `submitAction=<name>`, sent on the PHP session cookie, and most have no CSRF token. After the `setup-admin` UI login, tests can call `page.request.post(<page url>, { form: { submitAction, … } })` for fast setup and cleanup. UI tests then exercise the screens themselves.
- **Create program.** `POST /table/application_programs` with `submitAction=createApplicationProgram` (`sc-saas-admin/modules/table.php:852` ✔). It creates the `application_programs` row and its `forms` row and returns `editUrl`.
- **Delete program.** `submitAction=deleteApplicationProgram` (`program.php:1016` ✔; a second handler exists at `table.php:1170` ✔). The delete is **refused when any Jury NDA rows exist** (`program.php:1021-1026` ✔ `juryNdaProgramHasData`). Otherwise it hard-deletes about 16 tables, including `forms_submissions` for the program's forms, its rounds, ratings, jury, questions and FAQs (`program.php:1028-1082` ✔). It does **not** delete leads, documents, AI analyses, notifications, S3 objects or email logs.
- **Program wizard** at `/application_management/program/{id}/edit/{slug}`:
  - `editProgram` (`program.php:226`), including `bypass_otp_verification` (`program.php:262` ✔) and the re-application settings `allow_re_application` + `re_application_duration_type=immediate`
  - `editEvaluation` (L549)
  - `makeProgramLive` (L175 ✔; also sets `forms.status=1`)
  - `closeProgramApplications` (L925 ✔) and `reopenProgramApplications` (L968)
  - `closeProgram` (L868)
  - `changeTestMode` (L1272 ✔)
- **Form builder** at `/form-management/edit-form/{formId}/{slug}?programId=…&applicationForms=1`:
  - `saveForm` (`sc-saas-admin/modules/form-management/edit-form.php:309` ✔)
  - `importFieldsFromForm` (L456 ✔)
  - `uploadFieldsJson` (L510 ✔, requires `is_dev`)
  - versions and `restoreForm`
  - 22 field types; field ordering uses jQuery-UI sortable.
- **PWA apply.** Programs are listed at `/call-for-applications` (live, non-test-mode only). The apply page is `/programs/apply/:code/:slug[?autoStatusCheck=true]`.
  - **Guest flow:** modal → `POST api/v1/public/application-program-leads/upsert` → OTP send/verify (the code is md5-hashed client-side, README ✔). **No user or session is created.** The guest identity is kept in `localStorage['application-{uuid}']`, and `forms_submissions.user_id` is NULL.
  - **Form save:** `POST api/v1/public/forms-management/submission/:formUUID/submit` (`public-form-management.controller.ts:69` ✔). Autosave runs every 60s, and drafts have `submitted=0`.
  - **Apply:** `POST api/v1/application-programs-management/:programUUID/:submissionId/apply` (`application-program.controller.ts:344` ✔; guards are commented out per the backend module spec).
  - **Logged-in users** skip the OTP.
  - The OTP routes are rate-limited to 10 requests per 60s.
  - Re-applying after a rejection edits the same submission (SAN-352).
- **Admin review**
  - **Kanban:** `/application_management/submission-application-management/{programId}/{slug}`. It uses jQuery-UI drag, which is flaky.
  - **Table view:** `/application_management/submission-application-management-tableview/…`, with a Move-to-Round dropdown and a bulk Move action.
  - **Detail page:** `/application-submission-detail/{submissionId}`.
  - **Drafts page:** `/application_management/draft_applications/{programId}/{slug}`, with `moveToSubmitted`, `deleteApplication`, `download_csv` and bulk email.
  - **Fast seeding:** `import_applications_csv` (`submission-application-management.php:3033` ✔; also `-tableview.php:1073` ✔) followed by `moveToSubmitted`.
- **Rounds and round actions**
  - Round CRUD: `createProgramRound` (the round name must be unique), `editRound`, `deleteRound`.
  - Round editor iframe `#loadIframeBoxEditRound`: open `/application_management/edit_program_round/{roundId}?section=…` directly.
  - `silent_transfer` suppresses the move and reject emails.
  - `freeze_applications` (`edit_program_round.php:469` ✔) is enforced by the backend (`application-program.service.ts:771,1049` ✔).
  - Move: `moveApplicationToNextRound` calls the backend update-round.
  - Reject: `rejectApplication` calls reject-round.
  - Tentative: `tentativeApplication` (`submission-application-management.php:180,632` ✔) is **broken** (SAN-1878).
  - Other actions: `removeApplicationFromEvaluation`, `sendForResubmission`, `sendForRoundResubmission`.
  - Round status is shown to the applicant only when `application_management_round_status_updates` is on (`tenant-users.entity.ts:1531` ✔).
- **Evaluation**
  - Add a jury member with `add_jury_member`.
  - Allotment at `/application_management/edit_program_round_jury/…`: `add_allotment`, `remove_allotment`, `add_auto_allot_jury`.
  - Jury scoring at `/jury/round-applications/program/{p}/round/{r}`: `addRating`, `answerQuestions`. Scoring needs rating criteria on the round (SAN-1498).
  - Ratings report: `download_ratings_report`.
  - Limit Jury Access: `limit_jury_access_enabled` (`tenant-users.entity.ts:2470` ✔). It is DB-only and safe to test.
  - Jury NDA: `jury_nda_enabled` (`tenant-users.entity.ts:650` ✔). It writes to S3, sends emails and blocks program deletion.
- **Downloads.** All are GET under `…/submission-application-management/{id}/{slug}/`:
  - `export_all_applications[_xlsx]`
  - `download_program_data[_xlsx]`
  - `download_all_applications[_xlsx]`
  - `download_ratings_report`
  - `download_bulk_pdf` (ZIP)
  - `download_bulk_attachments` (ZIP, from S3)
  - `{round}/download_csv`
  - `download_jury_allotment_csv`
  - On the detail page: `download_pdf`, `download_attachments`
- **Other pages:**
  - Leads: `/application_management/leads`. There is no delete path, so rows accumulate.
  - Reports: `/application_management/reports/{programId}/{slug}`.
  - Timeline: `/application_management/timeline/{programId}`.
  - AI pages: `analysis_list/{programId}`, `analysis_form`, `analysis_cost_dashboard`.
- **Emails.** These are verified through the admin `email_logs` list, using the same pattern as `sc-saas-e2e/tests/admin/email-log.spec.ts:17-45` ✔ (filter by `recipient` + `template_code`, then poll). Template codes are kebab-case (`sc-saas-backend/src/core/constants/enum.ts:925-930` ✔):
  - `verify-email-address`
  - `application-program-management-application`, only when `call_for_applications_submitted_email_enabled` is on (`tenant-users.entity.ts:2290` ✔)
  - `application-program-management-success-email` (move, non-silent)
  - `application-program-management-reject-email`
  - `resubmit-application`, `resubmit-application-specific-documents`
- **Selectors.** No CFA admin or PWA surface has a `data-testid` [inventory]. Page objects use roles, labels and stable ids until the follow-up asks below land.

## Fixture design (P1)

**New Playwright project `cfa`.** It sets `testDir: ./tests/cfa` and `dependencies: ['setup-frontend', 'setup-admin']`. Both setups are needed because each CFA test spans admin and the PWA. A global `cfa-setup` / `cfa-teardown` project pair owns the per-run program.

**Per-run program lifecycle**
1. **Run id.** `runId = <yyyymmdd-hhmm>-<short random>`, exposed as `CFA_RUN_ID`. Names use the `[QA]` prefix agreed in the README nightly-reset plan, e.g. `[QA] CFA run-<runId>`.
2. **Create.** With an `APIRequestContext` built from `.auth/admin.json` and `ADMIN_URL`:
   1. `createApplicationProgram` (parse `editUrl` to get `programId` and `slug`)
   2. `importFieldsFromForm` from the env's **E2E template form** into the program form
   3. `editProgram` (title, dates, `bypass_otp_verification` per test need, re-application `immediate`)
   4. `createProgramRound` ×2 (`[QA] R1-<runId>`, `[QA] R2-<runId>`), including rating criteria on R2 (SAN-1498)
   5. `changeTestMode action=enable`, which also sets status=1
   6. `makeProgramLive`
   7. Write `{programId, uuid, code, slug, formId, formUUID, roundIds}` to `.cfa/run.json`.
3. **Use.** Worker-scoped fixtures `cfaProgram` (reads `run.json`) and `cfaAdmin` (an admin `APIRequestContext` with helpers: `submitAction(page, action, form)`, `importApplicationsCsv`, `moveToSubmitted`, `moveToRound`, `reject`, `downloads.get(name)`). Each test creates **its own applicants and submissions**, with unique `[QA] <test>-<runId>` names or `sc_cfa_<runId>_<n>@yopmail.com` addresses, so parallel tests never touch each other's rows.
4. **Program- and round-level state.** Tests that change state for the whole program or round (freeze, close/reopen, closeProgram, deleteRound, evaluation settings, test-mode toggles) call the same factory, `createCfaProgram({ … })`, to get a **throwaway program of their own**, and delete it in `afterAll`. They run in `test.describe.configure({ mode: 'serial' })` blocks.
5. **Teardown.** `cfa-teardown` calls `deleteApplicationProgram` for the run program and for every throwaway program the run recorded. It also does an **orphan sweep**: any `[QA] CFA run-*` program older than 24h is deleted, which covers crashed runs [INFERRED — requires validation: listing via `/table/application_programs` search].
6. **Never on the per-run program:** Jury NDA. NDA rows make `deleteApplicationProgram` refuse (`program.php:1021` ✔). NDA tests use the **dedicated long-lived NDA program** (see Prerequisites) and never delete it.

**Leftover-rows caveat.** `deleteApplicationProgram` leaves these behind:
- `application_program_leads` (and the Leads page has no delete path)
- documents
- AI analyses
- notifications
- S3 objects (attachments, bulk ZIPs)
- `email_logs`

These accumulate on the QA tenant, roughly one program's worth of leads and email-log rows per run. Removing them is **SAN-1613's job** (nightly reset, which identifies test data by the `[QA]` / `qa+run-` / `sc_cfa_` prefixes). This suite only guarantees the 16-table program graph is gone. Until SAN-1613 lands, tests must not assert on global counts (total leads, total emails). They assert only on rows filtered by their own run id or address.

## Test-data and environment prerequisites

| Item | development (`thub.sanchidev.in`) | staging (`demo.sanchiapp.com`) | production |
|---|---|---|---|
| Seeded QA accounts (startup, program_office, admin, jury) | exist (`npm run seed`, README ✔) | exist | n/a, CFA suite skipped |
| Fixed OTP (SAN-1864) + wildcard (SAN-1877) deployed | required | required before staging run can go green | n/a |
| `sc_cfa_*@yopmail.com` in backend `QA_FIXED_OTP_EMAILS` | **approved, add** (D4) | not yet; guest-OTP tests skip unless set | never |
| New secret `QA_CFA_EMAIL_PATTERN` (e.g. `sc_cfa_*@yopmail.com`) | set | set only if allowlisted | unset |
| **E2E template form**: one form, created once by hand per env, `[QA] E2E template form`, holding a representative field set (short text, long text, email, phone, dropdown, radio, checkbox, date, number, file upload, and one required field) | create once; id stored as secret `QA_CFA_TEMPLATE_FORM_ID` | same | n/a |
| **Dedicated NDA program**: `[QA] CFA NDA (do not delete)`, test mode on, the seeded QA jury allotted, used only by the NDA test | create once; id in `QA_CFA_NDA_PROGRAM_ID` | same | n/a |
| **Dedicated closed program** (D9): `[QA] CFA Closed (do not delete)`, live, test mode **off**, applications closed, form copied from the E2E template form, never written to by tests | create once; its code and slug stored as secret `QA_CFA_CLOSED_PROGRAM_PATH` (`{code}/{slug}`) | same | n/a |
| Flags expected **ON** on the QA tenant: `application_management`, `application_management_round_status_updates`, `call_for_applications_submitted_email_enabled`, `limit_jury_access_enabled`, `jury_nda_enabled` | expected on; each dependent test skips if off | same | n/a |
| QA admin permissions: `can_broadcast_messages` (email log page, per `email-log.spec.ts:7` ✔) plus application-management access | required | required | n/a |
| New devDependencies in `sc-saas-e2e/package.json`: **`xlsx`** (parse .xlsx/.csv downloads) and **`adm-zip`** (inspect ZIP downloads), plus `@types/adm-zip` | P6 | P6 | n/a |

Flag state is read once in `cfa-setup`, from the cockpit `verify_tenant` response `features` map, and saved to `run.json`. Tests call `test.skip(!flags.x, '<flag> is off on this tenant')`. **The suite never writes a flag.**

## Acceptance criteria (per phase, one bullet per test)

All tests are Given/When/Then. Unless noted, each is tagged `@regression @cfa @write` plus `@admin` or `@frontend`. "Program" means the per-run test-mode program, and "throwaway" means a program created by the factory for that test.

### P1 — Fixture, project wiring and helpers (unblocks everything) — SAN-1879
- [ ] A `cfa` project, plus the `cfa-setup` and `cfa-teardown` projects, exist in `playwright.config.ts`. `npm run typecheck` passes.
- [ ] **Given** admin auth state, **when** `cfa-setup` runs, **then** `.cfa/run.json` has the program id, uuid, code, slug, form id and uuid, and 2 round ids. The program shows `test_mode_enabled` and live in the admin program list.
- [ ] **Given** a completed run, **when** `cfa-teardown` runs, **then** `/application_management/program/{id}/edit/{slug}` no longer resolves to that program, and the run's throwaway programs are gone too.
- [ ] **Given** a `[QA] CFA run-*` program older than 24h, **when** teardown runs, **then** it is deleted (orphan sweep).
- [ ] **Given** the per-run program, **when** an anonymous browser opens `/call-for-applications`, **then** the program is **not** listed (test-mode hidden). **When** it opens `/programs/apply/{code}/{slug}` directly, **then** the apply page renders.
- [ ] `cfaAdmin.submitAction()` returns parsed JSON and fails loudly on `error: true`. `importApplicationsCsv` + `moveToSubmitted` seed N submitted applications in under 15s.
- [ ] SAN-1576 journeys 4 (apply) and 5 (approve) are rewritten to use this fixture, keep their `@smoke` tag, and the smoke suite still runs under 10 minutes.
- [ ] A missing `QA_CFA_TEMPLATE_FORM_ID` or admin secret makes the whole `cfa` project **skip** with a clear reason, not fail.

### P2 — Program setup, wizard and form builder (admin) — SAN-1880
- [ ] **Given** the admin is logged in, **when** they create a program through the UI at `/table/application_programs` (Add), **then** they land on the wizard `editUrl` and the program appears in the table. The program is a throwaway and is cleaned up afterwards.
- [ ] **Given** a throwaway program, **when** the admin edits basic details in the wizard and saves (`editProgram`), **then** a reload shows the saved values.
- [ ] **Given** a throwaway program, **when** the admin saves evaluation settings (`editEvaluation`), **then** a reload shows them.
- [ ] **Given** a throwaway program, **when** the admin creates a round, **then** it appears in the round list. **When** they create a second round with the same name, **then** they see an error (unique name).
- [ ] **Given** a throwaway round, **when** the admin edits it through `/application_management/edit_program_round/{roundId}?section=…`, **then** the change persists. **When** they delete the round, **then** it disappears.
- [ ] **Given** a throwaway program in test mode, **when** test mode is disabled (`changeTestMode action=disable`), **then** the wizard shows test mode off. **When** it is re-enabled, **then** the program is hidden from `/call-for-applications` again. The test-mode-off window lasts one assertion, and no deadline is set on the program.
- [ ] **Given** a throwaway draft program, **when** the admin clicks Make Live, **then** the program and its form are live (the apply page renders for a direct-URL visitor).
- [ ] **Given** a live throwaway program, **when** the admin closes applications, **then** the wizard shows closed. **When** they reopen, **then** it shows open. Admin-side state only. The PWA-side "closed" behaviour is covered in P3 against the dedicated closed program (D9).
- [ ] **Given** a throwaway program, **when** the admin closes the program (`closeProgram`), **then** its status shows closed in the program list.
- [ ] **Form builder (UI test 1).** **Given** the program form open in `/form-management/edit-form/{formId}/{slug}?programId=…&applicationForms=1`, **when** the admin adds a short-text and a dropdown field and saves (`saveForm`), **then** the PWA apply page shows both fields.
- [ ] **Form builder (UI test 2).** **Given** a saved form, **when** the admin saves a second version and then restores the first, **then** the field set matches the first version.
- [ ] **Given** a throwaway program, **when** fields are imported from the E2E template form (`importFieldsFromForm`), **then** the field count equals the template's field count. This also checks the fixture's seeding path.
- [ ] `uploadFieldsJson` is **not** tested, because it requires `is_dev`.

### P3 — Applicant path, PWA (absorbs the CFA parts of SAN-1606) — SAN-1881
- [ ] **Guest apply with OTP.** **Given** the program with OTP required and a fresh `sc_cfa_<runId>_<n>@yopmail.com`, **when** the guest fills the lead modal, verifies the fixed OTP, completes the form and submits, **then** the confirmation state shows, the submission appears in the admin table view with an empty user, and (if `call_for_applications_submitted_email_enabled` is on) an `application-program-management-application` email-log row exists for that address. Skips when `QA_CFA_EMAIL_PATTERN` is unset.
- [ ] **Guest apply with `bypass_otp_verification`.** **Given** a throwaway program with OTP bypass on, **when** a guest applies, **then** no `verify-email-address` row is logged for that address and the submission is created. This path keeps most guest tests clear of the 10/60s OTP rate limit.
- [ ] **Logged-in apply.** **Given** the seeded startup (`asRole('startup')`), **when** they open the apply URL, **then** no OTP modal appears. **When** they submit, **then** the submission is linked to their user in the admin detail page.
- [ ] **Draft and resume.** **Given** a guest who has filled part of the form, **when** they trigger save (explicit save, or wait past the 60s autosave in one test only), **then** the admin drafts page lists the draft with `submitted=0`. **When** the same browser context (same `localStorage['application-{uuid}']`) reopens the URL, **then** the entered values are restored.
- [ ] **Required-field validation.** **Given** the form's required field is empty, **when** the applicant submits, **then** a validation message shows and no apply call is made.
- [ ] **File upload field.** **Given** the template's file-upload field, **when** a small PDF is attached and the form submitted, **then** the admin detail page lists the attachment.
- [ ] **Status tracking.** **Given** a submitted application, **when** the applicant opens `/programs/apply/{code}/{slug}?autoStatusCheck=true`, **then** the status view shows the current round. If `application_management_round_status_updates` is on, **then** after an admin move it shows the new round.
- [ ] **Re-apply after rejection (SAN-352).** **Given** a throwaway program with `allow_re_application` and `re_application_duration_type=immediate`, and an application rejected by the admin, **when** the applicant re-applies, **then** the **same** submission id is edited (no new row in the table view).
- [ ] **Resubmission.** **Given** an application sent back with `sendForResubmission`, **when** the applicant opens the link and resubmits, **then** the admin sees the updated value and a `resubmit-application` email-log row exists.
- [ ] **Freeze blocks edits.** **Given** a throwaway program whose current round has `freeze_applications=1`, **when** the applicant tries to save or resubmit, **then** the backend refuses (`application-program.service.ts:771,1049` ✔) and the PWA shows the error.
- [ ] **Test-mode program unlisted.** **Given** the per-run program, **when** the seeded startup browses `/call-for-applications`, **then** the program is absent. This is the authenticated counterpart of the P1 anonymous check.

- [ ] **Given** the dedicated closed program (D9, `QA_CFA_CLOSED_PROGRAM_PATH`), **when** a guest or the seeded startup opens `/programs/apply/{code}/{slug}`, **then** the page shows applications closed and the Apply button is disabled. **And** the program is listed under "Past", not "Active", on `/call-for-applications`. Read-only; skipped if the secret is unset.

### P4 — Admin review and round transitions (absorbs the CFA program-office/admin parts of SAN-1607) — SAN-1882
- [ ] **Table view loads.** **Given** N seeded submissions, **when** the admin opens the table view, **then** N rows with the seeded names are shown.
- [ ] **Kanban renders.** **Given** seeded submissions, **when** the admin opens the kanban, **then** each seeded card is in its round column. There is no drag.
- [ ] **Move (non-silent).** **Given** a submission in R1, **when** the admin moves it to R2 from the table view dropdown, **then** the row shows R2 and an `application-program-management-success-email` row exists for the applicant.
- [ ] **Move (silent).** **Given** `silent_transfer` on, **when** the admin moves a submission, **then** it moves and **no** success-email row is logged for that address.
- [ ] **Bulk move.** **Given** 3 selected submissions, **when** the admin uses bulk Move, **then** all 3 show the target round.
- [ ] **Reject.** **Given** a submission, **when** the admin rejects it, **then** its status is rejected and an `application-program-management-reject-email` row exists (not silent).
- [ ] **Tentative (known failing, SAN-1878).** **Given** a submission, **when** the admin marks it Tentative, **then** it shows tentative. Written as `test.fail()` with annotation `{ type: 'issue', description: 'SAN-1878' }`.
- [ ] **Remove from evaluation.** **Given** a submission, **when** the admin removes it from evaluation, **then** it leaves the round's evaluation list.
- [ ] **Round resubmission.** **Given** a submission, **when** the admin uses `sendForRoundResubmission`, **then** a `resubmit-application` or `resubmit-application-specific-documents` email-log row exists.
- [ ] **Freeze toggle.** **Given** a throwaway program, **when** the admin toggles `freeze_applications` on and off in the round editor, **then** the toggle persists after reload.
- [ ] **Detail page.** **Given** a submission, **when** the admin opens `/application-submission-detail/{submissionId}`, **then** the answers match what the applicant submitted.
- [ ] **Drafts page.** **Given** a draft (seeded via the PWA save in P3, or a CSV import left unsubmitted), **when** the admin opens the drafts page, **then** it is listed. **When** they use `moveToSubmitted`, **then** it appears in the table view. **When** they delete a second draft (`deleteApplication`), **then** it disappears.
- [ ] **CSV import.** **Given** a 3-row CSV built from the template form's columns, **when** the admin imports it in the UI (`import_applications_csv`), **then** 3 rows appear in drafts or the table view.
- [ ] **Round status visible to the applicant.** Skips if `application_management_round_status_updates` is off. **Given** a move to R2, **when** the applicant checks status, **then** R2 is shown.

- [ ] **Known-failing until SAN-1886** (`test.fail()`). **Given** the dedicated closed program, **when** a draft submission is sent straight to `POST /api/v1/application-programs-management/:programUUID/:submissionId/apply`, **then** the API rejects it with 4xx. Today it returns 2xx (D10). When SAN-1886 ships, this test starts "unexpectedly passing", which is the signal to drop `test.fail()`. The submission row this creates is the only write against the closed program; it's tagged `[QA]` and swept like other leftovers (SAN-1613).

### P5 — Jury and evaluation (absorbs the jury parts of SAN-1607) — SAN-1883
- [ ] **Add jury member.** **Given** a throwaway program, **when** the admin adds the seeded QA jury with `add_jury_member`, **then** the jury list shows them. `add_new_jury` is never used.
- [ ] **Manual allotment.** **Given** a jury member and 2 submissions in R2, **when** the admin allots one submission (`add_allotment`), **then** the allotment CSV (`download_jury_allotment_csv`) lists it. **When** they remove it (`remove_allotment`), **then** it is gone.
- [ ] **Auto-allot.** **Given** 2 submissions and 1 jury member, **when** `add_auto_allot_jury` runs, **then** both are allotted.
- [ ] **Jury rates (second browser context).** **Given** an allotted submission in R2, which has rating criteria (SAN-1498), **when** the jury (`.auth/jury.json`, separate context) opens `/jury/round-applications/program/{p}/round/{r}` and submits a rating (`addRating`), **then** the admin's ratings report (`download_ratings_report`) contains that score.
- [ ] **Jury answers questions.** **Given** a round with a jury question, **when** the jury answers it (`answerQuestions`), **then** the admin detail page shows the answer.
- [ ] **Limit Jury Access.** Skips if `limit_jury_access_enabled` is off. **Given** limit-access on the throwaway program and the jury allotted to only one of two submissions, **when** the jury lists round applications, **then** only the allotted one is visible, and opening the other's URL directly is denied.
- [ ] **Jury NDA.** Skips if `jury_nda_enabled` is off. This test runs **only** on the dedicated NDA program. **Given** the jury has not yet accepted on this run, **when** the jury opens the program, **then** the NDA gate shows, and acceptance (or the existing accepted state) lets them through. It never runs against a per-run or throwaway program [INFERRED — requires validation: whether a re-run on an already-accepted NDA can still assert the gate. If not, the test asserts the accepted state only].

### P6 — Downloads, leads, reports, timeline — SAN-1884
- [ ] **XLSX exports.** **Given** seeded submissions, **when** the admin GETs `export_all_applications_xlsx`, `download_program_data_xlsx` and `download_all_applications_xlsx`, **then** each returns 200 with an xlsx content type, and `xlsx` parsing finds the seeded applicant names.
- [ ] **CSV exports.** The CSV (non-`_xlsx`) variants of those exports and `{round}/download_csv` parse and contain the seeded names.
- [ ] **Ratings report.** `download_ratings_report` contains the P5 rating, or the header row on a throwaway program without ratings.
- [ ] **Bulk PDF.** **When** `download_bulk_pdf` is requested for at most 3 submissions, **then** a ZIP is returned whose `adm-zip` entry count equals the submission count. The test timeout is 120s.
- [ ] **Bulk attachments.** **When** `download_bulk_attachments` is requested for the P3 upload submission, **then** the ZIP contains the uploaded file name. The test timeout is 120s (S3).
- [ ] **Detail downloads.** On the detail page, `download_pdf` returns a non-empty PDF and `download_attachments` returns a ZIP.
- [ ] **Leads.** **Given** the guest leads from P3, **when** the admin filters the leads page by the run's `sc_cfa_<runId>` address, **then** the lead is listed. The test is read-only and asserts on no global counts.
- [ ] **Reports and timeline.** `/application_management/reports/{programId}/{slug}` and `/application_management/timeline/{programId}` load without a PHP error or 403, and the timeline lists at least one action from this run.

### P7 — AI analysis pages (pages-load only, D3) — SAN-1885
- [ ] `/application_management/analysis_list/{programId}` loads (no 403 or PHP error, page heading visible) for the per-run program.
- [ ] `analysis_form` loads and shows its form, and the test **never** submits it.
- [ ] `analysis_cost_dashboard` loads.
- [ ] A network guard (`page.route` on the tenant's analyzer host, or a request listener) **fails the test if any request reaches the analyzer**.
- [ ] Each page test skips with a reason if the AI feature is not enabled for the tenant [INFERRED — requires validation: confirm which flag gates these pages when implementing; no new flag is introduced].

## Per-repo plan

### sc-saas-e2e (only repo edited)
Dependency order: P1 → (P2, P3, P4 in parallel) → P5 (needs P4's seeded R2 submissions helper) → P6 (needs P3 upload + P5 rating) → P7.

- `playwright.config.ts`: add the `cfa-setup`, `cfa` and `cfa-teardown` projects (teardown via `teardown:`).
- `config/accounts.ts` / `config/env.ts`: add `QA_CFA_EMAIL_PATTERN`, `QA_CFA_TEMPLATE_FORM_ID`, `QA_CFA_NDA_PROGRAM_ID` (optional; tests skip when unset). Update `env.example` and the README secrets list.
- `fixtures/cfa.ts`: the `cfaProgram`, `cfaAdmin` and `createCfaProgram()` factory, and the email-log poll helper (extracted from `tests/admin/email-log.spec.ts`).
- `pages/admin/cfa/*`: ProgramWizardPage, FormBuilderPage, SubmissionsTablePage, SubmissionDetailPage, DraftsPage, RoundEditorPage, JuryAllotmentPage.
- `pages/frontend/cfa/*`: ProgramApplyPage, GuestLeadModal, ApplicationStatusPage.
- `pages/jury/*`: JuryRoundApplicationsPage.
- `tests/cfa/{p2-program-setup,p2-form-builder,p3-apply-guest,p3-apply-member,p4-review,p5-jury,p6-downloads,p7-ai-pages}.spec.ts`
- `package.json`: add the devDependencies `xlsx`, `adm-zip`, `@types/adm-zip` (P6), and a `test:cfa` script (`--grep @cfa`).
- README: a "CFA regression suite" section covering prerequisites, the leftover-rows caveat, and the NDA program.

### Follow-ups (app-side data-testid asks — NOT created as issues now)
Each will be a separate, repo-labelled issue later. Until then, page objects use role, label and id selectors.
- **sc-saas-frontend** `program-public-apply.component.html`: `cfa-apply-submit`, `cfa-guest-lead-modal`, `cfa-otp-input`, `cfa-application-status`, `cfa-form-field-{key}`.
- **sc-saas-admin** submission table view: `cfa-row-{submissionId}`, `cfa-move-round-select`, `cfa-bulk-move`, `cfa-reject`, `cfa-tentative`.
- **sc-saas-admin** program wizard: `cfa-make-live`, `cfa-test-mode-toggle`, `cfa-close-applications`.
- **sc-saas-admin** form builder: `fb-add-field-{type}`, `fb-save`.
- **sc-saas-admin** jury round page: `jury-rate-{criteriaId}`, `jury-submit-rating`.

## Contracts & invariants

- **Flags:** read-only. The suite uses five existing cockpit flags (frontmatter), all evidenced in `tenant-users.entity.ts`. It adds, renames and toggles none. Invariant #1 is not touched.
- **API:** consumed only. Any rename of the CFA public routes listed in frontmatter breaks P3. These are backend-owned contracts (invariant #2), so `/audit-contract` on `application-management` and `form-management` should flag `sc-saas-e2e` as a consumer.
- **Admin submitAction contract:** this is not an API in the invariant-#2 sense, but the suite depends on it. The names it uses are:
  - Program: `createApplicationProgram`, `deleteApplicationProgram`, `editProgram`, `editEvaluation`, `makeProgramLive`, `closeProgramApplications`, `reopenProgramApplications`, `closeProgram`, `changeTestMode`
  - Form builder: `saveForm`, `importFieldsFromForm`, `restoreForm`
  - Rounds: `createProgramRound`, `editRound`, `deleteRound`, `freeze_applications`
  - Applications: `import_applications_csv`, `moveToSubmitted`, `deleteApplication`, `moveApplicationToNextRound`, `rejectApplication`, `tentativeApplication`, `removeApplicationFromEvaluation`, `sendForResubmission`, `sendForRoundResubmission`
  - Jury: `add_jury_member`, `add_allotment`, `remove_allotment`, `add_auto_allot_jury`, `addRating`, `answerQuestions`

  The same applies to the GET download route names, the POST field names and the JSON response shape (`error`/`success`/`editUrl`). Renaming any of these in `sc-saas-admin` silently breaks the suite.
- **Events:** none.
- **Invariants at risk:**
  - **#5 tenant scoping:** the suite writes only to the one QA tenant per env, chosen by `E2E_ENV` URLs. It never cross-references another tenant's host, and promotion/outreach (which writes the main tenants DB) is excluded.
  - **#4 auth:** single-session login is respected by reusing the saved `.auth/*.json` states, with no UI login inside a journey (README rule ✔).
  - #1, #2, #3 and #6 are unchanged.

## Cross-Repo Contract Impact

- **Repos edited:** `sc-saas-e2e` only. No application code changes.
- **Repos depended on (read/drive):** `sc-saas-admin` (submitAction + download routes), `sc-saas-frontend` (apply routes, `localStorage['application-{uuid}']` guest identity), `sc-saas-backend` (CFA public API, OTP, freeze guard, email templates, `QA_FIXED_OTP_EMAILS`).
- **Backend env change (ops, not code):** add `sc_cfa_*@yopmail.com` to dev `QA_FIXED_OTP_EMAILS` (D4).
- **Known app bugs the suite encodes:** SAN-1878 (tentative, `test.fail()`).
- **Recommended:** add `sc-saas-e2e` to the consumer list in `sc-saas-backend/src/modules/application-management/module.spec.md` and `sc-saas-admin/modules/application_management/module.spec.md`, so contract audits see it. That is a docs-only follow-up, not part of this spec's edit scope.

## Risks

| Risk | Mitigation |
|---|---|
| Kanban jQuery-UI drag is flaky | All moves go through the table view dropdown or bulk Move, or the `submitAction` request. The kanban is checked for render only. |
| 60s autosave makes draft tests slow and timing-dependent | Use explicit save. Exactly one test waits out autosave, with a 90s timeout. |
| OTP routes are rate-limited (10/60s) | Only one guest test does the real OTP path. The other guest tests use a throwaway program with `bypass_otp_verification`. Logged-in tests skip OTP. Reuse the `LoginPage.requestOtp` 61s back-off pattern. |
| S3-backed ZIPs are slow | Cap at 3 submissions and give those tests a 120s timeout. Bulk ZIPs run serially in P6. |
| Shared-tenant side effects (leads, email logs, S3, notifications accumulate; emails go to yopmail) | `[QA]`/`sc_cfa_` prefixes, no global-count assertions, cleanup via SAN-1613, test mode keeps programs out of public lists, counters and cron. |
| NDA rows block program deletion | NDA tests use only the dedicated long-lived program. |
| Crashed runs leave programs behind | 24h orphan sweep in teardown. |
| No data-testids, so selectors are brittle | Page objects isolate selectors, and the data-testid follow-ups replace them later. |
| A flag is off on a given env | Flag state is read once and dependent tests skip with a reason (never toggled). |
| Admin CSRF-less POSTs could get CSRF protection later | Helpers are centralised in `fixtures/cfa.ts`, so a token can be added in one place. |

## Runtime budget

- **Tier:** regression, run nightly at 02:00 IST on `development` (README CI ✔), plus on demand with `--grep @cfa`. It is not in the per-PR smoke gate, except SAN-1576 journeys 4 and 5.
- **Parallelism:** `fullyParallel: true` with 4 workers in CI (`playwright.config.ts:7,12` ✔). It is parallel-safe because of the per-run program plus per-test applicants. Program- and round-state tests use their own throwaway programs in serial describes.
- **Target:** the CFA slice finishes in ≤ 25 min wall-clock at 4 workers. Rough split: P1 setup/teardown ≤ 1 min, P2 ≤ 5, P3 ≤ 6, P4 ≤ 5, P5 ≤ 4, P6 ≤ 4, P7 ≤ 1. [INFERRED — requires validation: a proposed budget, to be re-measured after P4.]

## Test plan

- sc-saas-e2e: `npm run typecheck`; each new spec file run locally with `--repeat-each=3` against development (README rule ✔); a full `--grep @cfa` run green on development on 3 consecutive nightlies; `npm run test:smoke` stays under 10 min after the SAN-1576 j4/j5 refactor.
- Cross-repo: one on-demand staging run after SAN-1864, SAN-1877 and the `sc_cfa_*` allowlist (if approved for staging) are deployed there.

## Rollout

1. Land P1. Run it on development with `cfa-setup`/`cfa-teardown` only and confirm no leftover program.
2. Add the dev backend env `sc_cfa_*@yopmail.com` (D4) and create the E2E template form and the NDA program on dev.
3. Land P2–P7 incrementally. Each new test is quarantined the same day if flaky (README rule 1 ✔).
4. Repeat the prerequisites on staging and run on demand.
5. Production: nothing runs, because everything is `@write`.

## Out of scope

See "Scope / Out of scope" above.

## Open questions

None. The one open question (backend ignores closed state on CFA apply) was resolved on 2026-10-12:
- **D9:** test it on a dedicated closed program.
- **D10:** filed as SAN-1886, covered by a known-failing test.
