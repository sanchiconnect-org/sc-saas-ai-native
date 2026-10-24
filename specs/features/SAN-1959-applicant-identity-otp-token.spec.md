---
id: SAN-1959
title: Applicant identity via email OTP — short-lived applicant token for public call-for-applications routes
type: feature
status: approved
linear: https://linear.app/sanchiconnect/project/sanchi-connect-recovery-engineering-cccf66100c15
linear_milestone: SAN-1959 — Applicant identity via email OTP
owner: nirmal.s@sanchiconnect.com
repos: [backend, admin, frontend, sc-saas-e2e]   # dependency order
contracts:
  api:
    - "POST api/v1/public/otp_verifications/verify — request gains optional applicantProgramUUID; response data gains applicantToken + applicantTokenExpiresAt (additive)"
    - "POST api/v1/public/otp_verifications/send — per-email limit (429) added; shape unchanged"
    - "NEW POST api/v1/application-programs-management/admin/applicant-token — AdminTokenGuard; body { submissionId }; returns { applicantToken, applicantTokenExpiresAt, email, programUUID, programCode }"
    - "POST api/v1/public/forms-management/submission/:formUUID/submit — response data gains applicantToken + applicantTokenExpiresAt when a bypass-OTP program row is created without a token (additive)"
    - "NEW request header x-applicant-token (optional) accepted on the 21 routes below"
    - "DELETE api/v1/application-programs-management/delete-document/:id — applicant-or-owner"
    - "PUT    api/v1/application-programs-management/update-document/:id — applicant-or-owner; approvalStatus other than 'submitted' refused"
    - "POST   api/v1/application-programs-management/submit-document — applicant-or-owner"
    - "POST   api/v1/application-programs-management/:programUUID/upload-document — applicant-or-owner"
    - "POST   api/v1/application-programs-management/:programUUID/check_application_status/:email — applicant-or-owner"
    - "POST   api/v1/application-programs-management/:programUUID/check_application_status/:email/details — applicant-or-owner"
    - "POST   api/v1/application-programs-management/check_application_status_multiple — applicant-or-owner"
    - "POST   api/v1/application-programs-management/applied/:email — applicant-or-owner"
    - "GET    api/v1/application-programs-management/fetch-documents/:programId/:submissionId/:roundId? — applicant-or-owner"
    - "GET    api/v1/application-programs-management/fetch-documents-rejected/:programId/:submissionId — applicant-or-owner"
    - "POST   api/v1/application-programs-management/:programUUID/:submissionId/apply — applicant-or-owner"
    - "GET    api/v1/users/profile-data/guest/:email — applicant-or-owner"
    - "GET    api/v1/payments/round-pricing/:moduleType/:moduleTypeId/:moduleTypeSubId/:userId — applicant-or-owner when moduleType=application_programs"
    - "GET    api/v1/payments/verify/:moduleType/:moduleTypeId/:userId/:moduleTypeSubId? — applicant-or-owner when moduleType=application_programs"
    - "GET    api/v1/payments/previous_order/:moduleType/:moduleTypeId/:userId — applicant-or-owner when moduleType=application_programs"
    - "GET    api/v1/payments/applicant_payments/:moduleType/:moduleTypeId/:userId — applicant-or-owner when moduleType=application_programs"
    - "POST   api/v1/power-pitch/connect/call-for-applications — applicant-or-owner"
    - "POST   api/v1/public/forms-management/submission/:formUUID/fetch — applicant-or-owner when the form belongs to an application program"
    - "POST   api/v1/public/forms-management/submission/:formUUID/submit — applicant-or-owner when the form belongs to an application program"
    - "POST   api/v1/public/forms-management/submission/:formUUID/upload-file — applicant-or-owner when the form belongs to an application program"
    - "POST   api/v1/forms-management/submission/:submissionId/cfa/upload-pitch-document — applicant-or-owner"
  flags: []
  events: []
tenant_scoped: true
depends_on: []
created: 2026-10-22
---

# Applicant identity via email OTP

## Problem

Public call-for-applications (CFA) applicants have no account. The backend identifies them by an **email address alone**, and the document routes identify nothing at all:

- **Anyone can delete or rewrite any applicant's documents.** `DELETE .../delete-document/:id` and `PUT .../update-document/:id` have no auth guard and no ownership check, and ids are sequential (`application-program.controller.ts:621`, `:641`; service `application-program.service.ts:1716-1763`). Evidenced.
- **Anyone can approve a document.** `PUT update-document/:id` writes `approvalStatus` from the body (`update-document-submissionId.dto.ts:6-9`, enum `submitted|accepted|rejected`, `enum.ts:1062-1066`; written at `application-program.service.ts:1755-1756`). So an applicant, or anyone, can mark a document `accepted`. Evidenced. The only caller sends `submitted` (`dynamic-upload-documents.component.ts:158`).
- **The status route hands out submission ids.** `POST .../:programUUID/check_application_status/:email/details` returns round status, name, email and `submissionId` to anyone who knows the email (`application-program.controller.ts:409`, service `:1345-1411`). Checking that a document belongs to a `submissionId` adds nothing while this route stays open.
- **The guest form routes are keyed by email.** `public/forms-management/submission/:formUUID/fetch` returns the newest application of that email for that form. `.../submit` overwrites the newest row of that email, or any row named by `submissionId` in the body (`form-management.service.ts:402-547`, `public-form-management.controller.ts:44`, `:69`). Evidenced.
- **The submit body is trusted for privileged fields.** It accepts:
  - a client-supplied `userId`, which links the row to that member account (`public-form-submission.dto.ts:44-50`, used at `form-management.service.ts:532-547`);
  - `isBackdoor`, which overwrites the answers of a submitted data-collection form (`public-form-submission.dto.ts:96-99`, `form-management.service.ts:573-583`).
- **The same email-only identity reaches more routes.** They are:
  - the guest prefill (`users/profile-data/guest/:email`, which returns every answer, `user.service.ts:1395-1484`);
  - the CFA payment lookups;
  - the apply route;
  - the pitch-document upload;
  - PowerPitch connect, which still returns a working PowerPitch session for any `submissionId` (SAN-1962 left this open, `power-pitch.service.ts:180-195`).

A login guard would break these applicants: `programs/apply/:code/:slug` and `.../:re-upload-documents` have no `AuthGuard` (`programs.module.ts:102-115`).

**Decisions:**
- **2026-10-22, the mechanism:** applicants prove their email with an OTP through the existing `public/otp_verifications/send|verify` routes. The backend then issues a short-lived applicant token. Protected routes accept either that token or the owner's normal JWT and refuse everyone else. Rollout is staged: log-only by default, then enforce through an env var.
- **2026-10-22, follow-ups:** Nirmal settled all eight follow-up questions the same day. They are folded in below and listed in "Decision record".

## What already exists (Practice 1 — checked before proposing anything)

