---
type: index
repo: admin
updated: 2026-10-08 # SAN-1467
---

# Admin Module Specs Index

Master index of all `sc-saas-admin` module specs — **69 of 69** `modules/*/` directories now have a
`module.spec.md` (verified 2026-07-19; zero gaps; `email_logs` added 2026-09-30 by FA-009). The admin panel is PHP/Medoo/sparkAdminTpl with
**two DB connections per request**: `$mainDatabase` (tenants DB — reads feature flags, api_url,
per-tenant DB creds) and `$database` (per-tenant client DB — all business data). Plus cURL calls to
`$api_server_url` (sc-saas-backend REST API) and, for a few modules, direct calls to the
`sc-saas-3rdparty-webservices` gateway.

Roughly half the 68 specs (38) were authored 2026-07-17 → 2026-07-19 as part of a full-coverage sweep
that moved the repo from ~30 spec'd directories to all 68, one spec per actual `modules/<dir>/`. Nine
**older, still-valid "combined" specs** predate that sweep and document 2–8 directories' worth of code
under one umbrella file (e.g. `integrations/module.spec.md` covers zoho+aws+filemanager+scrapper+
intellectual_property). Those bundled docs are **not deleted** — they remain useful narrative context —
but every directory they cover now also has its own focused, current spec; treat the one-per-directory
spec as authoritative for that directory's `owns`/`consumes`/`db_access`, and the bundled doc as
supplementary background. Bundled entries are marked **(legacy/combined)** below.

> **How to use:** When working on a module, read its spec first — it records owned files, consumed
> flags, DB connections, known bugs, and security findings surfaced during spec authoring. When adding
> a handler or flag gate, update the spec's `owns` / `consumes` frontmatter and `updated` date.

---

## Foundation

| Module | Spec | Description |
|---|---|---|
| core-bootstrap | [module.spec.md](../sc-saas-admin/module.spec.md) | Dual DB connection setup, tenancy resolution, router, template engine, feature flag loading |
| auth | [module.spec.md](../sc-saas-admin/modules/auth/module.spec.md) | Admin login, session, SSO (Microsoft/Azure), password reset, profile — CSRF on login is commented out |
| ajax-handlers | [module.spec.md](../sc-saas-admin/modules/ajax/module.spec.md) | 7 jQuery AJAX endpoints: api_actions, crud_actions, email_actions, spa_actions, whatsapp_actions, stakeholder_export, fields_mapping |

---

## Stakeholder & Generic CRUD

| Module | Spec | Description |
|---|---|---|
| stakeholder-crud | [module.spec.md](../sc-saas-admin/modules/stakeholder-crud/module.spec.md) | Generic CRUD engine (table.php/add.php/edit.php) for all entity types driven by `spa_data_management` config |

---

## Application Lifecycle (CFA / Venture Studio / Jury)

| Module | Spec | Description |
|---|---|---|
| application_management | [module.spec.md](../sc-saas-admin/modules/application_management/module.spec.md) | Full CFA lifecycle — program creation wizard, round management, submission review, jury evaluation, approve/reject; also covers legacy startup-programs + mentor application flows; FA-011 Limit Jury Access adds the Limit Access pop-up (Round Settings → Jury allotment), round badges, activity + CSV and the admin-only "Preview as juror" page (`jury_visibility_preview`) |
| program-management | [module.spec.md](../sc-saas-admin/modules/program-management/module.spec.md) | PM/corporate-PM dashboards + program creation wizard; mentor round-advance/reject/tentative backend calls |
| jury | [module.spec.md](../sc-saas-admin/modules/jury/module.spec.md) | Jury assignment, per-round scoring dashboards, review of startup/application/mentor/individual submissions; FA-011 server-side hiding of questions on `round-applications.php` (fail closed, 15-minute file links, reviewers get the programme-wide union) |
| challenges | [module.spec.md](../sc-saas-admin/modules/challenges/module.spec.md) | Corporate challenge creation, participant management — details.php JSON comparison bug locks non-super-admin PMs |
| venture-studio | [module.spec.md](../sc-saas-admin/modules/venture-studio/module.spec.md) | VS-specific program management where individuals (not startups) apply and admins form teams from accepted applicants |
| startup-application-management-flow | [flow.spec.md](../sc-saas-admin/modules/startup-application-management-flow.spec.md) | Kanban/table/reports view for a program's applications — 13 AJAX handlers; bulk email; round moves via backend `:adminMd5` API |
| stakeholder-detail-pages | [spec.md](../sc-saas-admin/modules/stakeholder-detail-pages.spec.md) | startup-detail.php (1784 lines, 15+ inline actions incl. ID card auto-gen on approval), application-submission-detail.php, pm_dashboard, mentor/investor detail |

