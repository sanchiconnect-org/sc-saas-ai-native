---
type: index
repo: frontend
updated: 2026-10-08 # SAN-1467
---

# Frontend Module Specs — Index

All 82 directories under `sc-saas-frontend/src/app/modules/` have a `module.spec.md` (30 pre-existing + 52 added 2026-07-19/20). This index maps each directory to its spec, summarises its role, and flags security/quality notes surfaced during spec authoring.

> **How to use:** When working on a module, read its spec first — it records owned routes, Angular modules covered, consumed feature flags, backend modules called, and known footguns. When adding a route or flag gate, update the spec's `flags` / `backend_modules` frontmatter and `updated` date.
>
> **Important distinction — not every directory is a live routed feature.** Several older, broader specs (`hire`, `challenges`, `programs`, `search`, `resources`, `dashboard-v2`, `event-agenda`, `meetings`, `individuals`, `mentors`, `milestones`, `connection-v4`, `partners-dashboard`, `utilities`) are **umbrella specs** written before the finer-grained per-directory specs existed — they describe a group of sibling directories together. Each sibling directory now *also* has its own dedicated, more current `module.spec.md`; treat the umbrella spec as a cross-cutting overview and the per-directory spec as the primary reference for that directory's own routes/flags. Separately, a real handful of directories are **confirmed dead or non-routed**: `public/` and `payment-gateways/` are unreachable in the running app; `static-form-field`, `share-links`, `slider`, `inline-styles-csp`, `public-shared`, `ad-viewer` are real, in-use code but own no route of their own (shared components/libraries consumed by other feature modules). These distinctions are called out per-row below.

---

## Auth & Access

| Module | Spec | Description |
|---|---|---|
| `auth` | [spec](../sc-saas-frontend/src/app/modules/auth/module.spec.md) | Every entry point into/out of the platform: mobile-OTP login, all registration variants, email verification, admin-backdoor-impersonation route mount, email-link connection-request auth flow. Umbrella spec — mounts `admin-actions` and `connection-request-action-email` as sub-routes. `/auth/login`/`/auth/register` route through `custom-onboarding`'s gate components as of SAN-246/247/248. |
| `custom-onboarding` | [spec](../sc-saas-frontend/src/app/modules/custom-onboarding/module.spec.md) | SAN-246/247/248 — per-tenant custom branding for Login, Signup, and the 8 "Create Profile as…" profile screens. New `/onboarding/complete-profile/:screenKey` route (only the `startup` screen wired so far); its `LoginGateComponent`/`SignupGateComponent` are declared by `AuthModule` to avoid a circular NgModule import — see its own spec's "Watch out for". |
| `admin-actions` | [spec](../sc-saas-frontend/src/app/modules/admin-actions/module.spec.md) | **"Backdoor login"** impersonation tool: `GET /backdoor-login/:id/:uuid` silently authenticates as user `:id` using `:uuid` as an md5 secret — no confirmation UI, no `AuthGuard`. See findings table. |
| `connection-request-action-email` | [spec](../sc-saas-frontend/src/app/modules/connection-request-action-email/module.spec.md) | Generic "magic link" landing page for email notification actions (despite the name, handles 8 different deep-link types — connection, profile, message, meeting, mentorship, document, video pitch, growth metrics — not just connections). |
| `connection-approve-reject-page` | [spec](../sc-saas-frontend/src/app/modules/connection-approve-reject-page/module.spec.md) | Public, token-less accept/reject landing page reached from an email link — no login required, no JWT established. |

---

## Account, Team & Individual Profiles