- **The UI already has an OTP step, but it proves nothing to the server.** The apply modal (`program-public-apply-modal.component.ts:197-249`) and the check-status modal (`program-check-status-modal.component.ts:82-138`) call `send` then `verify`. On success they only write `localStorage['application-<programUUID>'] = { email, … }`, and every later call carries just the email. Evidenced.
- **Programs can skip the OTP.** `bypassOTPVerification` (`application-programs.entity.ts:149-153`, admin `program.php` `bypass_otp_verification`) or being logged in makes the modal skip the step (`program-public-apply-modal.component.ts:158-160`, `:176-178`). Evidenced.
- **OTP wire format.** The PWA md5-hashes the code before `verify` (`sign-up.service.ts:52`). The backend stores `md5(code)` (`verifications.service.ts:72`) and compares the submitted string as-is (`:205`, `:328-331`). The e2e seed does the same (`sc-saas-e2e/README.md:49`). This is the established convention. The "OTP comparison bug" note in `verifications/module.spec.md` is wrong and is corrected here.
- **OTP strength today:**
  - a 4-digit code from `Math.random()` (`core/utils/generate-otp.ts:1-2`);
  - 10 requests per 60 s per rate-limit key on `/send` and `/verify` (`verifications.controller.ts:49-55`, `:70-76`);
  - wrong codes are never counted (`verifications.service.ts:328-331`), and the entity has no attempts column (`verifications.entity.ts`);
  - no `trust proxy` in the backend (grep: no match), so behind a reverse proxy every client may share one limiter key. [INFERRED — the `nestjs-rate-limiter` default key uses the client IP; confirmed during implementation by logging `req.ip` on dev]
- **Token infrastructure.** `JwtStrategy` verifies with `JWT_SECRET_KEY` and returns **any** validly signed payload as `req.user` (`jwt.strategy.ts:25`, `:30-68`). A second token type signed with the same secret would pass `JwtAuthGuard` on every member route. Evidenced. Precedent for a separately keyed HS256 token: `core/services/token.service.ts`.
- **Staged-guard pattern.** `AdminServerKeyGuard` (`admin-server-key.guard.ts:11-79`) and the cockpit's `CockpitCallerKeyGuard` (`sanchiconnect-saas-tenants/src/core/guards/cockpit-caller-key.guard.ts:12-87`) share one shape:
  - mode is `off | log | enforce`, and anything unrecognised means `log`;
  - the mode is read from `process.env` on every call;
  - `log` mode logs one line with `logger.log` (not `warn`, which goes to Sentry) and lets the request through.
- **Admin token.** `AdminTokenGuard` (`admin-token.guard.ts:41-67`) reads `Authorization: Bearer <spa_admin_users.auth_token>` and sets `req.adminUser`. sc-saas-admin mints that token per call with `mintBackendAdminToken($database)` (`includes/core_functions.php:217-225`). Partner sessions mint on the developer row, so the backend cannot tell a partner from an admin.
- **JWT payload has no email.** `SessionDto` carries `userId`, the profile ids and `accountType` (`auth/dto/session.dto.ts`).
- **Submissions.** `forms_submissions` has `user_id` (nullable) and `email` (`form-submissions.entity.ts:30-31`, `:52-53`). A reapply creates a **new** row per attempt, and lookups take the newest by `(formId, email)` (`forms-submissions.repository.ts:48-84`). Form → program resolution already exists: `getSingleProgramByFormId(form.id)`, falling back to `form.applicationPrograms[0]` (`form-management.service.ts:372-400`).
- **Frontend auth transport.** Member auth is the httpOnly `accessToken` cookie with `withCredentials: true` (`add-token-header.http-request-interceptor.ts:46-57`). Any 401 clears **all** storage, logs out and redirects to `/auth/login`, unless the request sets `SKIP_UNAUTHORIZED_REDIRECT` (`:83-92`). A 403 navigates to `/` unless it sets `SKIP_FORBIDDEN_REDIRECT` (`:93-99`).
- **The apply page is embedded in other sites.** It posts its height to `window.parent` (`program-public-apply.component.ts:111-116`), so it runs inside third-party iframes. A cookie-based applicant token would be a third-party cookie there.
- **CORS has no `allowedHeaders` list** (`main.ts:75-81`). The `cors` package then reflects the requested headers, so `x-applicant-token` needs no CORS change, just as `x-hostname` needs none today.
- **Admin's "view as applicant" link.** The PWA turns `?applicationEmail=<email>&isBackdoor=true` into a stored guest identity with no proof (`program-public-apply.component.ts:380-391`). It also sends `isBackdoor` on every form save (`application-program-management-dynamic-form.component.ts:793`). The admin pages build that URL statically (`application-submission-detail.php:1838-1846` → template `themes/default/html/application-submission-detail.php:399-400`; `application_management/form-submission-detail.php:139-143` → template `themes/default/html/application_management/form-submission-detail.php:87-88`).

## Design

### 1. Tokens

All tokens are compact JWTs, HS256, signed with `jsonwebtoken` like `TokenService`. The common claims are `typ: 'cfa_applicant'`, `email` (trimmed, lower-cased), `programUUID`, `aud`, `iat`, `exp`, `jti`. `aud` is this deployment's tenant domain from bootstrap config.

There are two scopes:

| Kind | Extra claims | Authorises | Issued by |
|---|---|---|---|
| **email-scoped** (OTP proof) | none | every submission in `programUUID` whose `email` matches (case-insensitive), so a reapply's new row is covered, plus email-keyed routes for that email | `verify` (§2) |
| **submission-scoped** | `sid` (submissionId), `src: 'created' \| 'admin'` (+ `adminId` when `src=admin`) | only submission `sid`; email-keyed routes only when the submission they resolve is `sid`; never routes 7, 8 or 17 (multi-program, cross-form) | `submit` creating a new row on a bypass-OTP program without a token (§4), or the admin route (§5) |

- **Signing key (decision 3):**
  - `APPLICANT_TOKEN_SECRET` if set. Otherwise `HMAC-SHA256(JWT_SECRET_KEY, 'sanchisaas:cfa-applicant-token:v1')`.
  - `JwtStrategy` can never verify these tokens, and no new required env var is added, so a deployment that lacks it still boots (`validation-schema.ts:20-21`).
  - `JwtStrategy.validate()` additionally rejects any payload with `typ === 'cfa_applicant'`.
- **Expiry (decision 4):** 120 minutes. There is no refresh; after expiry the applicant does the OTP again.
- **`aud`:** binds a token to one tenant even if two tenant deployments share `JWT_SECRET_KEY` (invariant 5).

### 2. Issuing on OTP proof (reuse `public/otp_verifications/verify`)

- `VerifyOtpDTO` gains an optional `applicantProgramUUID` (`@IsOptional() @IsUUID()`).
- `verifyOTP()` returns `applicantToken` and `applicantTokenExpiresAt` (an email-scoped token) when all of these hold:
  - `type === 'email'`;
  - the OTP verifies;
  - `applicantProgramUUID` names an existing application program.