---

## Learning & Events

| Module | Spec | Description |
|---|---|---|
| learning_management | [module.spec.md](../sc-saas-admin/modules/learning_management/module.spec.md) | LMS course + enrollment management; `learning_management` flag not enforced inside handlers; sidebar menu commented out |
| events | [module.spec.md](../sc-saas-admin/modules/events/module.spec.md) | Admin management of the generic multi-format `events` table (webinar/1:1/conference/demo day/etc.) — multi-step edit wizard, attendee approve/reject/reschedule, exhibition floor/booth layout |
| meetings | [module.spec.md](../sc-saas-admin/modules/meetings/module.spec.md) | Admin view of peer-to-peer 1:1 meetings — participant notes, feedback responses, direct VideoSDK session lookup via the 3rdparty gateway (bypassing backend), tenant-wide feedback questionnaire config |
| events-meetings **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/events-meetings/module.spec.md) | Superseded by the `events/` and `meetings/` specs above; kept for narrative background — reject-attendee email API call confirmed commented out |

---

## Community & Connections

| Module | Spec | Description |
|---|---|---|
| community_wall | [module.spec.md](../sc-saas-admin/modules/community_wall/module.spec.md) | Moderation + admin-authored posting for the member social feed — reactions, reports (counted, never actioned), polls with CSV vote export, event-linking |
| connections | [module.spec.md](../sc-saas-admin/modules/connections/module.spec.md) | Admin-side connection moderation — user connection matrix (can_connect/can_search/limit) + global matrix per stakeholder-type pair |
| community-connections **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/community-connections/module.spec.md) | Predates `community_wall`'s split-out spec (missed reactions/reports/polls/event-linking); still the current spec for `connections/`; `connections/index.php` loads ALL connections with no pagination |

---

## Finance & Billing

| Module | Spec | Description |
|---|---|---|
| memberships | [module.spec.md](../sc-saas-admin/modules/memberships/module.spec.md) | Membership lifecycle (create/edit/soft-delete/approve) across all stakeholder types; single-active enforcement; certificate date sync |
| finance_management | [module.spec.md](../sc-saas-admin/modules/finance_management/module.spec.md) | Orders, payments, proforma invoices, coupons, tax + gateway settings — the standalone one-per-directory replacement for half of `finance-memberships` |
| payment_gateways | [module.spec.md](../sc-saas-admin/modules/payment_gateways/module.spec.md) | Gateway enable/disable with live API credential validation; Stripe/Razorpay/Easebuzz/PayPal; plaintext credential storage; duplicate entry point vs. `finance_management/settings/gateways/` |
| tax_management | [module.spec.md](../sc-saas-admin/modules/tax_management/module.spec.md) | Tax profile CRUD (GST/VAT rates applied to payment amounts) |
| ai_credits | [module.spec.md](../sc-saas-admin/modules/ai_credits/module.spec.md) | Admin-facing AI-credits wallet/buy/history/orders/invoice UI; purchases via tenants' `v1/ai-credits/purchase`; reserve/settle/refund logic lives in `includes/ai_credits_functions.php`, called from `application_management`, not from this module |
| finance-memberships **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/finance-memberships/module.spec.md) | Predates the `memberships`/`finance_management`/`payment_gateways`/`tax_management` split; `settings.php` still the documented cross-DB write to tenants DB |
| operation_cost | [module.spec.md](../sc-saas-admin/modules/operation_cost/module.spec.md) | SAN-756/758 (T-RISE). Self-declaration template upload (direct Medoo write) + a minimal claims list whose download action is a genuine REST call into `sc-saas-backend` (not a direct DB read/write) — the one module in this repo that proxies a mutating write to the backend instead of Medoo. Gated on `operational_cost_reimbursement_enabled`. |

