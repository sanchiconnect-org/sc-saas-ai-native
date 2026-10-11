---
id: SAN-1721                    # milestone "Startup Details — Self Declaration PDF" in Linear project
                                 # "Startup Grant Release Letter — Admin PDF Download" (P-SAN-57); issues SAN-1720 + SAN-1721.
title: Startup Details — Self Declaration PDF
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-1721
owner: aman.k@sanchiconnect.com
repos: [admin]
contracts:
  api: []                       # None. Reads the tenant DB directly via Medoo, no backend call.
  flags:
    - "startup_grant_release_format_download_enable"   # EXISTING flag, reused on purpose (decision by Aman, 2026-10-06).
  events: []
tenant_scoped: true             # per-request tenant DB connection is the scope (admin invariant #5).
depends_on: [SAN-786]           # reuses its flag, logo setting and PDF approach
created: 2026-10-06
---

# Startup Details — Self Declaration PDF

## Problem

On the admin Startup Detail page (`/startup-detail/{id}/details`) an operator can only Print the profile. The Tripura Directorate of IT needs each startup's **Self declaration** (turnover under Rs.25 crore, innovation, no demerger, not a subsidiary/holding, 50% Tripura workforce) as a PDF in a fixed government layout (reference: `self.pdf`). Today nothing produces it.

## Resolved decisions (do not re-litigate)

1. **Flag:** reuse `startup_grant_release_format_download_enable` (Aman, 2026-10-06). No new flag, no tenants change.
2. **Template storage:** a new `spa_settings` row `startup_self_declaration_template` in the existing `startup_grant_release_letter` settings section, next to the Grant Release Letter template. The logo row `startup_grant_release_letter_logo` is shared. The Grant Release Letter template is untouched.
3. **Button placement:** a new `btn-group` above the existing Print/Message row on Startup Detail.
4. **Layout:** reproduce `self.pdf`: logo, addressee block, "Sub: Self declaration", five checked certification rows in a rounded box, Notes, and a right-aligned Representative Name / Company Name / Date box. About 5% page margins, Helvetica, blue rounded checkboxes.
5. **Placeholders:** `{{representative_name}}` = startup owner's `users.name`; `{{company_name}}` = `startups.company_name`; `{{date}}` = download date (`d/m/Y`). A blank value renders as an em dash, never an empty gap.

## Acceptance criteria

- [x] Flag off or unset: button not rendered; direct URL hit redirects to `/404`.
- [x] Flag on: "Download Self Declaration" appears above the Print/Message row and downloads `startup-{id}-self-declaration.pdf` (single A4 page).
- [x] Template seeded once per tenant with the `self.pdf` wording; an admin's saved edit is never overwritten on later loads.
- [x] Template editable in Developer > Settings Management > Startup Grant Release Letter; line breaks are normalized on save.
- [x] Logo embedded as a base64 data URI (never a signed URL); a missing/unreachable logo does not break the PDF (it renders without it and logs a line).
- [x] Partner sessions can only download for their own startups (existing 403 check runs first).
- [x] Grant Release Letter download and the Print button are unchanged.
- [ ] QA/UAT sign-off: `specs/features/SAN-1721-startup-self-declaration-qa-uat-test-script.md` (assigned to Ritu Raj).

## Per-repo plan

### admin (only repo)

- `includes/core_functions.php` — `startupGrantReleaseLetterSettings()` seeds the third row with the default template.
- `modules/developer/settings_management.php` — save handler normalizes line breaks for the new template key too.
- `modules/startup-detail.php` — `download_self_declaration` GET handler (flag check, settings read, dompdf render).
- `themes/default/html/startup-detail/startup-detail.php` — flag-gated button.

No tenants / backend / frontend change. Contract checks: `/trace-flag` N/A (no flag added or renamed), `/audit-contract` N/A (no API), `/check-isolation` N/A (no new cross-tenant query; one `get` on the per-tenant connection by `startups.id`).

## Out of scope / known limits

- No audit-log row is written for the download (same as the Grant Release Letter download).
- The date is the download date, not a stored declaration date. If the government needs the original declaration date, that is a follow-up.
- The five certifications are fixed text in the template; they are always rendered as checked. They do not reflect any data the startup actually entered.
- The SVG checkbox needs `phenx/php-svg-lib` in `vendor/` (a dompdf dependency). If a deployment's vendor folder lacks it, boxes would not draw.
- Authored without an automated test suite (none exists in `sc-saas-admin`); verified with `php -l`, a local render of the real handler code checked against `self.pdf`, and the manual script.

## Open questions

None.