| Module | Spec | Description |
|---|---|---|
| `account` | [spec](../sc-saas-frontend/src/app/modules/account/module.spec.md) | Generic "Account Settings" area (profile, notifications, availability, certificates, ID card, membership/subscription, team, proforma invoices, deactivation) reused across every stakeholder type. |
| `team` | [spec](../sc-saas-frontend/src/app/modules/team/module.spec.md) | Generic team-member roster ("sub-accounts") management, deep-linked from 5+ places across multiple account types — not owned by any single stakeholder type. |
| `individuals` | [spec](../sc-saas-frontend/src/app/modules/individuals/module.spec.md) | Umbrella spec covering `individual-profile` + `team` together; see those two specs individually for current detail. |
| `individual-profile` | [spec](../sc-saas-frontend/src/app/modules/individual-profile/module.spec.md) | Self-service portal for the `INDIVIDUAL` account type — dashboard, intro/bio editing, custom forms, public profile. Mirrors the corporate/mentor pattern but smaller (single combined edit form). |

---

## Stakeholder Self-Service Portals

| Module | Spec | Description |
|---|---|---|
| `startups` | [spec](../sc-saas-frontend/src/app/modules/startups/module.spec.md) | Full startup self-service portal: profile lifecycle, all pitch-deck variants, supporting docs, dashboard, fund-raise toggle, compare tool, approval flow. |
| `investors` | [spec](../sc-saas-frontend/src/app/modules/investors/module.spec.md) | Investor self-service portal (org + individual investor variants), profile editing, comparison tool, "providing funding" toggle. |
| `corporate` | [spec](../sc-saas-frontend/src/app/modules/corporate/module.spec.md) | Corporate user self-service portal: dashboard, intro/engagement editing, approval request, public profile. |
| `mentors` | [spec](../sc-saas-frontend/src/app/modules/mentors/module.spec.md) | Umbrella spec: mentor self-service portal + the `tracker` (mentorship-hours) module together. |
| `partners` | [spec](../sc-saas-frontend/src/app/modules/partners/module.spec.md) | Thin module: public partner listing/directory page (`/partners`) only — deeper partner self-service lives in `partners-dashboard`. |
| `partners-dashboard` | [spec](../sc-saas-frontend/src/app/modules/partners-dashboard/module.spec.md) | Umbrella spec: authenticated partner self-service hub (`partners-dashboard/`) + public partner-profile detail page (`partners-details/`) together. |
| `partners-details` | [spec](../sc-saas-frontend/src/app/modules/partners-details/module.spec.md) | Public read-facing profile page for a single partner org (`/partners/:partnerId/:name`) — description, industries, startups, events, contact form. |
| `service-provider` | [spec](../sc-saas-frontend/src/app/modules/service-provider/module.spec.md) | Service-provider stakeholder self-service portal, gated entirely behind the `service_providers` flag. |
| `program-office` | [spec](../sc-saas-frontend/src/app/modules/program-office/module.spec.md) | Self-service portal for the "program office" (incubator/accelerator staff) account type — structurally a clone of the mentor/corporate/investor pattern. |
| `program-office-team` | [spec](../sc-saas-frontend/src/app/modules/program-office-team/module.spec.md) | Standalone team-listing page for program-office accounts — genuinely separate from `team/` (different backend endpoints, under the `partners/` route prefix). |

---

## Jobs

| Module | Spec | Description |
|---|---|---|
| `hire` | [spec](../sc-saas-frontend/src/app/modules/hire/module.spec.md) | Umbrella spec for the full job-board domain: posting/managing jobs (employer side) + search/apply/track (job-seeker side). |
| `job-search` | [spec](../sc-saas-frontend/src/app/modules/job-search/module.spec.md) | Public/authenticated job browse-and-filter listing (`/search/jobs`) — no account-type gating on the route itself. |
| `job-details` | [spec](../sc-saas-frontend/src/app/modules/job-details/module.spec.md) | **Not** a job-seeker view — the employer/poster's applicant-management console for one job posting (shortlist/reject/schedule interview). |
| `job-public-details` | [spec](../sc-saas-frontend/src/app/modules/job-public-details/module.spec.md) | Public, shareable job-detail page with "Apply Now" — reachable unauthenticated despite using the protected layout shell. |
| `job-interview` | [spec](../sc-saas-frontend/src/app/modules/job-interview/module.spec.md) | The live VideoSDK interview room — destination of `job-details`'s "Go To Meeting" link, plus an auto-saved personal-notes panel. |
| `applied-jobs` | [spec](../sc-saas-frontend/src/app/modules/applied-jobs/module.spec.md) | Job seeker's own application history ("My Applied Jobs") + upcoming-interviews panel — the account-holder-facing counterpart to `job-details`. |