---

## Communication & Outreach

| Module | Spec | Description |
|---|---|---|
| broadcast_messages | [module.spec.md](../sc-saas-admin/modules/broadcast_messages/module.spec.md) | Compose + send audience-filtered broadcasts (email / in-app chat / community-wall post); every send logged for audit. `approvals.php`: spoke broadcast approvals, pending-first with an Overdue flag (SAN-1445) |
| command_centre | [command_centre.module.spec.md](../sc-saas-admin/modules/command_centre.module.spec.md) | SAN-1381 admin notification centre: `command_centre.php` queue cards and SLA strip, header bell and sidebar badges, `includes/notification_centre_functions.php` counters (per-permission, NFR-06) and `spa_settings` SLA / escalation keys. Gated by `notification_centre_enabled` |
| email_logs | [module.spec.md](../sc-saas-admin/modules/email_logs/module.spec.md) | FA-009 (SAN-1157). Tenant-wide Email Logs page over `ses_email_queue`: filters (type, template, IST date range, recipient, status), server-side counters, per-row SES status + Request Stats (row loaded by id; POSTed email/messageId ignored), CSV without bodies. Gated by `can_broadcast_messages`, partners/jury redirected, CSV also needs `can_export_data` |
| canned_responses | [module.spec.md](../sc-saas-admin/modules/canned_responses/module.spec.md) | Reusable email templates for the applicant broadcast-email composer; also written to directly from other modules' "save as canned response" checkbox |
| outreach_requests | [module.spec.md](../sc-saas-admin/modules/outreach_requests/module.spec.md) | Cross-tenant/cross-partner program-promotion request system (`program_promotions` lives in the shared tenants DB, not per-tenant) — approve/reject with email notification, optional program clone into the receiving tenant |
| contacts | [module.spec.md](../sc-saas-admin/modules/contacts/module.spec.md) | Generic category-tagged personal/organizational rolodex (vCard/QR export) — distinct from `connections` and from `outreach_requests`' `program_promotions` |
| outreach-communications **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/outreach-communications/module.spec.md) | Predates the split above; also documents WATI/WhatsApp template settings shared with `broadcast_messages` |

---

## Content Management

| Module | Spec | Description |
|---|---|---|
| news | [module.spec.md](../sc-saas-admin/modules/news/module.spec.md) | Curated external "deeptech news" feed (links + blurb); create/edit only, list via generic `table.php` |
| glossary | [module.spec.md](../sc-saas-admin/modules/glossary/module.spec.md) | Term/definition dictionary consumed end-to-end by the PWA (`Feature.GLOSSARY`); smallest module in the repo — create/edit only |
| resource-files | [module.spec.md](../sc-saas-admin/modules/resource-files/module.spec.md) | Live tenant-facing resource library (documents/PDFs) — real cross-repo feature served by `sc-saas-backend/src/modules/resources/`; triggers async S3 thumbnail conversion |
| video_gallery | [module.spec.md](../sc-saas-admin/modules/video_gallery/module.spec.md) | YouTube-embed-only video showcase (`webinars` table) — no upload/transcode despite the "webinar" naming |
| industry_reports | [module.spec.md](../sc-saas-admin/modules/industry_reports/module.spec.md) | Downloadable report content items (upload or external URL); folder name doesn't match underlying `report_downloads` table |
| product_updates | [module.spec.md](../sc-saas-admin/modules/product_updates/module.spec.md) | Changelog/release-notes feed; create/edit only |
| ads-management | [module.spec.md](../sc-saas-admin/modules/ads-management/module.spec.md) | In-app promotional banner CRUD with per-placement filtering and drag-drop position ordering; entirely bespoke, no generic engine |
| startup-booster-kit | [module.spec.md](../sc-saas-admin/modules/startup-booster-kit/module.spec.md) | Vendor/partner service-offer catalog (`startupkit_services`) authoring + submissions dashboard; backend `RolesGuard` gap means non-startup users can currently hit claim endpoints |
| content-management **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/content-management/module.spec.md) | Predates the 8 one-per-directory content specs above; kept as the umbrella narrative for the content-publishing group |

