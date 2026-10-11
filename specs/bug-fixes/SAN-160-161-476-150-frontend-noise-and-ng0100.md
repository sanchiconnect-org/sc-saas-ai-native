# SAN-160 / SAN-161 / SAN-476 / SAN-150 — NG0100 on required fields; Popper margin warning; lightGallery license key

- **Repo:** sc-saas-frontend · **Assignee:** Aman kabra · **Classification:** CODE_ERROR (latent anti-patterns / console noise)

## SAN-160 / SAN-161 (SC-SAAS-FRONTEND-24 and -1G)
NG0100 on `requiredFields.length` interpolation and `requiredFields.length > 0` ngIf. The first fix only touched `EventFormsComponent`; the Sentry
issues actually come from `ApplicationProgramManagementDynamicFormComponent`, so the same deferral was applied there
(`Promise.resolve().then(...)` in the `valueChanges` handler). NG0100 is dev-mode only (see SAN-158).
Commits: `320caa25b`, `c8b7b8447`.

## SAN-476 (SC-SAAS-FRONTEND-60, same as SAN-563)
Popper's "margin styles cannot be used to apply padding" dev warning, forwarded by `captureConsoleIntegration`. Root cause: the global rule
`.input-group > :not(:first-child){margin-left:-1px}` gives margin to a tooltip host that Popper measures; tooltips on `.input-group-prepend`
hosts now use `container="body"` (9 templates, 43 hosts). Residual warnings from local dev sessions are also dropped in `main.ts` `beforeSend`.
Commits: `1add3107b`, `0016225c3`. Verified with an `ngc` template compile only.

## SAN-150 (SC-SAAS-FRONTEND-17)
lightGallery ran with its default key `0000-0000-000-0000`. 14 components now set `licenseKey: 'GPLv3'`; the old key remains only in a spec file.
The code change is commit `e5280e7f2` under SAN-598 (after `96ea39cb1`). **`'GPLv3'` declares open-source use, so whoever owns licensing must
confirm it is acceptable for this app; otherwise a commercial key is needed.**

## Contract impact
None. Frontend-only; no API, flag, tenancy or auth change.

## Verification
`tsc --noEmit` and `ngc` clean. No automated test added. Not checked in a browser. Not deployed.