- Otherwise the response is unchanged. No token is ever issued on a failed, expired or locked OTP.
- The QA fixed OTP (`resolveQaFixedOtp`, SAN-1864) keeps working. It only exists on the QA deployment.

### 3. The guard: `ApplicantOrOwnerGuard` (new, `src/core/guards/applicant-or-owner.guard.ts`)

- **Mode:** `APPLICANT_TOKEN_MODE` = `off | log | enforce`. Unset, empty or a typo means `log`. It is read from `process.env` on every request, via `parseApplicantTokenMode()`, which mirrors `parseAdminServerKeyMode`.
- **Per request:**
  1. **Owner JWT.** Run the passport `jwt` strategy optionally (as `OptionalJwtAuthGuard` does), so the cookie or Bearer can set `req.user`.
  2. **Applicant token.** Read `x-applicant-token`, verify signature, `typ`, `aud` and `exp`, and set `req.applicant`.
  3. **Resolve the resource** from `@ApplicantScope(...)` route metadata (§6 table), through `ApplicantAccessService`.
  4. **Allow when either holds:**
     - **owner:** `req.user` and (`submission.userId === req.user.userId`, or `lower(submission.email) === lower(users.email of req.user.userId)`, or for email-keyed routes `lower(:email) === lower(user.email)`);
     - **applicant:** `req.applicant` matches per §1 (email, program, `sid`).
  5. **Otherwise:**
     - **`log` mode:** allow, and log one `logger.log` line with the route pattern, the reason (`no-credential | bad-token | expired | wrong-tenant | not-owner`) and which credential kinds were present. **Never the email or the token** (SAN-1899 precedent, `program-public-apply.component.ts:411-415`).
     - **`enforce` mode:** 401 `{ code: 'APPLICANT_TOKEN_REQUIRED' | 'APPLICANT_TOKEN_EXPIRED' }` when there is no valid credential. 403 `{ code: 'APPLICANT_NOT_OWNER' }` when a valid credential belongs to someone else, or when the resource does not exist (no id probing).
     - The `code` field must survive `GlobalExceptionFilter`. A unit test asserts the response body.
- **Pass-through cases.** Routes whose resource is not CFA pass through unchanged in every mode, with no log line:
  - payments with `moduleType !== 'application_programs'`;
  - public-forms routes whose form belongs to no application program, e.g. event forms (`event-forms/form-field/form-field.component.ts:461`).
- **DI.** The guard and `ApplicantAccessService` live in a small exported module (repositories: form submissions, document submissions, users, application programs, forms). `ApplicationManagementModule`, `FormManagementModule`, `UserModule`, `PaymentManagementModule` and the power-pitch module import it.

### 4. Bypass-OTP programs: lazy OTP (decision 1)

Bypass still skips the OTP at apply time. Identity is proven lazily:

- **First save without a token.** On a program with `bypassOTPVerification = true`, `public/forms-management/.../submit` with no token is allowed **only when it creates a new row**: no existing submission for `(formId, email)`, or `multipleAccepted` without `submissionId`.
  - Its response adds a **submission-scoped** token (`src: 'created'`, `sid` = the new row).
  - That token carries the same session through autosaves, final submit, apply, document upload, pitch-document upload, payment and PowerPitch for that one submission.
- **Returning guests and existing rows.** A tokenless `submit` that would update an existing row, and any `fetch`, require a credential (401 `APPLICANT_TOKEN_REQUIRED`). The frontend skips the draft `fetch` for a tokenless bypass guest and treats them as new. If `submit` then answers 401, a row already exists for that email, so it prompts for the OTP.
- **Later protected calls.** The first status, documents or re-upload call in a later session (no valid token) prompts for the OTP once. The resulting email-scoped token covers the rest.
- **Programs without bypass:** the OTP happens in the modal as today, now returning the token. Every protected call requires it.

### 5. Admin "view as applicant" (decision 2, option a)

- **Backend route.** `POST application-programs-management/admin/applicant-token`, `@UseGuards(AdminTokenGuard)`, body `{ submissionId: number }` (`@IsInt()`).
  - It returns a submission-scoped token (`src: 'admin'`, `adminId = req.adminUser.id`, TTL 120 min), plus `email`, `programUUID`, `programCode` and `programTitle` for building the link.
  - It logs one line with the admin id and submission id (no email).
  - The path has two literal segments, so it cannot match `/:programUUID/upload-document`, `/:programUUID/send-reminder` or the other parameterised POSTs.
  - The scanner sees `AdminTokenGuard` as an auth guard, so no allow-list entry is needed.
- **`isBackdoor` honoured only for admin tokens.** The submit DTO's `isBackdoor` (overwrite a submitted data-collection form) is applied only when the request carries a `src: 'admin'` token. Otherwise it is ignored.
- **sc-saas-admin.** The link becomes a click-through:
  - A new module file `modules/application_management/view_as_applicant.php` is reached as `application_management/view_as_applicant/<submissionId>`.
  - It calls `checkLoggedIn()` and applies the access rule the detail pages use today (`backdoor_access == "1"`, or a partner session, `application-submission-detail.php:1838-1846`). A partner's access to that submission is checked here, because the backend cannot tell partner tokens apart.
  - It mints `mintBackendAdminToken($database)` and cURLs the backend route with `Authorization: Bearer`.
  - It then redirects (302) to `<frontend_url>/programs/apply/<code>/<slug>?isBackdoor=true&applicationEmail=<urlencoded email>#applicantToken=<token>`. The fragment keeps the token out of server logs, proxy logs and `Referer`.
  - The two templates' `href` (`application-submission-detail.php:400`, `application_management/form-submission-detail.php:88`) point at the new route. The `$backDoorUrl` building in the two modules is removed.

### 6. Route-by-route resolution (21 guarded routes + 1 new admin route)

The class-level `FeatureGuard` (application-program `:61`, payments `:39`) and `RateLimiterGuard` / `OptionalJwtAuthGuard` count as non-auth guards for the scanner (`tests/unguarded-routes.json:3-11`). All 21 routes are in the scanner's `unreviewed` list today (`tests/unguarded-routes.json:1559-1797`).