---

## Certificates & ID Cards

| Module | Spec | Description |
|---|---|---|
| certificates | [module.spec.md](../sc-saas-admin/modules/certificates/module.spec.md) | Certificate + ID card issuance (upsert, number generation); no PDF at issuance — frontend renders client-side from `spa_settings` |
| certificate_builders | [module.spec.md](../sc-saas-admin/modules/certificate_builders/module.spec.md) | Visual template designer for certificates across 9 stakeholder types; writes design settings to `spa_settings`, paired with `certificates/` for issuance |
| id_card_builders | [module.spec.md](../sc-saas-admin/modules/id_card_builders/module.spec.md) | Visual template designer for digital ID cards (startup-only, v1) — near-identical twin of `certificate_builders/` |
| id_cards | [module.spec.md](../sc-saas-admin/modules/id_cards/module.spec.md) | Issuance side of the ID-card feature — bulk generate/revoke/reactivate/regenerate, reads defaults from `spa_settings` written by `id_card_builders/` |
| onboarding_design | [module.spec.md](../sc-saas-admin/modules/onboarding_design/module.spec.md) | SAN-250 — per-tenant custom branding editor for all 10 onboarding screens (Login/Signup + 8 profile screens); same builder pattern as `certificate_builders`/`id_card_builders`, gated on `custom_onboarding_design_enabled` (read-only here, written only by `sanchiconnect-saas-tenants-admin`) |

---

## Metrics & Reporting

| Module | Spec | Description |
|---|---|---|
| metric_types | [module.spec.md](../sc-saas-admin/modules/metric_types/module.spec.md) | Create/edit forms for the KPI catalogue (`metric_types`) startups report against; list view lives in the sibling `growth_metrics/metric_types.php` |
| growth_metrics | [module.spec.md](../sc-saas-admin/modules/growth_metrics/module.spec.md) | Reporting/dashboard layer over startup-reported KPI values (`metrics` table) — charts, CSV export, defaulter tracking, edit-request workflow; unrelated to `portfolio_management` despite both keying off `startups` |
| milestones | [module.spec.md](../sc-saas-admin/modules/milestones/module.spec.md) | Read-oriented admin viewer of stakeholder milestone records; authoritative mutation surface is the backend counterpart |
| tickets | [module.spec.md](../sc-saas-admin/modules/tickets/module.spec.md) | Support ticket lifecycle (assign/reply/close/reopen); email delegated to backend; S3 attachments with no file-type validation |
| portfolio_management | [module.spec.md](../sc-saas-admin/modules/portfolio_management/module.spec.md) | Cap-table / equity-investment tracking — 5-step wizard per funding round (Pre Issue → Post Issue → Documents → Rights → Summary); functionally unrelated to `growth_metrics` |
| reporting | [module.spec.md](../sc-saas-admin/modules/reporting/module.spec.md) | Custom BI dashboards backed by stored SQL templates — raw SQL execution with bypassable denylist; highest security risk in admin |
| reporting_backup **(dead code)** | [module.spec.md](../sc-saas-admin/modules/reporting_backup/module.spec.md) | Confirmed stale, orphaned duplicate of `reporting/` from a pre-refactor snapshot — not a backup/DR feature, not routed |
| growth-metrics **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/growth-metrics/module.spec.md) | Predates the growth_metrics/metric_types/milestones/tickets/portfolio_management split; `metric_types.php` writes to tenants DB is the one confirmed cross-DB write |
| reporting-certificates **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/reporting-certificates/module.spec.md) | Predates the reporting/certificates/certificate_builders/id_cards/id_card_builders/form_builder split; kept as the "data to document" umbrella narrative |