---

## Business Challenges

| Module | Spec | Description |
|---|---|---|
| `challenges` | [spec](../sc-saas-frontend/src/app/modules/challenges/module.spec.md) | Umbrella spec: full challenge lifecycle (corporate creates/manages, startups discover/apply/track) across all challenge sub-modules. |
| `challenge-details` | [spec](../sc-saas-frontend/src/app/modules/challenge-details/module.spec.md) | Corporate/poster-side detail view of one challenge — full description + list of applicant startups. |
| `challenge-search` | [spec](../sc-saas-frontend/src/app/modules/challenge-search/module.spec.md) | Public browse/filter listing at `/search/challenges` — no collections concept (compare `challenge-public-view`). |
| `challenge-public-details` | [spec](../sc-saas-frontend/src/app/modules/challenge-public-details/module.spec.md) | Applicant-facing detail view + Apply flow — the mirror of `challenge-details` for the same `IChallenges` record. |
| `challenge-public-view` | [spec](../sc-saas-frontend/src/app/modules/challenge-public-view/module.spec.md) | Public browse/landing page at `/search_challenges` — functionally like `challenge-search` but adds collection-filter checkboxes and deep-links into `challenge-collection`. |
| `challenge-collection` | [spec](../sc-saas-frontend/src/app/modules/challenge-collection/module.spec.md) | Dedicated landing page for one challenge collection, reached as a deep link from `challenge-public-view`. |

---

## Programs & Application Forms

| Module | Spec | Description |
|---|---|---|
| `programs` | [spec](../sc-saas-frontend/src/app/modules/programs/module.spec.md) | Umbrella spec: three parallel program tracks (`programs`, `vs-programs`, `call-for-applications`) plus `program-office`/`program-office-team`. `/programs` root hard-redirects to `/call-for-applications` (legacy). |
| `vs-programs` | [spec](../sc-saas-frontend/src/app/modules/vs-programs/module.spec.md) | Venture-studio programs browse/apply/track flow for `ACCOUNT_TYPE.INDIVIDUAL` — structurally near-identical to `programs`/`call-for-applications` but its own backend collection. |
| `call-for-applications` | [spec](../sc-saas-frontend/src/app/modules/call-for-applications/module.spec.md) | Unified applicant-facing surface merging three program types (Startup Programs, VS-Programs, CFA) into one "Apply to Programs" experience — status `approved`. |
| `dynamic-forms` | [spec](../sc-saas-frontend/src/app/modules/dynamic-forms/module.spec.md) | Dynamic-form rendering engine for admin-configured forms — both a routed feature (preview/submit pages) and a shared component library imported by ~15 other modules. |
| `static-form-field` | [spec](../sc-saas-frontend/src/app/modules/static-form-field/module.spec.md) | **Not a routed feature** — a single standalone component (`app-static-form-field`), a hardcoded 4-field preview form used only inside `dynamic-forms`'s preview mode. |

---

## Events, Meetings & Calendar

| Module | Spec | Description |
|---|---|---|
| `event-agenda` | [spec](../sc-saas-frontend/src/app/modules/event-agenda/module.spec.md) | Umbrella spec: authenticated event-agenda view + public unauthenticated event-registration page (`public-events`) + YouTube webinar catalog (`webinars`). |
| `public-events` | [spec](../sc-saas-frontend/src/app/modules/public-events/module.spec.md) | Unauthenticated event-registration landing page for external share links — no login required to view or register. |
| `webinars` | [spec](../sc-saas-frontend/src/app/modules/webinars/module.spec.md) | **Not** a live-webinar feature despite the name — a YouTube-embed-only video showcase; no scheduling, no live streaming. |
| `meetings` | [spec](../sc-saas-frontend/src/app/modules/meetings/module.spec.md) | Umbrella spec: the in-meeting VideoSDK experience + feedback form + job-interview meeting management, alongside `calender`. |
| `calender` | [spec](../sc-saas-frontend/src/app/modules/calender/module.spec.md) | "My Meetings" scheduling hub (note: directory/route/class names are all spelled "calender", a typo baked in throughout). Full calendar, notes, availability, separate platform-events calendar. |

