# SAN-29 — WhatsApp Management: no role gate, plaintext WATI token

**Repo:** sc-saas-admin · **Parent:** SAN-1562 (secret rotation) · **Class:** CODE_ERROR

## Problem
`modules/developer/whatsapp_management.php` only called `checkLoggedIn()`. Any logged-in admin who opened the URL directly could read the live WATI token and run `TRUNCATE TABLE whatsapp_templates`. The menu link is shown only to `is_dev` users, but the page itself never checked the role. The save handler (`modules/ajax/whatsapp_actions.php`) did not check it either.

## Fix
- `modules/developer/whatsapp_management.php`: added a `checkRole("is_dev")` gate that redirects to 403, the same pattern as the other Developer-zone pages. The saved token is no longer passed to the template; it gets a `hasWatiToken` flag instead.
- `themes/default/html/developer/whatsapp_management.php`: the token textarea is always empty. When a token is saved, the placeholder says to leave the field blank to keep it. The client-side "required" check only applies when no token is saved.
- `modules/ajax/whatsapp_actions.php`: the same `is_dev` gate (applied after the CSRF check). On "edit settings", a blank token keeps the saved one; it is still required when none is saved. The only caller of this handler is the dev page.

## Verification
`php -l` clean on all 3 files. No automated tests (sc-saas-admin has no test framework). To check by hand: as a non-dev admin, `/developer/whatsapp_management` should redirect to 403. As a dev, the token field should show empty, and saving with it blank should keep the saved token.

## Follow-up (not code)
Rotate the WATI token (SAN-1562).

**Commit:** sc-saas-admin@18ccaea6 (ai_native_setup)
