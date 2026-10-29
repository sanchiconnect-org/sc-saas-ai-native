# SAN-2127 — Application detail "Backdoor Access": registered applicant goes to their dashboard

Linear: https://linear.app/sanchiconnect/issue/SAN-2127 · Repo: `sc-saas-admin` · Priority: Medium · Assignee: Sandeep · Labels: Repo: Admin, Improvement
Classification: **ENHANCEMENT** (requirement is clear: the reporter named the expected behaviour)

## Problem
"Backdoor Access" on the Application Detail panel always opens the program's apply form as the applicant (`view_as_applicant.php`, SAN-1959), even if the applicant already has an account. The Startup / MSME detail page's "Backdoor Login" opens the user's dashboard instead.

## Requested behaviour
- Applicant is a registered user: open that user's dashboard.
- Not registered: the plain apply-form link used before SAN-1959 (decided by the reporter after the applicant-token call returned HTTP 502 on a local run).

## Evidence
- `modules/application_management/view_as_applicant.php`: only the applicant-token flow existed; no `users` lookup.
- Dashboard flow already in use: `themes/default/html/startup-detail/startup-detail.php` (`#loginToBackdoor`, `generateBackdoorToken`, `window.open(frontend/backdoor-login/<userId>/<token>)`); PWA route `backdoor-login` → `BackdoorLoginComponent`; backend `GET v1/admin-actions/backdoor-login/:userId/:adminMd5` (`checkIsValidAdmin`, then a session for that user).

## Fix (`sc-saas-admin`, one file)
`modules/application_management/view_as_applicant.php`: for an admin session, after the permission check, look up `users.email = forms_submissions.email`. On a match: `generateRandomStringForBackdoor($database)`, then 302 to `<frontend_url>/backdoor-login/<users.id>/<token>` (`Cache-Control: no-store`, `Referrer-Policy: no-referrer`). No match (and a program with a `program_code`): 302 to `<frontend_url>/programs/apply/<program_code>/<slug>?applicationEmail=<email>&isBackdoor=true`, built from `application_programs` (`program_code`, `program_title`), no backend call and no `#applicantToken`. An empty email or no program: the applicant-token flow, unchanged. A redirect from the page (not `window.open` after an AJAX call) avoids popup blockers.

Decisions taken (not confirmed with the reporter):
- Partner sessions keep the applicant-token flow: the dashboard flow uses the developer token, which would let a partner sign in as any registered user.
- "Registered" = exact email match on `users.email`; an applicant who registered with another email counts as not registered.
- Any account type opens its own dashboard (the PWA picks it).
- The plain link is the pre-SAN-1959 URL. The PWA showed the form with the toast "This application belongs to someone else.", so editing or saving as the applicant may not work through it; the SAN-1959 backend no longer accepts the email alone.
- Local run (`sine-admin.sandeep`, submission 6376, email `mahima@yopmail.com`): no `users` row matched that email (the startup contact's email was different), so the page fell back to the applicant-token flow and `applicant-token` returned HTTP 502 (Apache error log, 3 times). Cause of the 502 not found; the plain link no longer calls it.

## Security note
The dashboard path puts the admin `auth_token` in the URL (backend NIR-5: it does not expire and works for any user id). Same exposure as the Startup / MSME detail page; weaker than the SAN-1959 applicant token. The backend's SAN-384/387 scoped one-time token would be the safer route but is built for partner sessions.

## Verification
- `php -l modules/application_management/view_as_applicant.php`: No syntax errors detected.
- Local evidence only: the 502 above, from before the plain-link change.
- NOT done: a run on development after the change (registered applicant → dashboard; unregistered → plain apply form; partner unchanged). No automated test added: sc-saas-admin has no test framework.

## Commit
Committed in sc-saas-admin (see Linear). Push branch: `ai_native_setup_sandeep`.