---

## Communication & Social

| Module | Spec | Description |
|---|---|---|
| `chat` | [spec](../sc-saas-frontend/src/app/modules/chat/module.spec.md) | In-app messaging — two distinct chat implementations selected at runtime by the `chat_type` setting (CometChat SDK vs. in-house REST+socket chat). |
| `community-feed` | [spec](../sc-saas-frontend/src/app/modules/community-feed/module.spec.md) | Member-facing social feed + notification inbox: posts, polls, reactions, comments, real-time push over Socket.IO. |
| `notifications` | [spec](../sc-saas-frontend/src/app/modules/notifications/module.spec.md) | Notification feed + navbar badge count, kept accurate via REST poll + WebSocket event, lazy-loaded. With `notification_centre_enabled`, it adds the SAN-1381 notification centre: NgRx `counters`, header/sidebar bell (`notification-bell`), `count-badge` (red/orange/outlined, WCAG AA), `QualifyingVisitService` (3 s rule), and filtered badge landing. |
| `connection-v4` | [spec](../sc-saas-frontend/src/app/modules/connection-v4/module.spec.md) | Umbrella spec: current active connections experience — wraps `connections-v3` (typed list sub-view) and `connection-approve-reject-page` (email-link flow). |
| `connections-v3` | [spec](../sc-saas-frontend/src/app/modules/connections-v3/module.spec.md) | Full-featured connections list UI (master-detail, vCard export, QR sharing, instant-meeting) — reused as a sub-view inside `connection-v4`, not a standalone top-level route. |
| `connections` | [spec](../sc-saas-frontend/src/app/modules/connections/module.spec.md) | Legacy shared-types-only directory — a single model file (`connections.model.ts`), no component, no route. |

---

## Content & Discovery

| Module | Spec | Description |
|---|---|---|
| `search` | [spec](../sc-saas-frontend/src/app/modules/search/module.spec.md) | Umbrella spec: paginated search across 9 stakeholder types + global search page + IP/patent search. |
| `global-search-page` | [spec](../sc-saas-frontend/src/app/modules/global-search-page/module.spec.md) | Single platform-wide search-results page (`/global-search`) — fans out across every enabled entity type + content types; publicly reachable (no `AuthGuard`). |
| `ip-search` | [spec](../sc-saas-frontend/src/app/modules/ip-search/module.spec.md) | Cross-tenant "IP Hub" patent browse-and-search — sends "Contact"/connect requests that land in the `ip-request` inbox. |
| `ip-request` | [spec](../sc-saas-frontend/src/app/modules/ip-request/module.spec.md) | The requester-facing inbox for IP/patent connection requests originating from `ip-search` — list + message-thread detail view. |
| `resources` | [spec](../sc-saas-frontend/src/app/modules/resources/module.spec.md) | Umbrella spec grouping five read-heavy content modules: `resources`, `glossary`, `product-updates`, `deeptech-news`, `startup-kit`. |
| `glossary` | [spec](../sc-saas-frontend/src/app/modules/glossary/module.spec.md) | Public-facing finance/business term glossary — index + per-term detail, frontend counterpart to `sc-saas-admin`'s `glossary` module. |
| `deeptech-news` | [spec](../sc-saas-frontend/src/app/modules/deeptech-news/module.spec.md) | End-user deep-tech "News" section, gated by `deeptech_news`. Two UIs exist (old simple list + newer preference-driven feed); only the latter is actually routed. |
| `product-updates` | [spec](../sc-saas-frontend/src/app/modules/product-updates/module.spec.md) | End-user "Platform updates" changelog feed inside the account-settings shell — no client-side flag gate observed. |
| `resource-reports` | [spec](../sc-saas-frontend/src/app/modules/resource-reports/module.spec.md) | "Reports" section — downloadable resource cards filterable by industry, gated by `reports_downloads`. |
| `startup-kit` | [spec](../sc-saas-frontend/src/app/modules/startup-kit/module.spec.md) | Public "Startup Booster Kit" vendor-offer catalogue — routing-only wrapper around components physically in `modules/public/`. See findings table for the inert `@Roles(STARTUP)` backend guard. |
| `market-insights` | [spec](../sc-saas-frontend/src/app/modules/market-insights/module.spec.md) | A static navigation shell embedding external PowerBI report iframes — makes **zero** backend calls, has no NgRx state and no service layer; not a data module in the usual sense, and there is no corresponding admin module or feature flag reserved for it. |

