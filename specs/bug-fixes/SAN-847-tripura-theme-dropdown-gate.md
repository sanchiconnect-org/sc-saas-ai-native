---
id: SAN-847
title: "Gate \"Tripura\" Certificate Theme option on tripura_certificate_theme_enabled"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-847
repos: [admin]
commit: sc-saas-admin@25ad01e4, sc-saas-admin@2441b47e
created: 2026-09-18
updated: 2026-09-18
---

# SAN-847 — gate the Tripura theme option in sc-saas-admin's Certificate Builder

## Request

Follow-up to [[SAN-845]] (`sanchiconnect-saas-tenants` — added the `tripura_certificate_theme_enabled` tenant
flag). `sc-saas-admin`'s Certificate Builder theme dropdown (`/certificate_builders/edit/<stakeholder>`) always
offered "Tripura" regardless of tenant. This wires the dropdown to actually read the new flag.

## Scope (single-repo, per this issue's own labeling)

Only `sc-saas-admin`. The flag itself is already live in `sanchiconnect-saas-tenants` (SAN-845).

## Fix

`modules/certificate_builders/edit.php:79` — the canonical theme list (`$certificateThemes`, shared by every
stakeholder type since this one controller serves all of them) is built conditionally instead of as a fixed string:

```php
$__tripuraThemeEnabled = ($brandSettings['tripura_certificate_theme_enabled'] ?? '0') == '1';
$certificateThemes = "default,classic,modern,aqua,pink,red" . ($__tripuraThemeEnabled ? ",tripura" : "");
```

`$brandSettings` is populated from the `tenant_users` row by `modules/common.php:481` (`$brandSettings =
$getDatabaseSettingsFromMainTable;`), included earlier in the same file — same read pattern already used for
`startup_grant_release_format_download_enable` (SAN-786/787) elsewhere in this repo.

No template change needed — `themes/default/html/certificate_builders/edit.php` only loops over
`$this->certThemeKeyValPair`, which the controller already builds from `$certificateThemes`
(`default_data` re-sync logic at edit.php:398-421, unaffected by this change other than the list now varying by
tenant instead of being a constant).

## Design notes / non-goals

- **Visibility gate only**, matching SAN-845's resolved design decision: when off, "Tripura" is not offered as a
  new selection. An already-selected `tripura` value in `setting_value` (a tenant that picked it before the flag
  existed, or before it's turned off) is untouched — this only affects `default_data` (the option list), not the
  stored selection.
- **No server-side POST-time coercion added** (unlike e.g. `is_scheme`'s belt-and-suspenders re-check in
  `program.php`) — this form is only reachable by an already-authenticated tenant admin acting on their own
  tenant's own settings, not a public/anonymous endpoint, so a UI-level gate is consistent with how this repo
  treats admin-only cosmetic toggles. Flagging this explicitly rather than silently deciding it doesn't matter.

## Addendum (2026-09-18, same day, found during manual QA)

Discovered testing this fix locally: a tenant that already had `certificate_theme` saved as `tripura` (selected
before the flag existed, or while it was on) saw the dropdown fall back to the blank "Choose an option..."
placeholder once `tripura` dropped out of the visible option list — the template
(`themes/default/html/certificate_builders/edit.php:724-726`) always renders an empty placeholder `<option>` and
only marks one `selected` if the stored value is found in the loop, so a stored value no longer in the list
matches nothing.

Fix: `modules/certificate_builders/edit.php`, right before the `$tpl->settingsKeyValPair` assignment — if the
stored `certificate_theme` isn't in `$certThemeKeyValPair` (the now-filtered list), the **displayed** selection
falls back to `default`. This only changes what's shown in the dropdown; the real `setting_value` in
`spa_settings` is untouched unless the admin explicitly re-saves the form (consistent with "visibility gate
only, does not force-select/un-select" from SAN-845's design decision — the live preview, which reads the real
stored value via the frontend's own API, will still show the tenant's actual previously-chosen theme until they
do).

## Verification

`php -l modules/certificate_builders/edit.php` — no syntax errors. No test framework exists in this repo (per
`sc-saas-admin/CLAUDE.md`) — manual QA needed: with the flag off, confirm "Tripura" no longer appears in the
dropdown for a test tenant; with it on, confirm it reappears and can still be selected/saved.

## Rollout

Committed and pushed to `ai_native_setup`: `25ad01e4`. `sanchiconnect-saas-tenants` (SAN-845, `4b9b9a2`) is also
pushed, so once both are deployed and the tenant's row is re-fetched, the flag will actually reach
`$brandSettings`. Until deployed, `?? '0'` keeps this safely defaulted to hidden everywhere.

## Open questions

None blocking.