| # | Route | Controller file:line | Guards today | Frontend caller | Resolution / check |
|---|---|---|---|---|---|
| 1 | `DELETE application-programs-management/delete-document/:id` | `application-program.controller.ts:621` | FeatureGuard | `program-office.service.ts:241` ← `dynamic-upload-documents.component.ts:236` | doc → `submissionId` → submission (email, userId, program) |
| 2 | `PUT .../update-document/:id` | `:641` | FeatureGuard | `program-office.service.ts:231` ← `dynamic-upload-documents.component.ts:163` | as 1; `approvalStatus` must be absent or `submitted` (400, all modes) |
| 3 | `POST .../submit-document` | `:494` | FeatureGuard | `program-office.service.ts:182` ← `dynamic-upload-documents.component.ts:164` | body `submissionId` → submission; body `programId` must be its program; `documentTypeId` must belong to `programId` |
| 4 | `POST .../:programUUID/upload-document` (S3 only, 25 MB) | `:536` | FeatureGuard | `program-office.service.ts:191` ← `dynamic-upload-documents.component.ts:152` | applicant: `token.programUUID === :programUUID`; owner: a member JWT with a submission in that program |
| 5 | `POST .../:programUUID/check_application_status/:email` | `:388` | FeatureGuard | `public-api.service.ts:207` ← `program-check-status-modal.component.ts:112` (moves after OTP, decision 5) | email + program |
| 6 | `POST .../:programUUID/check_application_status/:email/details` | `:409` | FeatureGuard | `public-api.service.ts:194` ← `program-public-apply.component.ts:400` | email + program (`sid` token: only if the resolved submission is `sid`) |
| 7 | `POST .../check_application_status_multiple` | `:430` | FeatureGuard | `public-api.service.ts:266` ← `call-for-applications.component.ts:157` (logged-in only, `:156`) | body email; owner JWT, or an email-scoped token whose email matches and whose program equals every UUID in the list |
| 8 | `POST .../applied/:email` | `:445` | FeatureGuard | `public-api.service.ts:231` ← `call-for-applications-applied.component.ts:86` (logged-in) | email; owner JWT |
| 9 | `GET .../fetch-documents/:programId/:submissionId/:roundId?` | `:568` | FeatureGuard | `program-office.service.ts:203` ← `dynamic-upload-documents.component.ts:186` | submission; `:programId` must be its program |
| 10 | `GET .../fetch-documents-rejected/:programId/:submissionId` | `:597` | FeatureGuard | `program-office.service.ts:217` ← `dynamic-upload-documents.component.ts:186` (re-upload page) | as 9 |
| 11 | `POST .../:programUUID/:submissionId/apply` | `:368` | FeatureGuard, RateLimiterGuard, OptionalJwtAuthGuard (`:361`) | `public-api.service.ts:182` ← `program-public-apply.component.ts:647` | submission; must belong to `:programUUID`. Keeps `RateLimiterGuard`. `OptionalJwtAuthGuard` is replaced by the new guard, which also sets `req.user` |
| 12 | `GET users/profile-data/guest/:email` | `user.controller.ts:611` | FeatureGuard, RateLimiterGuard (20/60 s) | `program-office.service.ts:378` ← `application-program-management-dynamic-form.component.ts:235` | email only (email-scoped token or owner); keeps `RateLimiterGuard` |
| 13 | `GET payments/round-pricing/:moduleType/:moduleTypeId/:moduleTypeSubId/:userId` | `payment-management.controller.ts:367` | FeatureGuard + `@Features(PAYMENT_GATEWAYS)` | `payments.service.ts:171` ← dynamic form `:1464` (`'application_programs'`) | only for `application_programs`: `:userId` = submissionId → submission; `:moduleTypeId` must be its program id |
| 14 | `GET payments/verify/:moduleType/:moduleTypeId/:userId/:moduleTypeSubId?` | `:408` | same | `payments.service.ts:157` ← dynamic form `:1485` | as 13 |
| 15 | `GET payments/previous_order/:moduleType/:moduleTypeId/:userId` | `:481` | same | `payments.service.ts:180` ← dynamic form `:1473` | as 13 |
| 16 | `GET payments/applicant_payments/:moduleType/:moduleTypeId/:userId` | `:516` | same | `payments.service.ts:190` | as 13 |
| 17 | `POST power-pitch/connect/call-for-applications` | `power-pitch.controller.ts:136` | none | `power-pitch.service.ts:129` ← `connect-power-pitch-modal.component.ts:39` | body `submissionId` → submission; body `programId` must be its program |
| 18 | `POST public/forms-management/submission/:formUUID/fetch` (body `email`) | `public-form-management.controller.ts:44` | none | `form-management.service.ts:177` ← CFA dynamic form `:475`; `dynamic-form-submit.component.ts:216` (member, `form/submit/:formId`) | form → program (§3; none = pass-through); body email must match the token email or the owner's email |
| 19 | `POST public/forms-management/submission/:formUUID/submit` | `public-form-management.controller.ts:69` | none | `form-management.service.ts:161` ← CFA dynamic form `:862`, `:892`; `dynamic-form-submit.component.ts:385` | form → program; body email must match. If body `submissionId` is set, that row must be the caller's. A tokenless create on a bypass program is allowed (§4). Body `userId` is honoured only if it equals `req.user.userId`; `isBackdoor` only with a `src=admin` token |
| 20 | `POST public/forms-management/submission/:formUUID/upload-file` (S3 only, 100 MB) | `public-form-management.controller.ts:110` | none | `form-management.service.ts:203` ← `event-forms/form-field/form-field.component.ts:461` (CFA and event forms share it) | form → program (none = pass-through). Applicant: `token.programUUID` matches. Bypass program: allowed tokenless, as for creation (§4) |
| 21 | `POST forms-management/submission/:submissionId/cfa/upload-pitch-document` | `form-management.controller.ts:308` | none (`JwtAuthGuard` commented out, `:306-307`) | `program-office.service.ts:261` ← CFA dynamic form `:1687` | submission |
| 22 (new) | `POST application-programs-management/admin/applicant-token` | new, `application-program.controller.ts` | AdminTokenGuard | sc-saas-admin `view_as_applicant.php` (new) | — |

- **Admin calls none of routes 1-21.** Grep of `sc-saas-admin` for every path found no cURL caller. The `applicant_payments` hits in `edit_program_round.php` are an unrelated POST field name.
- **Admin's links.** Its re-upload email link (`application-submission-detail.php:1404`) keeps working: the applicant does the OTP on landing. Its view-as-applicant link moves to §5.

### 7. OTP hardening (decision 7)

- **Attempt cap.**
  - Add `otp_verifications.attempts` (int, not null, default 0).
  - `optVerification()` increments it on a wrong code. From the 5th wrong attempt the row is dead (409, `OTP_TOO_MANY_ATTEMPTS`), even if the right code follows. The applicant requests a new code.
  - A TypeORM migration goes under `src/core/database/migrations/` (generated with `npx typeorm -d dist/core/database/data-source.js migration:generate ...`). The `migrations` CI workflow fails if the entity and the migrations differ (`src/core/database/migrations/README.md:17-18`). It is deployed by `npm run migration:deploy`.