---

## Learning Management (LMS)

| Module | Spec | Description |
|---|---|---|
| `learning-management` | [spec](../sc-saas-frontend/src/app/modules/learning-management/module.spec.md) | Course catalogue, enrollment (STARTUP-only), HLS video playback, quizzes with server-side grading, reviews — gated by `learning_management`. See findings table for the unauthenticated HLS-URL backend endpoint. |

---

## Dashboards & Metrics

| Module | Spec | Description |
|---|---|---|
| `dashboard-v2` | [spec](../sc-saas-frontend/src/app/modules/dashboard-v2/module.spec.md) | Umbrella spec: main role-aware home dashboard + growth-metrics reporting (`growth-matrics`/`growth-matrics-print`) + `market-insights`. |
| `growth-matrics` | [spec](../sc-saas-frontend/src/app/modules/growth-matrics/module.spec.md) | Startup KPI submission (monthly/quarterly), table/chart views, sharing with connections or external invitees by email; other stakeholder types use the same page to review, not submit. |
| `growth-matrics-print` | [spec](../sc-saas-frontend/src/app/modules/growth-matrics-print/module.spec.md) | Print/export-optimized, query-param-driven rendering of the same growth-metrics data — target of the "Print" button and shareable read-only links; can auto-trigger `window.print()`. |

---

## Finance & Payments

| Module | Spec | Description |
|---|---|---|
| `payment` | [spec](../sc-saas-frontend/src/app/modules/payment/module.spec.md) | Umbrella spec: gateway selection/checkout, coupons, order listing, membership subscription+upgrade, proforma invoices — the shared `CheckoutModule` widget is embedded across 4+ other feature modules. |
| `payment-gateways` | [spec](../sc-saas-frontend/src/app/modules/payment-gateways/module.spec.md) | **DEAD CODE — confirmed unreachable.** No `loadChildren` entry anywhere; calls hardcoded `localhost:3000` directly (bypasses `apiUrl`/`ApiEndpointService` entirely). Prototype/spike for PayPal/Stripe/Razorpay never wired up. |
| `membership` | [spec](../sc-saas-frontend/src/app/modules/membership/module.spec.md) | Two independent, non-code-sharing surfaces: the standalone `/membership` plan-picker page, and a reusable upgrade/renewal form embedded at `/account/edit/membership`. |
| `operational-cost-reimbursement` | [spec](../sc-saas-frontend/src/app/modules/operational-cost-reimbursement/module.spec.md) | SAN-756/757/758 (T-RISE, Tripura). 12-month eligibility grid + category preview, Month-1-only claim form. Gated on `operational_cost_reimbursement_enabled`; hard-redirects to `/errors/404` when off (mirrors `TrackerComponent`). |

---

## Facilities

| Module | Spec | Description |
|---|---|---|
| `facilities-management` | [spec](../sc-saas-frontend/src/app/modules/facilities-management/module.spec.md) | Full bookable-space lifecycle: catalogue, availability, bookings, authenticated + kiosk/QR check-in, ratings, plus the ecosystem (cross-tenant) listing route. |
| `external-facilities-management` | [spec](../sc-saas-frontend/src/app/modules/external-facilities-management/module.spec.md) | Satellite module for the cross-tenant "ecosystem" facility catalogue — its own route renders `FacilitycommonComponent` from the sibling `facilities-management` module, not its own component. `AuthGuard` is commented out on the route. |

