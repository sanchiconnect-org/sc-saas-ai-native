# SAN-1868 — each duplicate-label warning opens its own Sentry group

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1868 (Sentry SC-SAAS-BACKEND-3N, 3P, 5F, 5G, 5H, 5J, 5K, 5M, 5P and others)
- **Repo:** sc-saas-backend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** NOISE (one signal split across many Sentry groups)

## Evidence
The warning `getProfileDataByEmailOfGuestUser: duplicate label "<label>" has conflicting values` (`user.service.ts` ~1401) embeds the label, form id, submission id and guest email in its text. Sentry's default fingerprint hashes the message, so every label became a new group.
SAN-750 had decided the warning is a form-data-quality signal and kept it; SAN-1664 already limited it to one warn per (formId, label) per process.

## Root cause (observed vs inferred)
Observed: the message text varies per label/submission and the default grouping uses it. The underlying data issue (duplicated field labels on forms) is tenant-admin data and was not touched.

## Fix
`src/instrument.ts`: `fingerprintDuplicateLabelWarning(event)`, called from `scrubEvent`, sets `fingerprint = ['guest-user-profile-duplicate-label-conflict']` when the message contains both `getProfileDataByEmailOfGuestUser: duplicate label` and `has conflicting values`. The warning is still emitted and visible; only grouping changes.

## Not fixed
- Existing per-label groups remain as they are; only new events are grouped.
- The message still contains the guest email (PII) — left as is.
- The duplicated labels on the forms themselves.

## Contract impact
None. No API, flag, auth or tenant-scoping change; logging and Sentry grouping only.

## Verification
`tsc` clean. No automated test added (guardian skill blocked). Not run against Sentry, so the grouping result after deploy is unconfirmed.

## Commit
sc-saas-backend `3473722f` (with SAN-1867) on `ai_native_setup_aman`. Pushed, not deployed.

## Sentry
Old groups left to the sweep policy. After deploy, new events should land in one group; confirm that.