- **Per-email send limit.**
  - `sendOTP()` refuses (429, `OTP_SEND_LIMIT`) a 6th send for the same email (or mobile number) within a rolling 60 minutes.
  - It counts existing `otp_verifications` rows by `created_at`, so no new table is needed.
  - This covers the member login OTP too, because it shares `sendOTP()`.
  - Addresses matching `QA_FIXED_OTP_EMAILS` are exempt. That env var exists only on the QA deployment, so production is unaffected and the nightly e2e suite does not lock its own fixed-OTP accounts.
- **Crypto-secure code:** `crypto.randomInt(1000, 10000)` replaces `Math.random()` in `generate-otp.ts`. Still 4 digits: the PWA `ng-otp-input` length is 4 (`program-check-status-modal.component.ts:26-33`, `program-public-apply-modal.component.ts:62`) and `QA_FIXED_OTP` is 4 digits.
- **Rate-limit key behind the proxy.**
  - `main.ts` sets Express `trust proxy` from `TRUST_PROXY_HOPS` (default 1, since deployments sit behind one reverse proxy), so `req.ip` is the real client.
  - This changes the key of **every** `RateLimiterGuard` route and the `req.ip` in guard log lines, from the proxy address to the client.
  - Verified on dev by logging `req.ip` for two different clients before the flip to `enforce`.
- **Frontend impact:**
  - Both OTP modals show the 409 `OTP_TOO_MANY_ATTEMPTS` message and offer "Resend code".
  - A 429 `OTP_SEND_LIMIT` shows "Too many codes requested, try again later".
  - The OTP input length is unchanged.
- **e2e impact:**
  - The fixed-OTP accounts are exempt from the per-email limit.
  - No test submits a wrong code, so the attempt cap is never hit. One new negative test does it on a throwaway address.
  - `trust proxy` gives the CI runner its own 10/60 s bucket instead of sharing the proxy's. The 61 s back-off in `LoginPage.requestOtp` (`knowledge.md:25`) stays.

### 8. Frontend storage and transport

- **Storage.** Header token, not a cookie (iframe embedding, above). It lives in `localStorage['applicant-token-<programUUID>'] = { token, expiresAt }`. This is a separate key from `application-<programUUID>`, which is overwritten wholesale in three places (`program-public-apply.component.ts:439`, `program-public-apply-modal.component.ts:182`, `program-check-status-modal.component.ts:99`).
- **Attaching it.** A sibling interceptor (registered in `http-interceptor.module.ts`) sets `x-applicant-token` only when all three hold:
  - the request goes to the backend `apiUrl`, never the cockpit (the existing `tenants` check, `add-token-header.http-request-interceptor.ts:46`) and never third parties;
  - the path is one of routes 1-21;
  - `ApplicantTokenService` holds an unexpired token for the active program. `ProgramPublicApplyComponent` sets the active program on init.
- **Error handling.**
  - Every applicant-capable call sets `SKIP_UNAUTHORIZED_REDIRECT` and `SKIP_FORBIDDEN_REDIRECT`.
  - On 401 `APPLICANT_TOKEN_REQUIRED|EXPIRED`, the page opens the OTP modal and retries once.
  - A guest 401 never wipes storage or redirects.
- **Logged-in owners:** no change. The cookie already rides every backend call.

## Acceptance criteria

Backend (`APPLICANT_TOKEN_MODE=enforce` unless stated):
- [ ] **Issuing on verify.** `verify` with `type=email`, a correct OTP and `applicantProgramUUID` of an existing program returns an email-scoped `applicantToken` and `applicantTokenExpiresAt` (now + 120 min). Without `applicantProgramUUID`, or on a wrong, expired or locked OTP, there is no token and the response is otherwise unchanged.
- [ ] **No member access.** An applicant token sent as `Authorization: Bearer` or as the `accessToken` cookie to a `JwtAuthGuard` route (e.g. `GET users/profile`) gets 401.
- [ ] **Bad tokens refused.** A token past `exp`, with a different `aud`, with a tampered signature, or signed with `JWT_SECRET_KEY` itself gets 401 on every one of routes 1-21.
- [ ] **Each of routes 1-21:**
  - no credential gets 401;
  - an email-scoped token for email A on email B's resource gets 403;
  - a token for program P on program Q gets 403 (except route 12);
  - a `sid` token on a different submission gets 403;
  - the matching token gets 2xx;
  - the owner's member JWT on their own submission gets 2xx, both when matched by `forms_submissions.user_id` and by email.
- [ ] **Pass-through.** Payments with another `moduleType`, and public-forms routes on a form with no application program, behave exactly as before in all three modes.
- [ ] **Bypass create.** On a bypass-OTP program, a tokenless `submit` that creates a new row succeeds and returns a `sid` token (`src=created`). That token then works on routes 1-4, 9-11, 13-17 and 21 for that submission only. A tokenless `submit` that would update an existing row gets 401. A tokenless `fetch` gets 401.
- [ ] **Submit body fields.** `submit` with a body `userId` that is not the caller's member id does not write `user_id`. `isBackdoor: true` without a `src=admin` token does not overwrite a submitted data-collection form.
- [ ] **Admin route.** `POST .../admin/applicant-token` without a valid admin token gets 401. With one, it returns a `sid` token (`src=admin`) for that submission, plus `email`, `programUUID`, `programCode`, `programTitle`.
- [ ] **Document status.** `PUT update-document/:id` with `approvalStatus` `accepted` or `rejected` gets 400 for every caller in every mode. `submitted` or absent still works.
- [ ] **OTP attempt cap.** The 5th wrong code for one OTP row locks it; the right code afterwards gets 409 `OTP_TOO_MANY_ATTEMPTS`. The migration runs clean on an empty MySQL 8 database (`migrations` CI).
- [ ] **OTP send limit.** The 6th `send` for one email within 60 minutes gets 429 `OTP_SEND_LIMIT`, except for addresses matching `QA_FIXED_OTP_EMAILS`. Codes come from `crypto.randomInt`.
- [ ] **Proxy.** With `trust proxy` set, two clients behind the proxy get separate rate-limit buckets (verified on dev, evidence pasted).
- [ ] **Log mode.** Every refused-in-enforce request still succeeds and produces exactly one `ApplicantToken` log line with neither an email nor a token. `off` mode: no check, no log. Unset or garbage mode = `log`. A missing `APPLICANT_TOKEN_SECRET` does not stop boot.
- [ ] **Scanner.** `node scripts/unguarded-routes.js` passes. None of routes 1-21 is left in `unreviewed`, and nothing is added to `allowList`.
- [ ] **API snapshot.** `contracts/openapi.json` is regenerated: new DTO field, new admin route, optional `x-applicant-token` header on routes 1-21. The api-contract check passes.

Admin:
- [ ] **View-as-applicant.** For an admin with `backdoor_access`, or a partner session allowed on that submission, "view as applicant" on both detail pages opens the PWA as that applicant with a working token. The token is in the URL fragment, never the query string. Without permission the module refuses and calls no backend route.
- [ ] **Admin gates.** `composer gates` passes, including `tests/auth-gates.json` (the new module calls `checkLoggedIn()`). `php -l` is clean. No `//` comments.