---

## Support & Tracking

| Module | Spec | Description |
|---|---|---|
| `milestones` | [spec](../sc-saas-frontend/src/app/modules/milestones/module.spec.md) | Umbrella spec: startup goal-tracking (`milestones`) + member support-ticket system (`tickets`) — two independently-flagged, unrelated features grouped in one spec. |
| `tickets` | [spec](../sc-saas-frontend/src/app/modules/tickets/module.spec.md) | Support-ticket submission/tracking with threaded conversation with the admin team — same tables documented from the admin side in `sc-saas-admin/modules/tickets/`. |
| `tracker` | [spec](../sc-saas-frontend/src/app/modules/tracker/module.spec.md) | Implements **Mentor Hours** (log/approve/reject/rate mentoring sessions) — the name is historical/misleading, not a general activity tracker. |

---

## Pitch Deck

| Module | Spec | Description |
|---|---|---|
| `pitch-deck-management` | [spec](../sc-saas-frontend/src/app/modules/pitch-deck-management/module.spec.md) | Manages a startup's pitch video across 3 modes (PowerPitch live video, PowerPitchDeck Loom embed, raw upload) for 3 document types (fundraising/hiring/sales pitch). |
| `pitch-deck-recorder` | [spec](../sc-saas-frontend/src/app/modules/pitch-deck-recorder/module.spec.md) | Older in-app webcam pitch-recording flow (native `MediaRecorder`, not Loom). **Currently unreachable in practice** — its host page (`complete-profile`) is itself unrouted, and the module's own `record` child route is never registered. |

---

## Certificates & ID Cards

| Module | Spec | Description |
|---|---|---|
| `cerificates` | [spec](../sc-saas-frontend/src/app/modules/cerificates/module.spec.md) | Single-page "public verify" surface (`/certificate/verify`) — anyone can type a certificate number and check validity. Note: directory is misspelled "cerificates" (missing a "t"). |
| `sc-certificate-renderer` | [spec](../sc-saas-frontend/src/app/modules/sc-certificate-renderer/module.spec.md) | Renders the visual certificate face (6 themes) — live mode (real cert, backend fetch) and admin-preview mode (query-param-driven, zero backend calls). |
| `sc-id-card-renderer` | [spec](../sc-saas-frontend/src/app/modules/sc-id-card-renderer/module.spec.md) | Renders the digital ID card face (4 layouts) — mirrors `sc-certificate-renderer`'s architecture exactly, including the live/preview dual-mode pattern. |

---

## Non-routed Shared Components & Libraries

These directories own no route of their own — they are real, in-use component libraries consumed by other feature modules.

| Module | Spec | Description |
|---|---|---|
| `ad-viewer` | [spec](../sc-saas-frontend/src/app/modules/ad-viewer/module.spec.md) | Dumb presentational component (`<app-ad-viewer [placement]="...">`) rendering promotional banner ads at named placements app-wide — frontend consumer of `sc-saas-admin`'s `ads-management` module. No route, no page. |
| `share-links` | [spec](../sc-saas-frontend/src/app/modules/share-links/module.spec.md) | Generic "share this on social media" widget — no `.module.ts` of its own; declared/exported by `public-shared`. |
| `slider` | [spec](../sc-saas-frontend/src/app/modules/slider/module.spec.md) | Generic image/content carousel built on `swiper/angular` — a real `NgModule` but declares no routes; imported by other feature modules that need a carousel. |
| `inline-styles-csp` | [spec](../sc-saas-frontend/src/app/modules/inline-styles-csp/module.spec.md) | Root-level CSP-nonce shim for Angular's inline component-style injection, eagerly imported into `AppModule`. See findings table — the nonce is a **hardcoded static string**, providing no real protection. |
| `public-shared` | [spec](../sc-saas-frontend/src/app/modules/public-shared/module.spec.md) | Shared-declarations/exports barrel (declares `ShareLinksComponent`/`WindowComponent`, re-exports common Angular modules) consumed by `public`, `resources`, `glossary`, `startup-kit`. |
| `page-not-found` | [spec](../sc-saas-frontend/src/app/modules/page-not-found/module.spec.md) | The app's 404 page (`/errors/404`) — a Lottie animation with no logic; target of multiple wildcard/fallback redirects. |