---

## Facilities & Partners

| Module | Spec | Description |
|---|---|---|
| facilities | [module.spec.md](../sc-saas-admin/modules/facilities/module.spec.md) | Physical space booking — facility types, availability/pricing/add-ons/images/ratings, booking calendar, kiosk flow; soft-delete writes to both tenants and client DB |
| partners | [module.spec.md](../sc-saas-admin/modules/partners/module.spec.md) | Partner (tenant sub-admin) self-service portal — token-exchange login, own scoped stakeholders/programs/team/photo-gallery, two-layer tenant + partner_id scoping |
| recruitment-partners | [module.spec.md](../sc-saas-admin/modules/recruitment-partners/module.spec.md) | Recruiter-facing job pipeline view gated by an admin role (not a partner-organisation login) — `job_applications.partner_id` actually stores an admin_user_id |
| partner_domain_branding | [spec.md](../sc-saas-admin/modules/partner_domain_branding.spec.md) | SAN-388 Hub/Spoke — Domain & Branding iframe tab on partner-detail.php; sets a partner's Spoke subdomain (`partners.abbreviation`) + white-label branding. Writes `partner_branding` via Medoo (NOT the backend's partner-JWT-only write routes) and pushes the spoke hostname to the cockpit's CORS registry |
| partners-recruitment **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/partners-recruitment/module.spec.md) | Predates the `partners`/`recruitment-partners` split; documents both partner types under one spec |

---

## Form & Data Management

| Module | Spec | Description |
|---|---|---|
| form-management | [module.spec.md](../sc-saas-admin/modules/form-management/module.spec.md) | Custom program-application form builder, versioning (stored as `spa_admin_logs` snapshots), CSV import/export — version restore guard is critical |
| form_builder | [module.spec.md](../sc-saas-admin/modules/form_builder/module.spec.md) | Standalone data-collection forms (`use_form_as = "data_collection"`) distinct from program application forms; `custom_forms` flag defined end-to-end but not enforced in this module or the backend guard |
| document_types | [module.spec.md](../sc-saas-admin/modules/document_types/module.spec.md) | Startup-only supporting-document category registry; separate from `application_program_document_types` and `portfolio_document_types` |
| csv | [module.spec.md](../sc-saas-admin/modules/csv/module.spec.md) | Generic table-driven CSV export/import helper consumed by the shared list-view template; bespoke per-table query logic for 8 profile tables plus a generic fallback for any table |

---

## Integrations & Infrastructure

| Module | Spec | Description |
|---|---|---|
| zoho | [module.spec.md](../sc-saas-admin/modules/zoho/module.spec.md) | Zoho CRM connector — OAuth connect flow, per-module field mapping, custom-field entry; confirmed no Lead/Contact/Account record is ever actually pushed to or pulled from Zoho |
| aws | [module.spec.md](../sc-saas-admin/modules/aws/module.spec.md) | Raw S3 bucket manager (list/create/delete buckets & objects) plus an unlinked ACL-update maintenance script; separate from the generic per-field S3 upload path used across ~30+ other files |
| filemanager **(dead/unfinished)** | [module.spec.md](../sc-saas-admin/modules/filemanager/module.spec.md) | Local-disk file browser; the list-page template doesn't exist (route would fail); `download.php` has no path restriction, no allow-list, no auth check |
| scrapper | [module.spec.md](../sc-saas-admin/modules/scrapper/module.spec.md) | Unauthenticated-by-flag, unreachable-from-sidebar scrapers (Capboard, IESA) plus a `list.php` that opens ad-hoc connections to **every** tenant's DB using tenant_users credentials with no filter on the current tenant |
| intellectual_property | [module.spec.md](../sc-saas-admin/modules/intellectual_property/module.spec.md) | Patent/copyright/trademark/design register with a cross-tenant "connect"/licensing-inquiry workflow and a public India-patent-office scraper; writes to the shared tenants DB (`patents`) |
| upload | [module.spec.md](../sc-saas-admin/modules/upload/module.spec.md) | TinyMCE rich-editor inline image upload endpoint — writes to shared local disk, no per-tenant folder, same-origin check only via HTTP Host header |
| integrations **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/integrations/module.spec.md) | Predates the zoho/aws/filemanager/scrapper/intellectual_property split; kept as the umbrella narrative for third-party/file infrastructure |