Frontend:
- [ ] **Token stored and sent.** After a guest verifies the OTP in either modal, `applicant-token-<programUUID>` is stored. Every call on routes 1-21 from the apply and re-upload pages carries `x-applicant-token`. No cockpit or third-party call carries it.
- [ ] **Check-status order.** The check-status modal sends the OTP first, then calls `/details` with the token. A 404 shows "Application not found" (decision 5).
- [ ] **Bypass programs.** No OTP at apply. The `sid` token from the first `submit` is stored and used. A returning bypass guest is asked for the OTP once, at the first protected call (decision 1).
- [ ] **Stored identity without a token.** A guest with a stored `application-<uuid>` identity but no valid token (every guest from before this ships) is asked for an OTP before the status, documents, payment or PowerPitch calls run.
- [ ] **Admin link.** `?isBackdoor=true&applicationEmail=…#applicantToken=…` stores the token, removes the fragment from the address bar, and opens the application. Without a fragment token it behaves like any guest (OTP prompt).
- [ ] **No logout on applicant errors.** A 401 or 403 from an applicant call never clears storage, logs out or redirects.
- [ ] **OTP errors.** `OTP_TOO_MANY_ATTEMPTS` and `OTP_SEND_LIMIT` are shown with a resend or retry-later path.
- [ ] **Members.** Logged-in members see no OTP prompt, and their calls succeed on the cookie.
- [ ] **Generated types.** `core/contracts/api.generated.ts` is regenerated and compiles.

E2E:
- [ ] **Real OTP.** The guest real-OTP test asserts the token is issued and sent.
- [ ] **Existing tests.** Every test that injected a guest identity or read status through the API obtains a token first, and passes against development with `APPLICANT_TOKEN_MODE=enforce`.
- [ ] **Bypass flows.** They assert the `sid` token from `submit`.
- [ ] **New negative tests pass in `enforce`:**
  - no token gets 401;
  - wrong email gets 403;
  - `update-document` `accepted` gets 400;
  - the attempt cap locks after 5 wrong codes;
  - the admin view-as-applicant link opens the application.

## Per-repo plan

### backend (`sc-saas-backend`) — first; deploys in `log` mode

1. **`src/core/services/applicant-token.service.ts`** (new). Sign and verify both token kinds; key per §1; TTL 120 min; `aud` from bootstrap tenant config. Unit tests.
2. **Guard pieces** (new): `src/core/guards/applicant-or-owner.guard.ts`, `applicant-scope.decorator.ts`, `ApplicantAccessService`, and an exported module. Unit tests for every mode × credential × resource case, including pass-throughs.
3. **`src/core/strategy/jwt.strategy.ts`:** reject `typ === 'cfa_applicant'`.
4. **`verifications`:**
   - DTO `applicantProgramUUID`; token issue in `verifyOTP()`;
   - attempt cap in `optVerification()` with an `attempts` column on `verifications.entity.ts` plus a migration;
   - per-email send limit in `sendOTP()` with the `QA_FIXED_OTP_EMAILS` exemption;
   - `crypto.randomInt` in `core/utils/generate-otp.ts`.
5. **`main.ts`:** `trust proxy` from `TRUST_PROXY_HOPS` (default 1).
6. **Wire `@UseGuards(ApplicantOrOwnerGuard)` + `@ApplicantScope(...)` + `@ApiHeader({ name: 'x-applicant-token', required: false })` on routes 1-21:**
   - `application-program.controller.ts` (routes 1-11; route 11 keeps `RateLimiterGuard` and drops `OptionalJwtAuthGuard`);
   - `user.controller.ts:611` (keeps `RateLimiterGuard`);
   - `payment-management.controller.ts:367, 408, 481, 516`;
   - `power-pitch.controller.ts:136`;
   - `public-form-management.controller.ts:44, 69, 110`;
   - `form-management.controller.ts:308` (delete the commented-out guard lines `:306-307`, `:310`, `:320`).
7. **Admin route.** `POST application-programs-management/admin/applicant-token` with `AdminTokenGuard` and `AdminApplicantTokenDto { submissionId }`.
8. **`form-management.service.ts` `publicFormSubmission()`:**
   - return the `sid` token on a tokenless bypass create;
   - honour body `userId` only if it equals `req.user.userId`;
   - honour `isBackdoor` only for a `src=admin` token. Pass the guard's verdict in from the controller rather than re-reading headers in the service.
9. **`application-program.service.ts`:**
   - `updateDocument()` (`:1735`) refuses `approvalStatus` other than `submitted`, in the service so the OpenAPI schema keeps its shape;
   - `submitDocument()` (`:1501`) checks the program and document-type consistency.
10. **`tests/unguarded-routes.json`.** Run `node scripts/unguarded-routes.js --snapshot` and review the diff: the 21 entries leave `unreviewed`, nothing else changes. Note in the guard docstring that `log` mode passes the scanner without refusing anyone, as `AdminServerKeyGuard` does.
11. **`contracts/openapi.json`:** regenerate.
12. **Docs.**
    - Module specs: `application-management`, `verifications` (fix the md5 note; document attempts and the limit), `user`, `payment-management`, `power-pitch-module`, `form-management`.
    - Backend `CLAUDE.md`: add the guard and the env keys `APPLICANT_TOKEN_MODE`, `APPLICANT_TOKEN_SECRET`, `TRUST_PROXY_HOPS`.
13. **Deploy check.** `npm run build`, then `dist/main.js` starts and Nest DI resolves the guard's providers in every importing module, then `npm run migration:deploy` on dev.

### admin (`sc-saas-admin`) — second; needs backend step 7 deployed

