# SAN-1828 — Jury invite: reject an already-registered email

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1828
- **Repo:** sc-saas-admin · **Type:** Bug (CODE_ERROR) · **Priority:** High · **Assignee:** Nirmal Singh

## Problem
Edit Round → Jury Allotment → "or invite a new member who is not registered on the platform": the invited jury never received an email (reported when a program manager invited), while the UI said "Jury added successfully!".

## Root cause
The `add_new_jury` handler looked the email up in `spa_admin_users`. If it already existed, it reused that account and attached it to the program and round. It then still called the backend `v1/admin-actions/admin-account-created/:token` with `password: null`, because `$password` is only set when a new account is created. `AdminAccountCreatedDto.password` is `@IsNotEmpty()`, so the backend returned a 400 and no email was sent. `sendAccountCreatedEmail()` ignores the response, so the admin still showed success.

The mentor and venture-studio round editors already rejected existing emails. In the startup-program editor that check had been commented out, and the application-management copy never had it.

## Fix
When the email already exists, return the error "That email address is already associated with other account" and stop. Nothing is created, attached, or emailed. Both pages already show `errorMessage` as an error toast.

Files:
- `modules/application_management/edit_program_round.php` (`add_new_jury`)
- `modules/edit_program_round.php` (`add_new_jury`, startup-program round editor)

Not changed: `modules/edit_program_round2.php`, which no routing or template references (legacy copy).

## Verification
- `php -l` passes on both files.
- No automated test: sc-saas-admin has no test framework.
- Manual check pending: inviting an existing email shows the error toast and adds no row. Inviting a new email still creates the jury and sends the account-created email.

## Known gap (not in scope)
`sendAccountCreatedEmail()` still discards the backend response, so a gateway or send failure for a genuinely new jury still shows success. Check the admin Email Logs page for those.

## Commit
sc-saas-admin `51accc64` on `ai_native_setup`