---

## System Administration

| Module | Spec | Description |
|---|---|---|
| developer | [module.spec.md](../sc-saas-admin/modules/developer/module.spec.md) | Super-admin config cockpit — DDL, email/WhatsApp config, menu management, form-field/table-view mapping, settings management; now also SAN-315's `location_master_import.php` (SSRF-hardened direct-Medoo countries/states/districts/sub_districts/cities import, no backend route) |
| system_logs | [module.spec.md](../sc-saas-admin/modules/system_logs/module.spec.md) | Read-only viewer over `spa_admin_logs`, populated opportunistically by ~90 modules calling `createAdminLogs()` — no central logging hook; includes an unrouted near-duplicate `list_aditya.php` |
| profile_audit_logs | [module.spec.md](../sc-saas-admin/modules/profile_audit_logs/module.spec.md) | Read-only viewer of backend-written, field-level stakeholder profile change history |
| task_management | [module.spec.md](../sc-saas-admin/modules/task_management/module.spec.md) | Internal ops to-do/ticketing tool for admin staff; backend's `TasksController` is an empty controller with no routes — all real reads/writes happen here via Medoo |
| system-admin **(legacy/combined)** | [module.spec.md](../sc-saas-admin/modules/system-admin/module.spec.md) | Predates the developer/system_logs/profile_audit_logs/task_management split; kept as the umbrella narrative |

---

## Security findings

