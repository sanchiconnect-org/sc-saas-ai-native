# SAN-1664 — duplicate-label diagnostic warned on every read, one Sentry group per submission

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1664 (Sentry SC-SAAS-BACKEND-3N 39 events, 34 10 events, 3P 7 events)
- **Repo:** sc-saas-backend · **Priority:** Low · **Assignee:** Aman kabra · **Classification:** NOISE (diagnostic logging) over a data/form-config defect

## Problem
`getProfileDataByEmailOfGuestUser: duplicate label "Certificate of Incorporation" has conflicting values — keeping first (formId=20, submissionId=3703, ...)` and the same for
`"How did you get to know about us?"` (formId=1), in production.

## Root cause
`UserService.getProfileDataByEmailOfGuestUser` (`src/modules/user/user.service.ts`) warns whenever two fields on a form share a label and carry different values. This is a deliberate
diagnostic (SAN-750/899) so whoever has admin access can find and rename the duplicated field. It had two side effects: it runs on every read of the same submission, and
`logger.warn()` is forwarded to Sentry; and the text embeds `submissionId`, `email` and `conflictingKey`, so each submission was a separate Sentry group. The defect itself, two fields
sharing a label on a form, is form configuration owned by the tenant admin. SAN-418 (the broader investigation) was Canceled.

## Fix
New `warnDuplicateLabelOnce(formId, label, message)`: the first time a (formId, label) pair is seen in the process it calls `logger.warn()` with the full original message (the
admin hint is unchanged); later hits for the same pair are `logger.log()` lines that still carry the submission id. In-memory `Set`, bounded by the number of distinct duplicated labels.

## Not fixed
Renaming the duplicated fields on form 20 and form 1 (data, not code). The message still contains the submitter's email on the first warning, as before (Sentry scrubs it to `[email]`);
removing it is a separate privacy decision.

## Contract impact
None. Logging only; no API, flag, tenancy or auth change; the returned profile data is unchanged ("keeping first" logic untouched).

## Verification
- New `src/modules/user/user.service.duplicate-label.spec.ts`: 4 cases (first pair warns with the full message; repeats for the same pair, including other submissions, are log lines;
  a different label or form warns again; numeric and string form ids are the same pair). 4/4 pass.
- `tsc --noEmit` exits 0.

## Commit
sc-saas-backend `e5b4aeb6` on `ai_native_setup_aman`. Not deployed.
