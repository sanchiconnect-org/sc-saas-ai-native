---
id: SAN-401
title: "Startup detail printable view fatals on count(false) without a programId (SC-SAAS-ADMIN-B) — already fixed; latent renderAr bug fixed"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-401
sentry: [SC-SAAS-ADMIN-B]
repos: [admin]
related: [SAN-398, SAN-978, SAN-979, SAN-980, SAN-981, SAN-982, SAN-983]
commit: fatal already fixed by sc-saas-admin@cbd2817f (in main); latent renderAr fix sc-saas-admin@a5d7acea (branch ai_native_setup_vishali)
created: 2026-10-13
updated: 2026-10-13
---

# SAN-401: already fixed in production

## The reported fatal is fixed
* `cbd2817f` (Aman, 2026-09-24, SAN-978–983) changed `startup-detail-printable.php` (now line 1526) to `if(is_array($this->programRounds) && count($this->programRounds) > 0)`. That is fix option 2 from the ticket, applied at the one `count()` site.
* `cbd2817f` is in `origin/main` and `origin/ai_native_setup`.
* SC-SAAS-ADMIN-B (10 events, production, `adm.sinemumbai.sanchiapp.com`) is **resolved** in Sentry. Its last event was 2026-09-24 06:27 UTC, the day of the fix, and there have been none since.

## The four remaining `foreach ($this->programRounds …)` loops are unreachable without a programId
* The loops are at template lines 1252, 1266, 1332 and 1346. They sit inside `is_array($this->getStartupNotesForProgram) && count(...)` (line 1248) and `is_array($this->getStartupQuestionAnswers) && count(...)` (line 1328).
* `modules/startup-detail.php` assigns `getStartupNotesForProgram` (2203), `getStartupQuestionAnswers` (2224) and `programRounds` (2263) **only** inside the `programId` branch (2145–2277).
* So with no `programId`, both guards are false and the loops never run. With a `programId`, all three are assigned together. No change is needed.

## Latent bug fixed (sc-saas-admin@a5d7acea)
* `core/template.php` `renderAr()`: `if(count($dataAr && is_array($dataAr)))` is `count(bool)`, a TypeError under PHP 8 on every call. Changed it to `if(is_array($dataAr) && count($dataAr))`.
* `renderAr()` has **0 callers** in the repo (grep), so this change has no runtime effect today. It only removes the landmine for a first caller.
* `__get()` returning `false` for unset properties (fix option 3) was **not** changed. That is a repo-wide behaviour change with a high blast radius, and it needs its own spec.

## Verification
* `php -l core/template.php` is clean.
* Contract checks do not apply: this is presentation-layer PHP with no flag, API, auth or tenant-scoping change.
* No automated tests: `sc-saas-admin` has no test suite.