1. **`modules/application_management/view_as_applicant.php`** (new). It:
   - calls `checkLoggedIn()`;
   - applies the existing permission rule (`backdoor_access == "1"` or a partner session, and the partner may see this submission's program);
   - calls `mintBackendAdminToken($database)` and cURLs `api_server_url . "v1/application-programs-management/admin/applicant-token"` with `Authorization: Bearer`;
   - on success, 302-redirects to the PWA URL with the token in the fragment (§5);
   - on failure, shows an error. It does not fall back to the old URL.
2. **`modules/application-submission-detail.php:1838-1846` and `modules/application_management/form-submission-detail.php:139-143`:** set `$tpl->backdoorUrl` to the new admin route for that submission. No email is in the URL any more.
3. **Templates** `themes/default/html/application-submission-detail.php:399-400` and `themes/default/html/application_management/form-submission-detail.php:87-88`: no markup change beyond the href value.
4. **Conventions.** `/* */` comments only (PHP and inline JS), `count($arr) > 0`, `php -l` on every edited file, `composer gates`. Update `tests/auth-gates.json` only if the gate requires it (the new file calls `checkLoggedIn()`, so it should not). Update the `application_management` module spec.

### frontend (`sc-saas-frontend`) — third; needs backend (and admin for the backdoor path) deployed

1. **`core/service/applicant-token.service.ts`** (new): get, set and clear per `programUUID`; expiry; active program.
2. **`core/service/sign-up.service.ts` `verifyOTP()`:** pass `applicantProgramUUID` through and return the data. Keep `md5(code)` (`:52`).
3. **`program-public-apply-modal.component.ts`:** send `applicantProgramUUID` and store the token. On a bypass program it still skips the OTP (`:158-160`, `:198-201`).
4. **`program-check-status-modal.component.ts`:**
   - send the OTP first (drop the pre-check at `:112`);
   - verify with `applicantProgramUUID` and store the token;
   - then call `/details` with it, and show "Application not found" on 404 (decision 5).
5. **`program-public-apply.component.ts`:**
   - set the active program on init;
   - if the visitor is not logged in, has `applicationMeta.email` and has no valid token, open the check-status OTP modal before `applicationProgramManagementApplicationDetails()` (`:393`), and the same on the re-upload path (`:147`, `:352-361`);
   - `isBackdoor` (`:380-391`): read `#applicantToken` from `location.hash`, store it, `history.replaceState` to drop the fragment, then set the identity.
6. **`application-program-management-dynamic-form.component.ts`:**
   - store the `sid` token returned by the first `submit`;
   - for a tokenless bypass guest, skip the draft `fetch` (`:475`);
   - on 401 from `submit`, open the OTP modal.
7. **Interceptor.** A sibling interceptor in `core/http-interceptor/`, registered in `http-interceptor.module.ts`, attaches `x-applicant-token` per §8.
8. **Redirect suppression.** Set `SKIP_UNAUTHORIZED_REDIRECT` and `SKIP_FORBIDDEN_REDIRECT` (`http-context-tokens.ts`) on:
   - `public-api.service.ts:182, 194, 207, 231, 266`;
   - `program-office.service.ts:182, 191, 203, 217, 231, 241, 261, 378`;
   - `payments.service.ts:157, 171, 180, 190`;
   - `power-pitch.service.ts:129`;
   - `form-management.service.ts:161, 177, 203`.

   Only applicant-capable requests get them. On 401 with an applicant code: OTP modal, then retry once.
9. **Document errors.** `shared/dynamic-upload-documents/dynamic-upload-documents.component.ts`: surface the OTP prompt instead of the generic error toast (`:171`, `:213`, `:241`).
10. **OTP error messages** for `OTP_TOO_MANY_ATTEMPTS` (with resend) and `OTP_SEND_LIMIT`, in both modals.
11. **Generated types.** Regenerate `core/contracts/api.generated.ts` (`node scripts/sync-openapi.js`).
12. **Tests and docs.**
    - Karma specs: the service, the interceptor (only the listed backend paths; never the cockpit), both modals, the backdoor fragment handling.
    - Update `program-public-apply.component.spec.ts`.
    - Module specs: `programs`, `shared`, `dynamic-forms`.

### sc-saas-e2e — fourth; must be green against development in `enforce` before staging is flipped

1. **`fixtures/cfa.ts`:** an `applicantToken(programUuid, email)` helper.
   - It calls `public/otp_verifications/send`, then `/verify` with `md5(qaOtp())` and `applicantProgramUUID`.
   - It caches per run (TTL 120 min covers a run) and waits 61 s then retries once on a 429.
   - Seeded applicant emails must match `QA_CFA_EMAIL_PATTERN` / `QA_FIXED_OTP_EMAILS` (check `seedSubmittedApplications`).
2. **`cfaAdmin.applicationStatus()`** (`fixtures/cfa.ts:428-434`) sends `x-applicant-token`. Callers:
   - `admin-path.spec.ts:74, 88`;
   - `p4-admin-review.spec.ts:125, 136`;
   - `admin-approve-application.spec.ts:30, 48`;
   - `startup-path-decision.spec.ts:44`.
3. **`pages/frontend/cfa/ProgramApplyPage.ts` `useGuestIdentity()`** (`:50`) also injects `applicant-token-<uuid>`. Callers:
   - `p3-apply-guest.spec.ts:250, 278, 360, 393`;
   - `p4-admin-review.spec.ts:209`;
   - `p2-form-builder.spec.ts:49`.
4. **Bypass guest flows using `submitWithoutOtp()`.** These are `p3-apply-guest.spec.ts:125`, `:318`, `apply-program-round.spec.ts:37` and `p6-downloads-reports.spec.ts:152`.
   - Assert the `sid` token in the first `submit` response.
   - The resubmission test (`:299-335`) reuses an existing seeded row, so it now hits the lazy OTP prompt. It completes it with the fixed OTP. Its email is seeded, so it must match the fixed-OTP pattern.
   - Member flows (`p3-apply-member.spec.ts:73`, `startup-path-helpers.ts:43`) are unchanged (cookie).
5. **Real-OTP test** `p3-apply-guest.spec.ts:47-101`: assert `applicantToken` in the verify response and the header on the following calls.
6. **New `tests/cfa/applicant-token.spec.ts`** (`@regression @cfa @frontend @write`):
   - no token gets 401;
   - another applicant's token gets 403;
   - a member JWT gets 2xx;
   - `update-document` `accepted` gets 400;
   - 5 wrong codes lock the OTP (throwaway address, not a fixed-OTP account).
7. **New admin journey:** "view as applicant" from the admin submission detail opens the PWA application with a token (`@admin @cfa`).
8. **Docs.** `knowledge.md` (guest identity, status view, OTP limits and exemption, bypass `sid` token), `README.md`, `CLAUDE.md` if the setup changes.

## Cross-Repo Contract Impact (Practice 4)

- **API contract (invariant 2), owned by backend.**
  - **Before:**
    - `verify` body is `{ type, countryCode?, mobileNumber?, emailAddress?, code }`; data is `{ message, id, verified }`;
    - `public/forms-management/.../submit` data is the saved row;
    - routes 1-21 accept anyone.
  - **After:**
    - `verify` accepts an optional `applicantProgramUUID` and returns a token;
    - `submit` may add `applicantToken` and `applicantTokenExpiresAt`;
    - one new admin route;
    - routes 1-21 accept an optional `x-applicant-token` and, in `enforce`, refuse callers that are neither owner nor matching applicant;
    - `send` may answer 429 `OTP_SEND_LIMIT`; `verify` may answer 409 `OTP_TOO_MANY_ATTEMPTS`.
  - **Schema is additive.** The behaviour change is gated by the env var (refusals) or affects only abusive callers (limits).
  - **Consumers:**
    - frontend (all of the above);
    - admin (new route only);
    - e2e (direct API calls listed).
  - **Gate:** `/audit-contract` before `in-review`. The `api-consumers-updated` label is needed only if the api-contract check classes the change as breaking.
- **Auth (invariant 4).**
  - **New credential type:** isolated by key and `typ` rejection, so it can never satisfy `JwtAuthGuard`.
  - **Member JWT:** unchanged.
  - **Admin token:** reused as is.
  - **`trust proxy`:** changes `req.ip` for every rate-limited route (more accurate client keying).
- **Tenant scoping (invariant 5).**
  - All reads are in the deployment's own DB.
  - `aud` binds tokens to one tenant.
  - Admin calls its own tenant's `api_server_url`.
  - `/check-isolation` before `in-review`.
- **PowerPitch (invariant 6).** Route 17 only gains caller authorisation. `PowerPitchExternalService` and `/v1/externals/*` are untouched.
- **Flags (1) and verification shape (3):** not touched.

## Contracts & invariants

- **Flags:** none.
- **API:** see the frontmatter and the section above.
- **Events:** none.
- **Invariants at risk:**
  - 2 (API contract: additive schema, staged behaviour);
  - 4 (auth: new credential type, isolated);
  - 5 (tenant scoping: `aud`);
  - 6 (touched only by route 17's caller check).

## Test plan

- **backend.** jest, then `npm run gates` (unguarded-routes, api-contract, test floors, migrations), build, `dist/main.js` start, `npm run migration:deploy` on dev. Specs:
  - `applicant-token.service.spec.ts`: both kinds, expiry, `aud`, wrong key, a token signed with `JWT_SECRET_KEY` refused;
  - `applicant-or-owner.guard.spec.ts`: modes × credentials × resources, pass-throughs, the `code` body through `GlobalExceptionFilter`;
  - a `GUARDS_METADATA` test on all 21 handlers plus the admin route, like `login-required.san1958.spec.ts`;
  - `verifyOTP` token issue; attempt cap; send limit with the QA exemption;
  - bypass create returns a `sid` token; update without a token refused; `userId` / `isBackdoor` rules;
  - `updateDocument` status rule;
  - `JwtAuthGuard` refuses an applicant token.
- **admin.** `php -l`, `composer gates` (auth-gates), a manual click-through on dev as an admin with `backdoor_access` and as a partner.
- **frontend.** Karma per plan step 12, then `npm run gates`. Manual runs on dev:
  - guest apply with OTP;
  - bypass guest apply, then a later return;
  - re-upload link in a fresh browser;
  - check-status;
  - logged-in startup;
  - embedded iframe;
  - admin view-as-applicant.
- **sc-saas-e2e.** `npm run typecheck`, then `npm run test:cfa` against development twice: in `log`, then after dev is flipped to `enforce`.
- **cross-repo.** `/audit-contract`, `/check-isolation`.
- **Test coverage note:** the workspace "guardian" tests-first skill does not exist yet. These repos have jest, Karma, PHP gates and Playwright, so the tests above are required, not substituted.

## Rollout

Poly-repo, no atomic change; each step is safe on its own.

1. **Backend deploys with `APPLICANT_TOKEN_MODE` unset (= `log`).**
   - `npm run migration:deploy` adds `otp_verifications.attempts`.
   - Tokens are issued, including `sid` tokens on bypass creates. Nobody is refused by the guard, and refusals-to-be are logged.
   - These take effect immediately: the attempt cap, the per-email limit, crypto codes, `trust proxy`, the `update-document` status rule, and the `userId` / `isBackdoor` body rules. None affects a legitimate caller:
     - the PWA sends only `submitted`;
     - `userId` from the PWA is the member's own;
     - `isBackdoor` saves come only from the admin link, which is broken anyway until step 2. The old email-in-URL link still opens the PWA, but its saves no longer overwrite submitted data-collection forms until admin ships.
   - Confirm `req.ip` on dev shows real client addresses.
2. **Admin deploys.** View-as-applicant now goes through the backend route.
3. **Frontend deploys.**
   - Guests do the OTP (or get a `sid` token on bypass programs) and send the token.
   - Guests with a stored identity are asked for an OTP once.
   - From here the `log` lines should fall to stale tabs only.
4. **E2E updated and green against development in `log`.** Then set `APPLICANT_TOKEN_MODE=enforce` on development (`ai_native_setup`, `thub.sanchidev.in`; pm2 restart with the new env) and run the CFA suite.
5. **Staging (`stagingdemo`):** `enforce` after at least 7 days of dev in `enforce` with no unexplained refusals, and a staging `log` window longer than the 120-minute TTL.
6. **Production (`main`/`master`):** at least a 7-day `log` window, then `enforce`, only when Nirmal says so. No merges to main without explicit instruction.
7. **Rollback.**
   - Guard: `APPLICANT_TOKEN_MODE=log` (or `off`) and restart.
   - `trust proxy`: `TRUST_PROXY_HOPS=0`.
   - The attempts column is additive and is left in place.

## Out of scope

- **Payments routes for other module types.** `moduleType` other than `application_programs` (`programs` + `startupId`, `programs-details-page.component.ts:376`, `:426`; `lms_courses` + `userId`, `learning-management.service.ts:150`) stays open. File a separate issue.
- **Public forms not attached to an application program** (event forms and other public forms on routes 18-20). They pass through unchanged. File a separate issue if they need protecting.
- PowerPitch `video/call-for-applications` routes (already behind `PowerPitchGuard`).
- Changing the 4-digit OTP length.
- Any change to the member login flow beyond the shared send limit and crypto code.

## Decision record (Nirmal, 2026-10-22)

1. **Bypass-OTP programs:** lazy OTP. Bypass still skips it at apply time; the first protected call (status, documents, re-upload) prompts once. Design §4.
2. **Admin view-as-applicant:** option (a), a new `AdminTokenGuard` backend route that mints an applicant token for the link. sc-saas-admin is added to `repos`. Design §5.
3. **Signing key:** `APPLICANT_TOKEN_SECRET` if set, otherwise derived from `JWT_SECRET_KEY`; `JwtStrategy` rejects `typ=cfa_applicant`. Design §1.
4. **Token:** 120 minutes, scoped to (email, programUUID). Bypass creates and admin links get the narrower `sid`-scoped form of the same token. Design §1.
5. **`check_application_status/:email`:** the check-status modal sends the OTP first; the route is guarded like the others. Route 5.
6. **Extra routes included:** `public/forms-management/submission/:formUUID/fetch|submit|upload-file`, `:programUUID/:submissionId/apply`, `cfa/upload-pitch-document`. Routes 11, 18-21.
7. **OTP hardening in scope:** attempt cap with migration, per-email send limit, crypto-secure code, `trust proxy`. Design §7.
8. **Acceptance criteria and rollout:** updated above.

## Open questions

None. All eight were settled by Nirmal on 2026-10-22 (Decision record). Approved by Nirmal on 2026-10-22, including the two derived rules (bypass-program first save may only create; the 5-per-hour send limit also applies to member login).