---

## Dead / Confirmed Unrouted

| Module | Spec | Description |
|---|---|---|
| `public` | [spec](../sc-saas-frontend/src/app/modules/public/module.spec.md) | **Dead scaffolding, not a routed feature.** `PublicRoutingModule`'s route array is `children: []`, and neither it nor `PublicModule` is imported anywhere (confirmed by repo-wide grep). Repurposed as a shared component *library* — its ~40 components (glossary, resources, startup-kit, auth/profile modals, job-application modals) are imported directly into other routed modules' own `declarations`. Its FAQ section components are fully unused even as a library. |

(`payment-gateways` is also confirmed dead — listed under Finance & Payments above, alongside its own findings-table entry.)

---

## Legacy Umbrella Spec

| Module | Spec | Description |
|---|---|---|
| `utilities` | [spec](../sc-saas-frontend/src/app/modules/utilities/module.spec.md) | Pre-existing umbrella spec grouping `dynamic-forms`, `static-form-field`, `sc-certificate-renderer`, `sc-id-card-renderer`, `cerificates`, `public`, `public-shared`, `share-links`, `slider`, `inline-styles-csp`, `page-not-found`, and `shared/booth-display` (outside `modules/`). Each of those now also has its own dedicated, more current spec listed above — use this one for the cross-cutting "why are these grouped" narrative only. |

---

## Infrastructure (outside `src/app/modules/` — not part of the 82, not reverified this pass)

| Module | Spec | Description |
|---|---|---|
| `core` | [spec](../sc-saas-frontend/src/app/core/module.spec.md) | `CoreModule`, `HttpInterceptorModule`, `ServiceModule`, `StateModule` (38 NgRx effects) — the app's service/state backbone. |
| `shared` | [spec](../sc-saas-frontend/src/app/shared/module.spec.md) | `SharedModule`, `PipesModule` — cross-cutting presentation/utility components (including `booth-display`, referenced from `utilities`). |

---

## Security / bug findings summary (surfaced by spec authoring)

These findings were captured in module `Watch out for` sections. They are **not fixed here** — they are documented for awareness and prioritisation.