| Severity | Module | Finding |
|---|---|---|
| 🔴 Critical | system-admin / developer | `database_management.php` constructs DDL from `$_POST['table_name']` — backtick-quoting only, no allowlist |
| 🔴 Critical | auth | Password change skips old-password verification — any active session can change the password |
| 🔴 Critical | auth | Login CSRF protection is commented out |
| 🔴 Critical | reporting | Raw SQL from stored templates executed via PDO; keyword denylist (`INSERT`, `DROP`, etc.) is trivially bypassed via `SELECT...INTO OUTFILE`, `CALL`, `SLEEP(N)` |
| 🔴 Critical | reporting | No item-level auth on `_execute_chart`/`_export_data`/`_drilldown` — any admin guessing an `item_uuid` can pull any widget data regardless of dashboard `allowed_roles` |
| 🔴 Critical | filemanager | `download.php` `readfile()`s the query-string path directly — no path restriction, no allow-list, no auth check of any kind |
| 🟠 High | ajax-handlers | `stakeholder_export.php` has no CSRF check (only handler without it); no ownership validation on startupId |
| 🟠 High | system-admin / developer | `email_management.php` send-email action has CSRF and sanitization commented out |
| 🟠 High | integrations / intellectual_property | `intellectual_property/` writes to tenants DB (`patents`) — cross-tenant blast radius |
| 🟠 High | integrations / scrapper | Capboard scraper has `display_errors=1` never removed — exposes PHP errors in production |
| 🟠 High | auth | Open redirect in backdoor login — `$_GET['redirect_url']` passed to `header(Location:...)` without protocol validation |
| 🟠 High | payment-gateways | Payment credentials (`live_client_id`, `live_client_secret`) stored as plaintext VARCHAR — DB dump exposes all tenant payment keys |
| 🟠 High | payment-gateways | Easebuzz credential validation POSTs a live dummy transaction payload — not a dry-run |
| 🟠 High | payment-gateways | Seed array typo: `live_client_id` appears twice; `live_client_secret` never seeded |
| 🟠 High | tickets | `upload_attachment` has no file-type validation — any file type accepted to S3 |
| 🟠 High | reporting | Export adds `LIMIT 10000` only if no LIMIT present — a template with `LIMIT 99999` can stream all rows unbounded |
| 🟠 High | aws | `acl_update.php` is a standalone, unlinked script that makes every image/document key across ~12 tables `public-read` and dumps the full URL list on execution |
| 🟠 High | scrapper | `list.php` opens ad-hoc Medoo connections to every tenant's DB using tenant_users-sourced credentials with no filter scoping to the current request's tenant — one route, all tenants' data readable |
| 🟠 High | growth_metrics / growth-metrics | Public-metrics bypass in `list.php`/`startup.php` (per 2026-07-18 sweep finding, carried into the new `growth_metrics` spec) — verify current guard before relying on it |
| 🟡 Medium | stakeholder-crud | Raw SQL with unparameterized ID in `table.php` DELETE queries |
| 🟡 Medium | application_management | `memory_limit` set to `6600000000000` — effectively no PHP memory limit |
| 🟡 Medium | community-connections | `connections/index.php` loads ALL connections with no pagination — OOM on large tenants |
| 🟡 Medium | integrations / zoho | WATI access token stored unencrypted in `spa_settings` |
| 🟡 Medium | challenges | `details.php` JSON comparison bug locks all non-super-admin PMs out of challenge details |
| 🟡 Medium | finance-memberships | Payment gateway validation calls third-party APIs synchronously — slow gateway deadlocks PHP process |
| 🟡 Medium | reporting-certificates / reporting | Report template SQL executes raw against live client DB |
| 🟡 Medium | learning_management | `learning_management` flag not enforced inside LMS handlers — accessible by direct URL |
| 🟡 Medium | system-admin / developer | `rename_table` cascade across 8 config tables runs without transaction |
| 🟡 Medium | tickets | `assigned_to_ids` written from `$_POST` without existence check; no CSRF on any ticket action |
| 🟡 Medium | payment-gateways | Duplicate entry point at `finance_management/settings/gateways/` — two paths to same `payment_gateways` table; changes to one may not reflect in the other |
| 🟡 Medium | startup-booster-kit | Backend `StartupKitController` guard chain omits `RolesGuard` — `@Roles(Role.STARTUP)` is inert, any authenticated user can hit `check`/submission endpoints |
| 🟡 Medium | filemanager | `ajax.php` (upload/rename/remove/create_folder) is fully live and independently reachable even though the UI that would drive it (`list.php`'s template) doesn't exist |
| 🟢 Low | system_logs | `list_aditya.php` is an unrouted near-duplicate of `list.php` — dead code, not a security issue but a maintenance trap |
| 🟢 Low | reporting_backup | Confirmed dead code — stale duplicate of `reporting/`, not a real backup/DR mechanism; safe to delete but out of scope here |

Updated: 2026-10-06 (FA-011 Limit Jury Access: application_management + jury rows). Earlier: 2026-07-20

---

## Feature specs and Gap Register

Cross-repo features are specified in `specs/features/` (the workspace layer), not in module specs. The notification-centre family:

- [SAN-1381 Notifications and an Action-Driven Dashboard](features/SAN-1381-notifications-action-driven-dashboard.spec.md) (formerly NOTIF-001). Phase 1; includes the performance measurements and BRD sign-off.
- Phase 2 specs:
  - [SAN-1471 application status updates](features/SAN-1471-application-status-updates.spec.md)
  - [SAN-1472 event reminders](features/SAN-1472-event-reminders.spec.md)
  - [SAN-1475 escalation rules](features/SAN-1475-escalation-rules.spec.md)
  - [SAN-1478 in-app preferences](features/SAN-1478-notification-preferences-in-app.spec.md)
  - [SAN-1481 recommended for you](features/SAN-1481-recommended-for-you.spec.md)
- [BRD §4 baseline queries](features/SAN-1381-baseline-queries.md)

Known gaps (deferred, unverified or risky items) are tracked in the **[Gap Register](gap-register.md)**.