| Severity | Module | Finding |
|---|---|---|
| 🔴 Critical | `admin-actions` | `/backdoor-login/:id/:uuid` has zero confirmation UI and no `AuthGuard` — anyone with a valid link silently takes over that user's session (httpOnly cookie set on load). Treat a leaked backdoor-login link as equivalent to a leaked session token. Also: `loginBackdoor()`'s post-login redirect only branches STARTUP vs. everything-else, so non-startup/investor account types land on the wrong dashboard after impersonation. |
| 🔴 Critical | `learning-management` | `GET videos/:id/hls-url` has no `@Features` or `JwtAuthGuard` on the backend — any caller who knows a `videoAssetId` retrieves a signed CloudFront HLS URL without auth. Frontend nav guard is the only access control. |
| 🔴 Critical | `payments` | Nearly all backend payment routes have `JwtAuthGuard` commented out — no server-side identity check on order creation, coupon verification, or transaction recording. |
| 🔴 Critical | `payment-gateways` | Confirmed dead but instructive: calls hardcoded `localhost:3000` for Stripe/PayPal/Razorpay and embeds a test Stripe publishable key in source — must never be wired up as-is. |
| 🟠 High | `inline-styles-csp` | The CSP nonce stamped onto every Angular-injected `<style>` tag is a **hardcoded static string literal** (`'random-csp-nonce'`), not generated per-request. A nonce's entire security value is unpredictability — this implementation gives a false sense of protection against inline-style injection under a nonce-based CSP. |
| 🟠 High | `startup-kit` | `POST/GET public/startup-kit/service/:serviceUUID/check` and `.../:serviceUUID` carry `@Roles(Role.STARTUP)` on the backend but **no `RolesGuard` in the guard chain** — the role restriction is inert. Frontend-side redirect-if-`startup_kit`-disabled check is also commented out, so a disabled flag doesn't currently hide or block the route at all. |
| 🟠 High | `external-facilities-management` | Route wrapper (`FacilitycommonComponent`) has `AuthGuard` commented out — unauthenticated users can reach the ecosystem (cross-tenant) facility listing. |
| 🟠 High | `auth` | OTP verify sends `code` as an md5 hash (`login/verify`, `auth-external/login/verify/import`, `otp_verifications/verify*`) — must match backend storage format exactly; a known bug in the verifications module means verification always fails unless the client sends md5. |
| 🟠 High | `meetings` | `/meeting/:meetingId` has no `AuthGuard` — intentionally accessible via emailed link, but the backend's matching public route also has no `JwtAuthGuard`, exposing the full meeting entity to any caller with the UUID. |
| 🟠 High | `jobs` (`job-search`/`job-public-details`) | `public/resumes/submit` and `public/resumes/upload` are fully unauthenticated on the backend — rate-limited only; frontend sends no auth header. |
| 🟠 High | `payment` | Membership routes (`history`, `last`, `types`) are unauthenticated on the backend — any caller who knows `profileType` + `profileId` can read membership history. |
| 🟠 High | `payment` | `getProformaInvoiceHtml` returns raw HTML injected via `[innerHTML]` + `DomSanitizer.bypassSecurityTrustHtml` — only safe if the backend sanitises content first. |
| 🟡 Medium | `core` | `GlobalService` calls multiple unauthenticated backend reference-data/news endpoints with no client-side tenant-scoping check — correct tenant is resolved at cockpit bootstrap, but a stale `apiUrl` in localStorage could point to the wrong tenant. |
| 🟡 Medium | `startups` | `logout_on_rejection` side-effect runs inside a 1-second `setTimeout` on every completeness poll — high polling frequency causes a visible toast-before-logout race. |
| 🟡 Medium | `job-interview` | `/job-interview/:id` has no layout shell wrapper at all — no navbar/sidebar, global layout styles don't apply; guard is also absent. |
| 🟡 Medium | `hire`/`job-details` | `PATCH jobs/hiring-profile` is a no-op on the backend (service body commented out) — frontend call returns 200 but nothing persists. |
| 🟡 Medium | `community-feed` | No Angular `FeatureGuard` on community routes — backend enforces `community_feed`, but the nav item isn't hidden before the network call fires if the flag is off. |
| 🟡 Medium | `calender`/`meetings` | `getCalenderAvilablity()` returns hardcoded static data, not a live API call — easily confused with `getUsersAvailability()`, which calls the real endpoint. `EditMeetingComponent`, `DeleteMeetingComponent`, `MeetingDetailsModalComponent` are commented out of `CalenderModule` declarations/exports — present on disk but unusable until uncommented. |
| 🟡 Medium | `dynamic-forms`/`utilities` | `savePublicFormsSubmission()` in `FormManagementService` has a `console.log(payload)` left in the production code path. |
| 🟡 Medium | `search`/`global-search-page` | `/global-search` relies on the `elastic_search` flag but has no Angular `FeatureGuard` on the route. |
| 🟡 Medium | `chat` | Two conversation-management backend calls (`update-admin`, whole-conversation `DELETE`) are referenced by comment/convention but have no corresponding frontend method at all — `createConversation()` itself is entirely commented-out dead code. |
| 🟡 Medium | `pitch-deck-recorder` | Confirmed unreachable in the running app today: its host page (`complete-profile`) is itself unrouted, and the module's own `record` child route is never registered (`RouterModule.forChild(routes)` commented out) — correctly-wired but dead code, not orphaned. |

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
